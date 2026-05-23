from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from template_config import templates
from app_state import DEPLOY_ENVIRONMENT, PROJECT_LAUNCH_TIME, SYSTEM_VERSION
from database import SessionLocal
from models import InvitationCode, User
from services.common import add_no_cache_headers
from services.admin import get_system_monitor_service


router = APIRouter()


def require_admin(request: Request):
    return request.session.get("role") == "admin"


def render_admin_page(request: Request, template_name, current_page):
    if not require_admin(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"current_page": current_page},
    )

    return add_no_cache_headers(response)


@router.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return render_admin_page(request, "admin/dashboard.html", "dashboard")


@router.get("/system-monitor", response_class=HTMLResponse)
def system_monitor_page(request: Request):
    return render_admin_page(
        request,
        "admin/system_monitor.html",
        "system_monitor"
    )


@router.get("/admin/system-monitor")
def system_monitor_data():
    return get_system_monitor_service()


@router.get("/user-management", response_class=HTMLResponse)
def user_management_page(request: Request):
    return render_admin_page(
        request,
        "admin/user_management.html",
        "user_management",
    )


@router.get("/admin/stats")
def admin_stats():
    db = SessionLocal()

    try:
        return {
            "success": True,
            "total_users": db.query(User).count(),
            "admin_count": db.query(User).filter(User.role == "admin").count(),
            "organizer_count": db.query(User).filter(User.role == "organizer").count(),
            "user_count": db.query(User).filter(User.role == "user").count(),
            "unused_invitation_codes": db.query(InvitationCode)
            .filter(InvitationCode.is_used == 0)
            .count(),
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        db.close()


@router.get("/admin/system-monitor")
def system_monitor_data():
    total_runtime_seconds = int(
        (datetime.utcnow() - PROJECT_LAUNCH_TIME).total_seconds()
    )

    return {
        "success": True,
        "total_runtime_seconds": total_runtime_seconds,
        "database_status": "正常",
        "deploy_environment": DEPLOY_ENVIRONMENT,
        "system_version": SYSTEM_VERSION,
    }


@router.get("/admin/users")
def get_users(request: Request):
    if not require_admin(request):
        return {"success": False, "message": "无权限访问。"}

    db = SessionLocal()

    try:
        users = db.query(User).order_by(User.id.asc()).all()

        return {
            "success": True,
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "role": user.role,
                    "group_id": user.group_id,
                    "avatar_url": user.avatar_url,
                    "created_at": (
                        user.created_at.strftime("%Y-%m-%d %H:%M")
                        if user.created_at
                        else ""
                    ),
                }
                for user in users
            ],
        }

    finally:
        db.close()