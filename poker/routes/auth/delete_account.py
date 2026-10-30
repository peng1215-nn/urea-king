"""
登录页的“注销账号”：输入用户名、密码和确认文字即可注销，不需要先登录。
规则见 poker/services/auth/delete_account.py。
"""

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from core.middleware import clear_session_cache
from poker.core.rate_limit import reserve_login_attempt
from poker.services.common.avatar import delete_avatar_for_user
from poker.services.admin.audit_log import get_client_ip, write_audit_log
from poker.services.auth.delete_account import delete_account_service
from poker.template_config import templates


router = APIRouter()


@router.get("/delete-account", response_class=HTMLResponse)
def delete_account_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/delete_account.html",
    )


@router.post("/account/delete")
def delete_account(
    request: Request,
    username: str = Form("", max_length=50),
    password: str = Form("", max_length=256),
    confirm_text: str = Form("", max_length=64),
):
    ip = get_client_ip(request) or "unknown"

    # 这里要验证账号密码，所以和登录共用限流；先占名额再校验
    attempt = reserve_login_attempt(ip, username)
    if attempt.wait:
        return JSONResponse(
            {"success": False, "message": "loginTooManyAttempts", "retry_after": attempt.wait},
            status_code=429,
        )

    result = delete_account_service(username, password, confirm_text)

    if not result.pop("credential_failed", False):
        attempt.release()

    if not result.get("success"):
        return result

    user_id = result["user_id"]
    original_username = result["original_username"]

    # 系统日志属于安全记录，保留注销前的用户名
    for group in result["deleted_groups"]:
        write_audit_log(
            request=request,
            action="DELETE_GROUP",
            target_type="group",
            target_id=group["group_id"],
            old_value=(
                f"group_code={group['group_code']}, group_name={group['group_name']}, "
                f"counts={group['counts']}, reason=organizer_account_deleted"
            ),
            new_value=None,
            operator_id=user_id,
            operator_username=original_username,
        )

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

    # 如果这个浏览器里还留着该账号的登录状态，一并清掉
    if request.session.get("user_id") == user_id:
        request.session.clear()
    clear_session_cache()

    if result["had_avatar"]:
        delete_avatar_for_user(user_id)

    return {
        "success": True,
        "message": "accountDeleteSuccess",
        "deleted_groups": len(result["deleted_groups"]),
    }
