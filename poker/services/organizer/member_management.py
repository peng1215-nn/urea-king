from core.time import now_columbus_naive
from database import SessionLocal
from poker.models import Group
from poker.models import GroupMemberAlias
from poker.models import InvitationCode
from poker.models import User
from poker.models import UserGroupRole
from core.validators import check_name
from poker.core.validators import ALIAS_MAX
from core.errors import safe_error
from poker.services.common.common import user_in_ongoing_game


def _get_aliases(db, group_id: int) -> dict:
    """返回 {user_id: alias} 字典"""
    rows = db.query(GroupMemberAlias).filter(
        GroupMemberAlias.group_id == group_id
    ).all()
    return {r.user_id: r.alias for r in rows}


def get_organizer_members_service(group_id: int):
    db = SessionLocal()

    try:
        group = db.query(Group).filter(
            Group.id == group_id
        ).first()

        if not group:
            return {
                "success": False,
                "message": "groupNotFound",
            }

        rows = (
            db.query(UserGroupRole, User)
            .join(User, UserGroupRole.user_id == User.id)
            .filter(UserGroupRole.group_id == group_id)
            .order_by(
                UserGroupRole.role.asc(),
                User.id.asc(),
            )
            .all()
        )

        aliases = _get_aliases(db, group_id)
        members = []

        for user_group_role, user in rows:
            members.append({
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "alias": aliases.get(user.id, ""),
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
            "members": members,
            "group_name": group.group_name,
            "group_code": group.group_code,
            "organizer_count": sum(1 for m in members if m["role"] == "organizer"),
            "max_organizers": MAX_ORGANIZERS,
        }

    except Exception as e:
        return {
            "success": False,
            "message": safe_error(e),
        }

    finally:
        db.close()


def save_member_alias_service(group_id: int, target_user_id: int, alias: str):
    db = SessionLocal()
    try:
        alias, alias_error = check_name(alias, ALIAS_MAX)
        if alias_error:
            return {
                "success": False,
                "message": "textTooLong" if alias_error == "too_long" else "textInvalidChars",
            }
        # 只能给本组成员设置备注名。加共享锁：和"移除成员""退出组"互斥，
        # 不会在成员关系刚被删掉时又写进一条备注名
        is_member = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == group_id,
            UserGroupRole.user_id == target_user_id,
        ).with_for_update(read=True).first()
        if not is_member:
            return {"success": False, "message": "memberNotInGroup"}
        existing = db.query(GroupMemberAlias).filter(
            GroupMemberAlias.group_id == group_id,
            GroupMemberAlias.user_id == target_user_id,
        ).first()
        if alias == "":
            # 清空备注 → 删除记录
            if existing:
                db.delete(existing)
                db.commit()
            return {"success": True}
        if existing:
            existing.alias = alias
            existing.updated_at = now_columbus_naive()
        else:
            db.add(GroupMemberAlias(
                group_id=group_id,
                user_id=target_user_id,
                alias=alias,
                updated_at=now_columbus_naive(),
            ))
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def remove_member_service(group_id: int, target_user_id: int):
    db = SessionLocal()

    try:
        # 先锁住组：和"加入牌局"互斥，避免一边移除、一边把他加进牌局
        db.query(Group.id).filter(Group.id == group_id).with_for_update().first()

        record = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == group_id,
            UserGroupRole.user_id == target_user_id,
        ).first()

        if not record:
            return {
                "success": False,
                "message": "memberNotInGroup",
            }

        if record.role == "organizer":
            return {
                "success": False,
                "message": "cannotRemoveOrganizer",
            }

        # 和成员自己退出组一样：还在进行中的牌局里时不能移除
        if user_in_ongoing_game(db, target_user_id, group_id):
            return {
                "success": False,
                "message": "removeMemberOngoingGame",
            }

        # 释放该成员使用的邀请码仓位
        user = db.query(User).filter(User.id == target_user_id).first()
        group = db.query(Group).filter(Group.id == group_id).first()
        if user and group:
            used_invite = db.query(InvitationCode).filter(
                InvitationCode.group_code == group.group_code,
                InvitationCode.used_by_username == user.username,
                InvitationCode.is_used == 1,
            ).first()
            if used_invite:
                db.delete(used_invite)

        # 和成员自己退出组一样：删除局头给他设的备注名
        db.query(GroupMemberAlias).filter(
            GroupMemberAlias.group_id == group_id,
            GroupMemberAlias.user_id == target_user_id,
        ).delete(synchronize_session=False)

        db.delete(record)
        db.commit()

        return {
            "success": True,
            "message": "removeMemberSuccess",
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": safe_error(e),
        }

    finally:
        db.close()

# ── 第二个局头 ──
# 局头可以把组内成员设为局头（每组最多 MAX_ORGANIZERS 个）。局头之间完全平等：
# 不能互相移出、也没有撤掉别人局头身份的功能；不想当了自己卸任，变回普通成员。

MAX_ORGANIZERS = 2


def _organizer_count(db, group_id):
    return db.query(UserGroupRole).filter(
        UserGroupRole.group_id == group_id,
        UserGroupRole.role == "organizer",
    ).count()


def promote_member_service(group_id: int, target_user_id: int):
    db = SessionLocal()
    try:
        # 锁住组：两个局头同时提拔时排队执行，不会超过上限
        group = db.query(Group).filter(Group.id == group_id).with_for_update().first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        record = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == group_id,
            UserGroupRole.user_id == target_user_id,
        ).with_for_update().first()
        if not record:
            return {"success": False, "message": "memberNotInGroup"}
        if record.role == "organizer":
            return {"success": False, "message": "memberAlreadyOrganizer"}
        if record.role != "user":
            return {"success": False, "message": "permissionDenied"}

        user = db.query(User).filter(User.id == target_user_id).first()
        if not user or user.is_active == 0 or user.deleted_at is not None:
            return {"success": False, "message": "memberNotInGroup"}

        if _organizer_count(db, group_id) >= MAX_ORGANIZERS:
            return {"success": False, "message": "organizerLimitReached", "limit": MAX_ORGANIZERS}

        record.role = "organizer"
        db.commit()
        return {"success": True, "message": "promoteOrganizerSuccess"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def step_down_organizer_service(group_id: int, user_id: int):
    """局头自己卸任，变回普通成员。组里只剩自己一个局头时不能卸任。"""
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).with_for_update().first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        record = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == group_id,
            UserGroupRole.user_id == user_id,
            UserGroupRole.role == "organizer",
        ).with_for_update().first()
        if not record:
            return {"success": False, "message": "permissionDenied"}

        if _organizer_count(db, group_id) <= 1:
            return {"success": False, "message": "lastOrganizerCannotStepDown"}

        record.role = "user"
        db.commit()
        return {"success": True, "message": "stepDownSuccess"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()
