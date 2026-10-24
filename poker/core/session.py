"""
poker 模块的登录状态核对：每个请求都确认账号仍然有效（由 core/middleware.py 的 session_guard 调用）。
"""

from database import SessionLocal
from core.security import fingerprint_matches
from poker.models import User, UserGroupRole


# 不需要登录也能访问的页面：登录状态失效时这些页面照常打开，不跳转
PUBLIC_PATHS = ("/", "/login", "/register", "/group-join", "/delete-account", "/account/delete")


def session_key(session):
    user_id = session.get("user_id")
    if not user_id:
        return None
    return (
        user_id,
        session.get("current_group_id"),
        session.get("current_role"),
        session.get("pw_fp"),
    )


def session_is_valid(key):
    """账号存在且未被禁用、密码没改过、仍在该组担任该角色。"""
    user_id, group_id, role, pw_fp = key

    db = SessionLocal()
    try:
        row = db.query(User.is_active, User.password_hash).filter(User.id == user_id).first()
        if row is None or row[0] == 0:
            return False

        # 密码改过（本人修改、管理员重置、注销）之后，之前的登录全部失效
        if not fingerprint_matches(row[1], pw_fp):
            return False

        if role and group_id:
            membership = db.query(UserGroupRole.id).filter(
                UserGroupRole.user_id == user_id,
                UserGroupRole.group_id == group_id,
                UserGroupRole.role == role,
            ).first()
            if membership is None:
                return False

        return True
    finally:
        db.close()
