from datetime import datetime

from database import SessionLocal
from models import User, InvitationCode
from app_state import PROJECT_LAUNCH_TIME
from app_state import SYSTEM_VERSION
from app_state import DEPLOY_ENVIRONMENT


def get_admin_stats_service():
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


def get_system_monitor_service():
    total_runtime_seconds = int(
        (
            datetime.utcnow()
            - PROJECT_LAUNCH_TIME
        ).total_seconds()
    )

    return {
        "success": True,
        "total_runtime_seconds": total_runtime_seconds,
        "database_status": "正常",
        "deploy_environment": DEPLOY_ENVIRONMENT,
        "system_version": SYSTEM_VERSION
    }


def get_admin_users_service():
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