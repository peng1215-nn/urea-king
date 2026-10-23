"""
退出组与注销账号。

原则：只删除仅属于本人的信息；与其他用户有关的牌局记录保留。
例外：局头注销时，他的组（组里已经没有其他成员）连同组内全部记录一起删除。
系统日志属于安全审计记录，不删除。

- 普通用户退出组：删除该组的成员身份、局头给他设的备注名、他占用的邀请码名额。
  该组有他参与的进行中牌局时不能退出。他在该组历史牌局里的记录保留。
- 注销（在登录页用用户名 + 密码操作，不需要先登录）：
  - 管理员不能注销；
  - 普通用户：必须已经不属于任何组；
  - 局头：只能剩下自己作为局头的组，且组里没有其他成员、没有进行中的牌局；
    注销时这些组连同组内全部记录一起删除。
  - 账号本身做匿名化而不是删除整行：他在其他组历史牌局里的记录仍引用这个账号。
    用户名改成注册规则不允许的占位名，原用户名可以被重新注册。
"""

import secrets

from passlib.context import CryptContext

from database import SessionLocal
from poker.core.errors import safe_error
from poker.models import (
    ChipRequest,
    Group,
    GroupMemberAlias,
    InvitationCode,
    PokerGame,
    PokerGamePlayer,
    User,
    UserGroupRole,
)


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


def purge_group(db, group):
    """
    删除一个组及组内全部记录（不提交事务，由调用方提交）。
    管理员强制解散组与局头注销共用。返回各类记录的删除数量。
    """
    game_ids = [row[0] for row in db.query(PokerGame.id).filter(PokerGame.group_id == group.id).all()]
    counts = {"games": len(game_ids), "chip_requests": 0, "players": 0}

    if game_ids:
        counts["chip_requests"] = db.query(ChipRequest).filter(
            ChipRequest.game_id.in_(game_ids)
        ).delete(synchronize_session=False)
        counts["players"] = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id.in_(game_ids)
        ).delete(synchronize_session=False)
        db.query(PokerGame).filter(PokerGame.id.in_(game_ids)).delete(synchronize_session=False)

    counts["aliases"] = db.query(GroupMemberAlias).filter(
        GroupMemberAlias.group_id == group.id
    ).delete(synchronize_session=False)
    counts["members"] = db.query(UserGroupRole).filter(
        UserGroupRole.group_id == group.id
    ).delete(synchronize_session=False)
    counts["invites"] = db.query(InvitationCode).filter(
        InvitationCode.group_code == group.group_code
    ).delete(synchronize_session=False)

    db.delete(group)
    return counts


def _in_ongoing_game(db, user_id, group_id=None):
    query = db.query(PokerGamePlayer.id).join(
        PokerGame, PokerGame.id == PokerGamePlayer.game_id
    ).filter(
        PokerGamePlayer.user_id == user_id,
        PokerGame.status == "ongoing",
    )
    if group_id is not None:
        query = query.filter(PokerGame.group_id == group_id)
    return query.first() is not None


# ───────────────────────── 退出组 ─────────────────────────

def leave_group_service(user_id, group_id):
    db = SessionLocal()

    try:
        membership = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id,
            UserGroupRole.group_id == group_id,
        ).with_for_update().first()

        if membership is None:
            return _fail("leaveGroupNotMember")

        if membership.role != "user":
            return _fail("leaveGroupOnlyUser")

        if _in_ongoing_game(db, user_id, group_id):
            return _fail("leaveGroupOngoingGame")

        user = db.query(User).filter(User.id == user_id).first()
        group = db.query(Group).filter(Group.id == group_id).first()

        # 释放他占用的邀请码名额（与局头移除成员时的处理一致）
        if user and group:
            db.query(InvitationCode).filter(
                InvitationCode.group_code == group.group_code,
                InvitationCode.used_by_username == user.username,
                InvitationCode.is_used == 1,
            ).delete(synchronize_session=False)

        db.query(GroupMemberAlias).filter(
            GroupMemberAlias.group_id == group_id,
            GroupMemberAlias.user_id == user_id,
        ).delete(synchronize_session=False)

        db.delete(membership)
        db.commit()

        remaining = db.query(UserGroupRole).filter(UserGroupRole.user_id == user_id).count()

        return {
            "success": True,
            "group_code": group.group_code if group else "",
            "group_name": group.group_name if group else "",
            "remaining_groups": remaining,
        }

    except Exception as e:
        db.rollback()
        return _fail(safe_error(e))

    finally:
        db.close()


# ───────────────────────── 注销账号 ─────────────────────────

def delete_account_service(username, password, confirm_text):
    if (confirm_text or "").strip().lower() not in CONFIRM_WORDS:
        return _fail("accountDeleteConfirmMismatch")

    username = (username or "").strip()

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).with_for_update().first()

        if user is None:
            return _fail("loginUserNotFound", credential_failed=True)

        if not pwd_context.verify(password or "", user.password_hash):
            return _fail("loginPasswordIncorrect", credential_failed=True)

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

        if _in_ongoing_game(db, user.id):
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
