"""普通用户：资料页（昵称、密码、退出当前组）。"""

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.common.account import get_current_account_service
from poker.services.common.account import update_nickname_service
from poker.services.common.account import update_password_service
from poker.services.common.common import add_no_cache_headers
from poker.services.user.leave_group import leave_group_service
from poker.services.admin.audit_log import write_audit_log
from core.middleware import clear_session_cache
from poker.template_config import templates


router = APIRouter()


def require_user(request: Request):
    return request.session.get("current_role") == "user"


def get_group_id(request: Request):
    return request.session.get("current_group_id")


def get_user_id(request: Request):
    return request.session.get("user_id")


# 修改密码
@router.get("/user-change-password", response_class=HTMLResponse)
def change_password_page(request: Request):
    if not require_user(request):
        return RedirectResponse(url="/login", status_code=302)
    response = templates.TemplateResponse(
        request=request,
        name="user/change_password.html",
        context={"current_page": "change_password"},
    )
    return add_no_cache_headers(response)


@router.get("/user/change-password/current")
def get_current_account(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    return get_current_account_service(user_id=get_user_id(request))


@router.post("/user/change-password/update-nickname")
def update_nickname(request: Request, nickname: str = Form(..., max_length=200)):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    result = update_nickname_service(user_id=get_user_id(request), nickname=nickname)
    if result.get("success"):
        request.session["nickname"] = result.get("nickname")
    return result


@router.post("/user/change-password/update-password")
def update_password(
    request: Request,
    current_password: str = Form(..., max_length=256),
    new_password: str = Form(..., max_length=256),
    confirm_password: str = Form(..., max_length=256),
):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    result = update_password_service(
        user_id=get_user_id(request),
        current_password=current_password,
        new_password=new_password,
        confirm_password=confirm_password,
    )
    if result.get("success"):
        request.session.clear()
        # 让其他设备上的旧登录立即失效
        clear_session_cache()
    return result


# 退出当前组（只有普通用户可以；局头的组需要管理员处理）
@router.post("/user/leave-group")
def leave_group(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}

    user_id = get_user_id(request)
    group_id = get_group_id(request)

    result = leave_group_service(user_id, group_id)

    if result.get("success"):
        write_audit_log(
            request=request,
            action="LEAVE_GROUP",
            target_type="group",
            target_id=group_id,
            old_value=f"group_code={result['group_code']}, group_name={result['group_name']}",
            new_value=None,
            operator_id=user_id,
            operator_username=request.session.get("username"),
        )
        # 退出后当前会话所在的组已经无效，回到登录页重新选择
        request.session.clear()
        clear_session_cache()

    return {
        "success": result.get("success", False),
        "message": "leaveGroupSuccess" if result.get("success") else result.get("message"),
        "remaining_groups": result.get("remaining_groups"),
    }
