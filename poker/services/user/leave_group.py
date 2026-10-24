"""
普通用户退出当前组。

删除该组的成员身份、局头给他设的备注名、他占用的邀请码名额。
该组有他参与的进行中牌局时不能退出。他在该组历史牌局里的记录保留。
"""

from database import SessionLocal
from core.errors import safe_error
from poker.models import Group, GroupMemberAlias, InvitationCode, User, UserGroupRole
from poker.services.common.common import user_in_ongoing_game


def _fail(message, **extra):
    return {"success": False, "message": message, **extra}


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

        if user_in_ongoing_game(db, user_id, group_id):
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
