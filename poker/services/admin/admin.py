from core.time import now_columbus_naive
from poker.app_state import DEPLOY_ENVIRONMENT
from poker.app_state import PROJECT_LAUNCH_TIME
from poker.app_state import SYSTEM_VERSION
from database import SessionLocal
from poker.models import Group
from poker.models import InvitationCode
from poker.models import SiteCounter
from poker.models import User
from poker.models import UserGroupRole
from core.errors import safe_error
from core.security import pwd_context




def get_admin_stats_service():
    db = SessionLocal()

    try:
        total_users = db.query(User).count()

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

        total_groups = db.query(Group).count()

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
        return {
            "success": False,
            "message": safe_error(e),
        }

    finally:
        db.close()


def _increment_counter(key: str):
    """通用计数器 +1，key+date 唯一，不存在则新建。"""
    today = now_columbus_naive().strftime("%Y-%m-%d")
    db = SessionLocal()
    try:
        row = db.query(SiteCounter).filter(
            SiteCounter.key == key,
            SiteCounter.date == today,
        ).first()
        if row:
            row.count += 1
        else:
            db.add(SiteCounter(key=key, date=today, count=1))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _get_counter_stats(key: str):
    """返回指定 key 的今日计数和历史总计。"""
    today = now_columbus_naive().strftime("%Y-%m-%d")
    db = SessionLocal()
    try:
        rows = db.query(SiteCounter).filter(SiteCounter.key == key).all()
        total = sum(r.count for r in rows)
        today_count = next((r.count for r in rows if r.date == today), 0)
        return {"today": today_count, "total": total}
    except Exception:
        return {"today": 0, "total": 0}
    finally:
        db.close()


def record_login_page_view_service():
    """登录页每次被访问时调用。"""
    _increment_counter("login_page_view")


def record_login_success_service():
    """登录成功时调用。"""
    _increment_counter("login_success")


def get_system_monitor_service():
    total_runtime_seconds = int(
        (now_columbus_naive() - PROJECT_LAUNCH_TIME).total_seconds()
    )

    pv = _get_counter_stats("login_page_view")
    ls = _get_counter_stats("login_success")

    return {
        "success": True,
        "total_runtime_seconds": total_runtime_seconds,
        "database_status": "normal",
        "deploy_environment": DEPLOY_ENVIRONMENT,
        "system_version": SYSTEM_VERSION,
        "page_view_today": pv["today"],
        "page_view_total": pv["total"],
        "login_success_today": ls["today"],
        "login_success_total": ls["total"],
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
            "message": safe_error(e),
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
                "message": "roleInvalid",
            }

        user_group_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == target_user_id,
            UserGroupRole.group_id == group_id,
        ).first()

        if not user_group_role:
            return {
                "success": False,
                "message": "userNotInSelectedGroup",
            }

        if user_group_role.role == "admin":
            return {
                "success": False,
                "message": "adminRoleImmutable",
            }

        if user_group_role.role == new_role:
            return {
                "success": False,
                "message": "roleNoChange",
            }

        old_role = user_group_role.role

        user_group_role.role = new_role

        db.commit()

        return {
            "success": True,
            "message": "roleUpdateSuccess",
            "old_role": old_role,
            "new_role": new_role,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": safe_error(e),
        }

    finally:
        db.close()


RESET_PASSWORD = "00000000"


def reset_user_password_service(target_user_id):
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == target_user_id
        ).first()

        if not user:
            return {
                "success": False,
                "message": "userNotFound",
            }

        admin_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == target_user_id,
            UserGroupRole.role == "admin",
        ).first()

        if admin_role:
            return {
                "success": False,
                "message": "adminPasswordResetForbidden",
            }

        user.password_hash = pwd_context.hash(RESET_PASSWORD)

        db.commit()

        return {
            "success": True,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": safe_error(e),
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
                "message": "userNotFound",
            }

        admin_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == target_user_id,
            UserGroupRole.role == "admin",
        ).first()

        if admin_role:
            return {
                "success": False,
                "message": "adminDisableForbidden",
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
            "message": safe_error(e),
        }

    finally:
        db.close()