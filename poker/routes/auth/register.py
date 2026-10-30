from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from poker.core.rate_limit import (
    login_retry_after,
    record_login_failure,
    register_failures_by_ip,
    resend_verify_failures_by_ip,
)
from poker.services.admin.audit_log import get_client_ip
from poker.services.auth.register import register_user_service, verify_email_service
from poker.services.auth.resend_verify import resend_verify_email_service
from poker.services.auth.change_email import change_email_service
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


@router.post("/resend-verify-email")
def resend_verify_email(request: Request, email: str = Form(...)):
    ip = get_client_ip(request) or "unknown"
    wait = resend_verify_failures_by_ip.retry_after(ip)
    if wait:
        return JSONResponse(
            {"success": False, "error_code": "resendTooManyAttempts", "retry_after": wait},
            status_code=429,
        )
    # 回复几乎总是"已发送"，所以按请求次数计数，而不是按失败计数
    resend_verify_failures_by_ip.hit(ip)
    return resend_verify_email_service(email)


@router.post("/change-email")
def change_email(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    new_email: str = Form(...),
):
    ip = get_client_ip(request) or "unknown"

    # 这里要验证账号密码，所以和登录共用限流，防止借此反复猜密码
    wait = login_retry_after(ip, username)
    if wait:
        return JSONResponse(
            {"success": False, "error_code": "changeEmailTooManyAttempts", "retry_after": wait},
            status_code=429,
        )

    result = change_email_service(username, password, new_email)
    if result.get("error_code") == "changeEmailWrongCredentials":
        record_login_failure(ip, username)
    return result


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email_page(request: Request, token: str = ""):
    """用户点击邮件链接后到达此页面，展示确认按钮（不自动验证，防止安全扫描消耗 token）。"""
    return templates.TemplateResponse(
        request=request,
        name="auth/verify_email.html",
        context={"pending": True, "token": token},
    )


@router.post("/verify-email", response_class=HTMLResponse)
def verify_email_confirm(request: Request, token: str = Form("")):
    """用户点击确认按钮后才真正验证 token。"""
    result = verify_email_service(token)
    return templates.TemplateResponse(
        request=request,
        name="auth/verify_email.html",
        context={"success": result.get("success"), "error_code": result.get("error_code", "")},
    )
