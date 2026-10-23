"""
登录页注销账号（用户名 + 密码 + 确认文字，不需要先登录）。

原则：只删除仅属于本人的信息；与其他用户有关的牌局记录保留。系统日志保留。
- 管理员不能注销；
- 普通用户：必须已经不属于任何组（先在资料页退出组）；
- 局头：只能剩下自己作为局头的组，且组里没有其他成员、没有进行中的牌局；
  注销时这些组连同组内全部记录一起删除。
- 账号本身做匿名化而不是删除整行：他在其他组历史牌局里的记录仍引用这个账号。
  用户名改成注册规则不允许的占位名，原用户名可以被重新注册。
"""

import secrets


from database import SessionLocal
from poker.core.errors import safe_error
from poker.core.security import verify_user_password
from poker.models import Group, PokerGame, User, UserGroupRole
from poker.services.common.common import user_in_ongoing_game
from poker.services.common.group_purge import purge_group
from poker.core.security import pwd_context



# 中文界面输入“注销”，英文界面输入 DELETE（不区分大小写），两者都接受
CONFIRM_WORDS = {"注销", "delete"}

DELETED_NICKNAME = "已注销用户"


def deleted_username(user_id):
    # 含 "#"，注册规则不允许，因此不会与任何真实用户名冲突
    return f"deleted#{user_id}"


def _fail(message, **extra):
    return {"success": False, "message": message, **extra}


def delete_account_service(username, password, confirm_text):
    if (confirm_text or "").strip().lower() not in CONFIRM_WORDS:
        return _fail("accountDeleteConfirmMismatch")

    username = (username or "").strip()

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).with_for_update().first()

        if not verify_user_password(user, password):
            return _fail("loginInvalidCredentials", credential_failed=True)

        if user.is_active == 0:
            return _fail("loginAccountDisabled")

        roles = db.query(UserGroupRole).filter(UserGroupRole.user_id == user.id).all()

        if any(role.role == "admin" for role in roles):
            return _fail("accountDeleteAdminForbidden")

        member_of = [role for role in roles if role.role != "organizer"]
        if member_of:
            names = [
                g.group_name or g.group_code
                for g in db.query(Group).filter(Group.id.in_([r.group_id for r in member_of])).all()
            ]
            return _fail("accountDeleteStillInGroup", group_name="、".join(names))

        organized = [role for role in roles if role.role == "organizer"]
        groups = []

        for role in organized:
            group = db.query(Group).filter(Group.id == role.group_id).with_for_update().first()
            if group is None:
                continue

            other_member = db.query(UserGroupRole.id).filter(
                UserGroupRole.group_id == group.id,
                UserGroupRole.user_id != user.id,
            ).first()
            if other_member:
                return _fail("accountDeleteGroupHasMembers", group_name=group.group_name or group.group_code)

            ongoing = db.query(PokerGame.id).filter(
                PokerGame.group_id == group.id,
                PokerGame.status == "ongoing",
            ).first()
            if ongoing:
                return _fail("accountDeleteOngoingGame")

            groups.append(group)

        if user_in_ongoing_game(db, user.id):
            return _fail("accountDeleteOngoingGame")

        deleted_groups = []
        for group in groups:
            info = {"group_id": group.id, "group_code": group.group_code, "group_name": group.group_name}
            info["counts"] = purge_group(db, group)
            deleted_groups.append(info)

        user_id = user.id
        had_avatar = bool(user.avatar_url)

        # 账号本身：只清除仅属于本人的信息
        db.query(UserGroupRole).filter(UserGroupRole.user_id == user_id).delete(synchronize_session=False)
        user.username = deleted_username(user_id)
        user.nickname = DELETED_NICKNAME
        user.avatar_url = None
        user.invitation_code = None
        user.password_hash = pwd_context.hash(secrets.token_urlsafe(32))
        user.is_active = 0

        db.commit()

        return {
            "success": True,
            "user_id": user_id,
            "original_username": username,
            "had_avatar": had_avatar,
            "deleted_groups": deleted_groups,
        }

    except Exception as e:
        db.rollback()
        return _fail(safe_error(e))

    finally:
        db.close()
