from fastapi import APIRouter
from database import SessionLocal
from models import User, InvitationCode
from datetime import datetime
from app_state import PROJECT_LAUNCH_TIME
from app_state import SYSTEM_VERSION
from app_state import DEPLOY_ENVIRONMENT
from fastapi import Request


router = APIRouter()


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


@router.get("/current-user")
def current_user(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        return {
            "success": False,
            "message": "未登录。"
        }

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if not user:
            return {
                "success": False,
                "message": "用户不存在。"
            }

        return {
            "success": True,
            "username": user.username,
            "nickname": user.nickname,
            "role": user.role,
            "avatar_url": user.avatar_url
        }

    finally:
        db.close()