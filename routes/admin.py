from fastapi import APIRouter
from fastapi import Request

from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from template_config import templates

from services.common import add_no_cache_headers

from services.admin import get_admin_stats_service
from services.admin import get_admin_users_service
from services.admin import get_system_monitor_service


router = APIRouter()


def require_admin(request: Request):
    return request.session.get(
        "current_role"
    ) == "admin"


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


@router.get(
    "/admin-dashboard",
    response_class=HTMLResponse,
)
def admin_dashboard(request: Request):
    return render_admin_page(
        request,
        "admin/dashboard.html",
        "dashboard",
    )


@router.get(
    "/system-monitor",
    response_class=HTMLResponse,
)
def system_monitor_page(request: Request):
    return render_admin_page(
        request,
        "admin/system_monitor.html",
        "system_monitor",
    )


@router.get("/admin/system-monitor")
def system_monitor_data():
    return get_system_monitor_service()


@router.get(
    "/user-management",
    response_class=HTMLResponse,
)
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

    current_group_id = request.session.get(
        "current_group_id"
    )

    return get_admin_stats_service(
        current_group_id
    )


@router.get("/admin/users")
def get_users(request: Request):

    if not require_admin(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    current_group_id = request.session.get(
        "current_group_id"
    )

    return get_admin_users_service(
        current_group_id
    )