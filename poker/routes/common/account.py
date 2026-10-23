from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from poker.core.middleware import clear_session_cache
from poker.core.rate_limit import login_retry_after, record_login_failure
from poker.routes.common.avatar import delete_avatar_for_user
from poker.services.admin.audit_log import get_client_ip, write_audit_log
from poker.services.common.account_deletion import delete_own_account_service


router = APIRouter()

# 只有局头和普通用户可以自助注销；管理员不行
SELF_DELETE_ROLES = ("organizer", "user")


@router.post("/account/delete")
def delete_account(
    request: Request,
    password: str = Form(""),
    confirm_text: str = Form(""),
):
    user_id = request.session.get("user_id")

    if not user_id or request.session.get("current_role") not in SELF_DELETE_ROLES:
        return {"success": False, "message": "permissionDenied"}

    username = request.session.get("username") or ""
    ip = get_client_ip(request) or "unknown"

    # 这里要验证密码，所以和登录共用限流
    wait = login_retry_after(ip, username)
    if wait:
        return JSONResponse(
            {"success": False, "message": "tooManyAttempts", "retry_after": wait},
            status_code=429,
        )

    result = delete_own_account_service(
        user_id=user_id,
        password=password,
        confirm_text=confirm_text,
    )

    if result.pop("password_failed", False):
        record_login_failure(ip, username)

    if not result.get("success"):
        return result

    original_username = result.pop("original_username")
    had_avatar = result.pop("had_avatar")

    # 系统日志属于安全记录，保留注销前的用户名
    write_audit_log(
        request=request,
        action="DELETE_ACCOUNT",
        target_type="user",
        target_id=user_id,
        old_value=original_username,
        new_value="account_deleted",
        operator_id=user_id,
        operator_username=original_username,
    )

    request.session.clear()
    clear_session_cache()

    if had_avatar:
        delete_avatar_for_user(user_id)

    return {"success": True}
