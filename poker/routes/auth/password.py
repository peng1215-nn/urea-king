from fastapi import APIRouter, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from core.middleware import clear_session_cache
from poker.core.rate_limit import forgot_password_failures_by_ip, reset_password_failures_by_ip
from poker.services.admin.audit_log import get_client_ip
from poker.services.auth.reset_password import (
    check_reset_token_service,
    forgot_password_service,
    reset_password_service,
)
from poker.template_config import templates

router = APIRouter()

# 这些结果说明提交的重置链接无效，计入同一 IP 的失败次数
RESET_TOKEN_FAILURES = {"resetTokenInvalid", "resetTokenUsed", "resetTokenExpired"}


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/forgot_password.html")


@router.post("/forgot-password")
def forgot_password(request: Request, background_tasks: BackgroundTasks, email: str = Form(..., max_length=254)):
    ip = get_client_ip(request) or "unknown"
    # 回复总是"已发送"，所以按请求次数计数，而不是按失败计数
    wait, _ = forgot_password_failures_by_ip.try_hit(ip)
    if wait:
        return JSONResponse(
            {"success": False, "error_code": "forgotPasswordTooManyAttempts", "retry_after": wait},
            status_code=429,
        )
    # 邮件在响应返回后再发，响应时间不会暴露邮箱是否注册
    return forgot_password_service(email=email, background_tasks=background_tasks)


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str = ""):
    # 先只读检查链接，失效时直接显示错误，不用等用户填完密码才知道
    error_code = check_reset_token_service(token[:256])
    return templates.TemplateResponse(
        request=request,
        name="auth/reset_password.html",
        context={"token": token, "error_code": error_code or ""},
    )


@router.post("/reset-password")
def reset_password(
    request: Request,
    token: str = Form(..., max_length=256),
    new_password: str = Form(..., max_length=256),
    confirm_password: str = Form(..., max_length=256),
):
    ip = get_client_ip(request) or "unknown"
    # 先按失败占用名额，链接有效时退回
    wait, stamp = reset_password_failures_by_ip.try_hit(ip)
    if wait:
        return JSONResponse(
            {"success": False, "error_code": "forgotPasswordTooManyAttempts", "retry_after": wait},
            status_code=429,
        )
    result = reset_password_service(
        token=token,
        new_password=new_password,
        confirm_password=confirm_password,
    )
    if result.get("error_code") not in RESET_TOKEN_FAILURES:
        reset_password_failures_by_ip.undo(ip, stamp)
    if result.get("success"):
        # 密码已改，其他设备上的旧登录立即失效
        clear_session_cache()
    return result
