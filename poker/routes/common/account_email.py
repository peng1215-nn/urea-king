"""个人资料页：已验证账号更换邮箱（所有身份共用）。"""

from fastapi import APIRouter, BackgroundTasks, Form, Request
from fastapi.responses import JSONResponse

from poker.core.rate_limit import change_email_by_ip, current_password_failures_by_user
from poker.services.admin.audit_log import get_client_ip, write_audit_log
from poker.services.auth.change_email import (
    cancel_email_change_service,
    get_account_email_service,
    request_email_change_service,
)

router = APIRouter()


def _session_user_id(request: Request):
    user_id = request.session.get("user_id")
    return int(user_id) if user_id else None


def _expired():
    return JSONResponse({"success": False, "message": "sessionExpired"}, status_code=401)


@router.get("/account/email")
def get_account_email(request: Request):
    user_id = _session_user_id(request)
    if not user_id:
        return _expired()
    return get_account_email_service(user_id)


@router.post("/account/change-email")
def request_email_change(
    request: Request,
    background_tasks: BackgroundTasks,
    current_password: str = Form("", max_length=256),
    new_email: str = Form("", max_length=254),
):
    user_id = _session_user_id(request)
    if not user_id:
        return _expired()

    # 每次请求都按 IP 计数：成功的请求会发邮件，不能被拿来给任意邮箱批量发信
    wait, _ = change_email_by_ip.try_hit(get_client_ip(request) or "unknown")
    if wait:
        return JSONResponse(
            {"success": False, "message": "accountEmailTooManyAttempts", "retry_after": wait},
            status_code=429,
        )

    # 要核对当前密码：和修改密码共用“输错当前密码”的次数限制，先占名额，密码没错再退回
    limiter_key = str(user_id)
    wait, stamp = current_password_failures_by_user.try_hit(limiter_key)
    if wait:
        return JSONResponse(
            {"success": False, "message": "currentPasswordTooManyAttempts", "retry_after": wait},
            status_code=429,
        )

    result = request_email_change_service(
        user_id=user_id,
        password=current_password,
        new_email=new_email,
        background_tasks=background_tasks,
    )
    if result.get("message") != "accountEmailWrongPassword":
        current_password_failures_by_user.undo(limiter_key, stamp)

    if result.get("success"):
        write_audit_log(
            request=request,
            action="EMAIL_CHANGE_REQUESTED",
            target_type="user",
            target_id=user_id,
            old_value=None,
            new_value=None,
            operator_id=user_id,
            operator_username=request.session.get("username"),
        )
    return result


@router.post("/account/change-email/cancel")
def cancel_email_change(request: Request):
    user_id = _session_user_id(request)
    if not user_id:
        return _expired()
    return cancel_email_change_service(user_id)
