from datetime import datetime

from app_state import DEPLOY_ENVIRONMENT
from app_state import PROJECT_LAUNCH_TIME
from app_state import SYSTEM_VERSION

from database import SessionLocal

from models import Group
from models import InvitationCode
from models import User
from models import UserGroupRole


def get_admin_stats_service(current_group_id):
    db = SessionLocal()

    try:
        total_users = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == current_group_id
        ).count()

        admin_count = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == current_group_id,
            UserGroupRole.role == "admin"
        ).count()

        organizer_count = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == current_group_id,
            UserGroupRole.role == "organizer"
        ).count()

        user_count = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == current_group_id,
            UserGroupRole.role == "user"
        ).count()

        unused_invitation_codes = db.query(
            InvitationCode
        ).filter(
            InvitationCode.is_used == 0
        ).count()

        return {
            "success": True,
            "total_users": total_users,
            "admin_count": admin_count,
            "organizer_count": organizer_count,
            "user_count": user_count,
            "unused_invitation_codes": unused_invitation_codes,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def get_system_monitor_service():
    total_runtime_seconds = int(
        (datetime.utcnow() - PROJECT_LAUNCH_TIME).total_seconds()
    )

    return {
        "success": True,
        "total_runtime_seconds": total_runtime_seconds,
        "database_status": "normal",
        "deploy_environment": DEPLOY_ENVIRONMENT,
        "system_version": SYSTEM_VERSION,
    }


def get_admin_users_service(current_group_id):
    db = SessionLocal()

    try:
        group_roles = db.query(
            UserGroupRole,
            User,
            Group,
        ).join(
            User,
            UserGroupRole.user_id == User.id,
        ).join(
            Group,
            UserGroupRole.group_id == Group.id,
        ).filter(
            UserGroupRole.group_id == current_group_id
        ).order_by(
            User.id.asc()
        ).all()

        user_list = []

        for user_group_role, user, group in group_roles:

            user_list.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "role": user_group_role.role,
                "group_id": group.group_code,
                "group_name": group.group_name,
                "avatar_url": user.avatar_url,
                "created_at": (
                    user.created_at.strftime("%Y-%m-%d %H:%M")
                    if user.created_at
                    else ""
                )
            })

        return {
            "success": True,
            "users": user_list,
        }

    finally:
        db.close()