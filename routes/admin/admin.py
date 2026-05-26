from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from services.admin.admin import get_admin_stats_service
from services.admin.admin import get_admin_users_service
from services.admin.admin import get_system_monitor_service
from services.common.common import add_no_cache_headers
from template_config import templates
from fastapi import Form
from services.admin.admin import update_user_role_service
from services.admin.admin import reset_user_password_service
from services.admin.admin import toggle_user_active_service
from services.admin.audit_log import write_audit_log


router = APIRouter()


def require_admin(request: Request):
    return request.session.get("current_role") == "admin"


def render_admin_page(
    request: Request,
    template_name,
    current_page,
):
    if not require_admin(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    response = templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "current_page": current_page,
        },
    )

    return add_no_cache_headers(response)


@router.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return render_admin_page(
        request,
        "admin/dashboard.html",
        "dashboard",
    )


@router.get("/system-monitor", response_class=HTMLResponse)
def system_monitor_page(request: Request):
    return render_admin_page(
        request,
        "admin/system_monitor.html",
        "system_monitor",
    )


@router.get("/user-management", response_class=HTMLResponse)
def user_management_page(request: Request):
    return render_admin_page(
        request,
        "admin/user_management.html",
        "user_management",
    )


@router.get("/admin/stats")
def admin_stats(request: Request):
    if not require_admin(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    return get_admin_stats_service()


@router.get("/admin/system-monitor")
def system_monitor_data(request: Request):
    if not require_admin(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    return get_system_monitor_service()


@router.get("/admin/users")
def get_users(request: Request):
    if not require_admin(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    return get_admin_users_service()


@router.post("/admin/update-user-role")
def update_user_role(
    request: Request,
    target_user_id: int = Form(...),
    group_id: int = Form(...),
    role: str = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    result = update_user_role_service(
        target_user_id=target_user_id,
        group_id=group_id,
        new_role=role,
    )

    if result.get("success"):

        write_audit_log(
            request=request,
            action="UPDATE_USER_ROLE",
            target_type="user",
            target_id=target_user_id,
            old_value=result.get("old_role"),
            new_value=result.get("new_role"),
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get(
                "username"
            ),
        )

    return result


@router.post("/admin/reset-user-password")
def reset_user_password(
    request: Request,
    target_user_id: int = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    result = reset_user_password_service(
        target_user_id=target_user_id,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="RESET_USER_PASSWORD",
            target_type="user",
            target_id=target_user_id,
            old_value=None,
            new_value="password_reset_to_default",
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result


@router.post("/admin/toggle-user-active")
def toggle_user_active(
    request: Request,
    target_user_id: int = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    result = toggle_user_active_service(
        target_user_id=target_user_id,
    )

    if result.get("success"):
        is_active = result.get("is_active")

        action = (
            "ENABLE_USER"
            if int(is_active) == 1
            else "DISABLE_USER"
        )

        new_value = (
            "active"
            if int(is_active) == 1
            else "disabled"
        )

        write_audit_log(
            request=request,
            action=action,
            target_type="user",
            target_id=target_user_id,
            old_value=None,
            new_value=new_value,
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result