from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from poker.core.rate_limit import register_failures_by_ip
from poker.services.admin.audit_log import get_client_ip
from poker.services.auth.register import register_user_service, verify_email_service
from poker.template_config import templates

router = APIRouter()


def render_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/register.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render_register_page(request)


@router.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    nickname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    ip = get_client_ip(request) or "unknown"
    wait = register_failures_by_ip.retry_after(ip)
    if wait:
        return JSONResponse(
            {"success": False, "error_code": "registerTooManyAttempts", "retry_after": wait},
            status_code=429,
        )

    result = register_user_service(
        request=request,
        username=username,
        nickname=nickname,
        email=email,
        password=password,
        confirm_password=confirm_password,
    )

    if not result.get("success"):
        register_failures_by_ip.hit(ip)

    return result


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email_page(request: Request, token: str = ""):
    """用户点击邮件链接后到达此页面，自动完成验证。"""
    result = verify_email_service(token)
    return templates.TemplateResponse(
        request=request,
        name="auth/verify_email.html",
        context={"success": result.get("success"), "error_code": result.get("error_code", "")},
    )
