from typing import Optional

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse

from poker.services.auth.group_join import group_join_service
from poker.services.auth.group_join import group_join_logged_in_service
from poker.template_config import templates
from fastapi.responses import JSONResponse
from poker.core.rate_limit import (
    GLOBAL_KEY,
    group_join_failures_by_ip,
    invite_failures_global,
    Reservation,
    reserve,
    reserve_login_attempt,
)
from poker.services.admin.audit_log import get_client_ip
from poker.services.common.invite_codes import invite_code_is_available


router = APIRouter()


@router.get(
    "/group-join",
    response_class=HTMLResponse,
)
def group_join_page(request: Request):
    is_logged_in = bool(request.session.get("user_id"))
    return templates.TemplateResponse(
        request=request,
        name="auth/group_join.html",
        context={"is_logged_in": is_logged_in},
    )


@router.post("/group-join")
def group_join(
    request: Request,
    invite_code: str = Form(..., max_length=64),
    username: Optional[str] = Form(None, max_length=50),
    password: Optional[str] = Form(None, max_length=256),
):
    ip = get_client_ip(request) or "unknown"
    user_id = request.session.get("user_id")

    # 未登录用户：需要账号密码 + 邀请码
    if not user_id:
        if not username:
            return {"success": False, "message": "groupJoinUsernameRequired"}
        if not password:
            return {"success": False, "message": "groupJoinPasswordRequired"}

    # 先占名额再校验，并发的请求不能同时通过检查。
    # 账号密码错误计入登录限流；邀请码不存在或已使用计入按 IP 限流；邀请码不存在还计入全站上限。
    login_attempt = reserve_login_attempt(ip, username) if not user_id else None
    if login_attempt and login_attempt.wait:
        return JSONResponse(
            {"success": False, "message": "groupJoinTooManyAttempts", "retry_after": login_attempt.wait},
            status_code=429,
        )

    ip_attempt = reserve([(group_join_failures_by_ip, ip, True)])
    global_attempt = reserve([(invite_failures_global, GLOBAL_KEY, True)]) if not ip_attempt.wait else None
    if global_attempt is not None and global_attempt.wait and invite_code_is_available(invite_code):
        # 全站猜码上限被别人刷满时，真实有效的邀请码照样放行，不让一个人锁住全站的加组
        global_attempt = Reservation()
    blocked = ip_attempt.wait or (global_attempt.wait if global_attempt else 0)
    if blocked:
        # 被全站上限挡下时，按 IP 的次数照样扣（不退回）：否则"挡下还是放行"就成了
        # 可以无限试探邀请码是否有效的信号。被按 IP 上限挡下时本来就没有占用名额。
        if global_attempt:
            global_attempt.release()
        if login_attempt:
            login_attempt.release()
        return JSONResponse(
            {"success": False, "message": "groupJoinTooManyAttempts", "retry_after": blocked},
            status_code=429,
        )

    if user_id:
        # 已登录用户：直接用 session 身份，只需邀请码
        result = group_join_logged_in_service(
            request=request,
            user_id=user_id,
            invite_code=invite_code,
        )
    else:
        result = group_join_service(
            request=request,
            username=username,
            password=password,
            invite_code=invite_code,
        )

    message = result.get("message")
    if login_attempt and message != "groupJoinAccountInvalid":
        login_attempt.release()
    if message not in ("groupJoinInviteCodeNotFound", "groupJoinInviteCodeUsed"):
        ip_attempt.release()
    if message != "groupJoinInviteCodeNotFound":
        global_attempt.release()

    return result