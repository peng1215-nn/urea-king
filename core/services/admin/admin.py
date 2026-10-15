from app_state import DEPLOY_ENVIRONMENT, PROJECT_LAUNCH_TIME, SYSTEM_VERSION
from utils.time import now_columbus_naive
from database import SessionLocal
from poker.models import (
    PokerUser, PokerGroup, PokerInvitationCode, PokerUserGroupRole, PokerGame
)
from core.models import PlatformUser, PlatformUserGroupRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_admin_stats_service():
    db = SessionLocal()
    try:
        total_users = db.query(PokerUser).count()
        admin_count = db.query(PlatformUserGroupRole).count()  # platform-level admin/dev accounts
        organizer_count = db.query(PokerUserGroupRole).filter(PokerUserGroupRole.role == "organizer").count()
        user_count = db.query(PokerUserGroupRole).filter(PokerUserGroupRole.role == "user").count()
        unused_invitation_codes = db.query(PokerInvitationCode).filter(PokerInvitationCode.is_used == 0).count()
        total_groups = db.query(PokerGroup).count()
        return {
            "success": True,
            "total_users": total_users,
            "total_groups": total_groups,
            "admin_count": admin_count,
            "organizer_count": organizer_count,
            "user_count": user_count,
            "unused_invitation_codes": unused_invitation_codes,
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def get_system_monitor_service():
    total_runtime_seconds = int(
        (now_columbus_naive() - PROJECT_LAUNCH_TIME).total_seconds()
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
        group_roles = (
            db.query(PokerUserGroupRole, PokerUser, PokerGroup)
            .join(PokerUser, PokerUserGroupRole.user_id == PokerUser.id)
            .join(PokerGroup, PokerUserGroupRole.group_id == PokerGroup.id)
            .order_by(PokerGroup.group_name.asc(), PokerUser.id.asc())
            .all()
        )
        users = []
        for ugr, user, group in group_roles:
            users.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "role": ugr.role,
                "group_id": group.id,
                "group_code": group.group_code,
                "group_name": group.group_name,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "",
            })
        return {"success": True, "users": users}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def update_user_role_service(target_user_id, group_id, new_role):
    db = SessionLocal()
    try:
        if new_role not in ["organizer", "user"]:
            return {"success": False, "message": "身份类型无效。"}

        ugr = db.query(PokerUserGroupRole).filter(
            PokerUserGroupRole.user_id == target_user_id,
            PokerUserGroupRole.group_id == group_id,
        ).first()
        if not ugr:
            return {"success": False, "message": "该用户不属于所选组别。"}
        if ugr.role == new_role:
            return {"success": False, "message": "身份无需更改。"}

        old_role = ugr.role
        ugr.role = new_role
        db.commit()
        return {"success": True, "message": "用户身份修改成功。", "old_role": old_role, "new_role": new_role}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def reset_user_password_service(target_user_id):
    db = SessionLocal()
    try:
        user = db.query(PokerUser).filter(PokerUser.id == target_user_id).first()
        if not user:
            return {"success": False, "message": "用户不存在。"}
        user.password_hash = pwd_context.hash("000000")
        db.commit()
        return {"success": True, "message": "密码已重置为 000000。"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def toggle_user_active_service(target_user_id):
    db = SessionLocal()
    try:
        user = db.query(PokerUser).filter(PokerUser.id == target_user_id).first()
        if not user:
            return {"success": False, "message": "用户不存在。"}
        user.is_active = 0 if user.is_active == 1 else 1
        db.commit()
        return {
            "success": True,
            "is_active": user.is_active,
            "message": "accountDisabled" if user.is_active == 0 else "accountEnabled",
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
