from typing import Optional

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse

from poker.services.auth.group_join import group_join_service
from poker.services.auth.group_join import group_join_logged_in_service
from poker.template_config import templates
from fastapi.responses import JSONResponse
from poker.core.rate_limit import GLOBAL_KEY, group_join_failures_by_ip, invite_failures_global, login_retry_after, record_login_failure
from poker.services.admin.audit_log import get_client_ip


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
    invite_code: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
):
    ip = get_client_ip(request) or "unknown"
    user_id = request.session.get("user_id")

    # 已登录用户：直接用 session 身份，只需邀请码
    if user_id:
        wait = max(
            group_join_failures_by_ip.retry_after(ip),
            invite_failures_global.retry_after(GLOBAL_KEY),
        )
        if wait:
            return JSONResponse(
                {"success": False, "message": "groupJoinTooManyAttempts", "retry_after": wait},
                status_code=429,
            )
        result = group_join_logged_in_service(
            request=request,
            user_id=user_id,
            invite_code=invite_code,
        )
        if result.get("message") in ("groupJoinInviteCodeNotFound", "groupJoinInviteCodeUsed"):
            group_join_failures_by_ip.hit(ip)
            if result.get("message") == "groupJoinInviteCodeNotFound":
                invite_failures_global.hit(GLOBAL_KEY)
        return result

    # 未登录用户：需要账号密码 + 邀请码
    if not username:
        return {"success": False, "message": "groupJoinUsernameRequired"}
    if not password:
        return {"success": False, "message": "groupJoinPasswordRequired"}

    wait = max(
        login_retry_after(ip, username),
        group_join_failures_by_ip.retry_after(ip),
        invite_failures_global.retry_after(GLOBAL_KEY),
    )
    if wait:
        return JSONResponse(
            {"success": False, "message": "groupJoinTooManyAttempts", "retry_after": wait},
            status_code=429,
        )

    result = group_join_service(
        request=request,
        username=username,
        password=password,
        invite_code=invite_code,
    )

    message = result.get("message")
    if message == "groupJoinAccountInvalid":
        record_login_failure(ip, username)
    elif message in ("groupJoinInviteCodeNotFound", "groupJoinInviteCodeUsed"):
        group_join_failures_by_ip.hit(ip)
        if message == "groupJoinInviteCodeNotFound":
            invite_failures_global.hit(GLOBAL_KEY)

    return result