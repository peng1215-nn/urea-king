from datetime import datetime
from app_state import DEPLOY_ENVIRONMENT
from app_state import PROJECT_LAUNCH_TIME
from app_state import SYSTEM_VERSION
from database import SessionLocal
from models import Group
from models import InvitationCode
from models import User
from models import UserGroupRole
from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def get_admin_stats_service():
    db = SessionLocal()

    try:
        total_users = db.query(UserGroupRole).count()

        admin_count = db.query(UserGroupRole).filter(
            UserGroupRole.role == "admin"
        ).count()

        organizer_count = db.query(UserGroupRole).filter(
            UserGroupRole.role == "organizer"
        ).count()

        user_count = db.query(UserGroupRole).filter(
            UserGroupRole.role == "user"
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


def get_admin_users_service():
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
        ).order_by(
            Group.group_name.asc(),
            User.id.asc(),
        ).all()

        users = []

        for user_group_role, user, group in group_roles:
            users.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "role": user_group_role.role,
                "group_id": group.id,
                "group_code": group.group_code,
                "group_name": group.group_name,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": (
                    user.created_at.strftime("%Y-%m-%d %H:%M")
                    if user.created_at
                    else ""

                ),
            })

        return {
            "success": True,
            "users": users,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def update_user_role_service(
    target_user_id,
    group_id,
    new_role,
):
    db = SessionLocal()

    try:
        if new_role not in [
            "organizer",
            "user",
        ]:
            return {
                "success": False,
                "message": "身份类型无效。",
            }

        user_group_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == target_user_id,
            UserGroupRole.group_id == group_id,
        ).first()

        if not user_group_role:
            return {
                "success": False,
                "message": "该用户不属于所选组别。",
            }

        if user_group_role.role == "admin":
            return {
                "success": False,
                "message": "管理员身份不可修改。",
            }

        if user_group_role.role == new_role:
            return {
                "success": False,
                "message": "身份无需更改。",
            }

        user_group_role.role = new_role

        db.commit()

        return {
            "success": True,
            "message": "用户身份修改成功。",
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def reset_user_password_service(target_user_id):
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == target_user_id
        ).first()

        if not user:
            return {
                "success": False,
                "message": "用户不存在。",
            }

        admin_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == target_user_id,
            UserGroupRole.role == "admin",
        ).first()

        if admin_role:
            return {
                "success": False,
                "message": "不允许重置管理员密码。",
            }

        user.password_hash = pwd_context.hash("000000")

        db.commit()

        return {
            "success": True,
            "message": "密码已重置为 000000。",
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def toggle_user_active_service(target_user_id):
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == target_user_id
        ).first()

        if not user:
            return {
                "success": False,
                "message": "用户不存在。",
            }

        admin_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == target_user_id,
            UserGroupRole.role == "admin",
        ).first()

        if admin_role:
            return {
                "success": False,
                "message": "不允许禁用管理员账号。",
            }

        user.is_active = 0 if user.is_active == 1 else 1

        db.commit()

        return {
            "success": True,
            "is_active": user.is_active,
            "message": (
                "accountDisabled"
                if user.is_active == 0
                else "accountEnabled"
            ),
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()