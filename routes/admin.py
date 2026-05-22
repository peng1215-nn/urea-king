from fastapi import APIRouter
from database import SessionLocal
from models import User, InvitationCode
from datetime import datetime
from app_state import PROJECT_LAUNCH_TIME
from app_state import SYSTEM_VERSION
from app_state import DEPLOY_ENVIRONMENT
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


@router.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse(
            url="/login",
            status_code=302
        )

    response = templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "current_page": "dashboard"
        }
    )

    response.headers["Cache-Control"] = \
        "no-store, no-cache, must-revalidate, max-age=0"

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@router.get("/system-monitor", response_class=HTMLResponse)
def system_monitor_page(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse(
            url="/login",
            status_code=302
        )

    response = templates.TemplateResponse(
        request=request,
        name="admin/system_monitor.html",
        context={
            "current_page": "system_monitor"
        }
    )

    response.headers["Cache-Control"] = \
        "no-store, no-cache, must-revalidate, max-age=0"

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@router.get("/user-management", response_class=HTMLResponse)
def user_management_page(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse(
            url="/login",
            status_code=302
        )

    response = templates.TemplateResponse(
        request=request,
        name="admin/user_management.html",
        context={
            "current_page": "user_management"
        }
    )

    response.headers["Cache-Control"] = \
        "no-store, no-cache, must-revalidate, max-age=0"

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@router.get("/admin/stats")
def admin_stats():
    db = SessionLocal()

    try:
        total_users = db.query(User).count()

        admin_count = db.query(User).filter(
            User.role == "admin"
        ).count()

        organizer_count = db.query(User).filter(
            User.role == "organizer"
        ).count()

        user_count = db.query(User).filter(
            User.role == "user"
        ).count()

        unused_invitation_codes = db.query(InvitationCode).filter(
            InvitationCode.is_used == 0
        ).count()

        return {
            "success": True,
            "total_users": total_users,
            "admin_count": admin_count,
            "organizer_count": organizer_count,
            "user_count": user_count,
            "unused_invitation_codes": unused_invitation_codes
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


@router.get("/admin/system-monitor")
def system_monitor_data():

    total_runtime_seconds = int(
        (
            datetime.utcnow()
            -
            PROJECT_LAUNCH_TIME
        ).total_seconds()
    )

    return {
        "success": True,
        "total_runtime_seconds": total_runtime_seconds,
        "database_status": "正常",
        "deploy_environment": DEPLOY_ENVIRONMENT,
        "system_version": SYSTEM_VERSION
    }


@router.get("/admin/users")
def get_users(request: Request):

    if request.session.get("role") != "admin":
        return {
            "success": False,
            "message": "无权限访问。"
        }

    db = SessionLocal()

    try:
        users = db.query(User).order_by(
            User.id.asc()
        ).all()

        user_list = []

        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "role": user.role,
                "group_id": user.group_id,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M")
                if user.created_at else ""
            })

        return {
            "success": True,
            "users": user_list
        }

    finally:
        db.close()