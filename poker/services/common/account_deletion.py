"""
用户自助注销（仅局头和普通用户）。

原则：只删除仅属于本人的信息；与其他用户有关的记录全部保留。
- 删除 / 清空：登录凭据、昵称、头像、注册邀请码、所有组的成员身份。
- 保留：他参与或主持过的牌局、牌局玩家记录（含当时记录的昵称）、筹码申请、
  局头给他设的备注名、系统日志——这些是其他人的牌局与账目的一部分。
- 用户名改成一个注册规则不允许的占位名，原用户名随即可以被别人重新注册。

不能注销的情况：
- 是管理员；
- 本人在任何进行中的牌局里，或者是某个进行中牌局的局头；
- 是局头，且所在组里除自己以外还有其他成员。
"""

import secrets

from passlib.context import CryptContext

from database import SessionLocal
from poker.core.errors import safe_error
from poker.models import Group, PokerGame, PokerGamePlayer, User, UserGroupRole


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

# 中文界面输入“注销”，英文界面输入 DELETE（不区分大小写），两者都接受
CONFIRM_WORDS = {"注销", "delete"}

DELETED_NICKNAME = "已注销用户"


def deleted_username(user_id):
    # 含 "#"，注册规则不允许，因此不会与任何真实用户名冲突
    return f"deleted#{user_id}"


def _fail(message, **extra):
    return {"success": False, "message": message, **extra}


def delete_own_account_service(user_id, password, confirm_text):
    if (confirm_text or "").strip().lower() not in CONFIRM_WORDS:
        return _fail("accountDeleteConfirmMismatch")

    db = SessionLocal()

    try:
        # 锁住这一行，避免注销过程中同时发生其它操作
        user = db.query(User).filter(User.id == user_id).with_for_update().first()

        if user is None or user.is_active == 0:
            return _fail("userNotFound")

        if not pwd_context.verify(password or "", user.password_hash):
            return _fail("currentPasswordIncorrect", password_failed=True)

        roles = db.query(UserGroupRole).filter(UserGroupRole.user_id == user_id).all()

        if any(role.role == "admin" for role in roles):
            return _fail("accountDeleteAdminForbidden")

        organizing_ongoing = db.query(PokerGame.id).filter(
            PokerGame.organizer_id == user_id,
            PokerGame.status == "ongoing",
        ).first()

        playing_ongoing = db.query(PokerGamePlayer.id).join(
            PokerGame, PokerGame.id == PokerGamePlayer.game_id
        ).filter(
            PokerGamePlayer.user_id == user_id,
            PokerGame.status == "ongoing",
        ).first()

        if organizing_ongoing or playing_ongoing:
            return _fail("accountDeleteOngoingGame")

        for role in roles:
            if role.role != "organizer":
                continue

            other_member = db.query(UserGroupRole.id).filter(
                UserGroupRole.group_id == role.group_id,
                UserGroupRole.user_id != user_id,
            ).first()

            if other_member:
                group = db.query(Group).filter(Group.id == role.group_id).first()
                return _fail(
                    "accountDeleteGroupHasMembers",
                    group_name=group.group_name if group else "",
                )

        original_username = user.username
        had_avatar = bool(user.avatar_url)

        # 仅属于本人的信息
        db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id
        ).delete(synchronize_session=False)

        user.username = deleted_username(user_id)
        user.nickname = DELETED_NICKNAME
        user.avatar_url = None
        user.invitation_code = None
        user.password_hash = pwd_context.hash(secrets.token_urlsafe(32))
        user.is_active = 0

        db.commit()

        return {
            "success": True,
            "original_username": original_username,
            "had_avatar": had_avatar,
        }

    except Exception as e:
        db.rollback()
        return _fail(safe_error(e))

    finally:
        db.close()
