from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from poker.services.auth.register import register_user_service
from poker.template_config import templates
from fastapi.responses import JSONResponse
from poker.core.rate_limit import GLOBAL_KEY, invite_failures_global, register_failures_by_ip
from poker.services.admin.audit_log import get_client_ip


router = APIRouter()


def render_register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
    )


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render_register_page(request)


@router.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    invite_code: str = Form(...),
):
    ip = get_client_ip(request) or "unknown"
    wait = max(
        register_failures_by_ip.retry_after(ip),
        invite_failures_global.retry_after(GLOBAL_KEY),
    )

    if wait:
        return JSONResponse(
            {
                "success": False,
                "error_code": "registerTooManyAttempts",
                "retry_after": wait,
            },
            status_code=429,
        )

    result = register_user_service(
        request=request,
        username=username,
        nickname=nickname,
        password=password,
        confirm_password=confirm_password,
        invite_code=invite_code,
    )

    # 只统计邀请码相关的失败，防止暴力猜测邀请码
    if not result.get("success") and str(result.get("error_code", "")).startswith("registerInviteCode"):
        register_failures_by_ip.hit(ip)
        invite_failures_global.hit(GLOBAL_KEY)

    return result