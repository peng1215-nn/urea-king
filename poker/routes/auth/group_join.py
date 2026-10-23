from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse

from poker.services.auth.group_join import group_join_service
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
    return templates.TemplateResponse(
        request=request,
        name="auth/group_join.html",
    )


@router.post("/group-join")
def group_join(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
):
    ip = get_client_ip(request) or "unknown"
    # 这里也要输入账号密码，所以同时受登录限流约束
    wait = max(
        login_retry_after(ip, username),
        group_join_failures_by_ip.retry_after(ip),
        invite_failures_global.retry_after(GLOBAL_KEY),
    )

    if wait:
        return JSONResponse(
            {
                "success": False,
                "message": "groupJoinTooManyAttempts",
                "retry_after": wait,
            },
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