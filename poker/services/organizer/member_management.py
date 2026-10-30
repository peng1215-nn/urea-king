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
        # 只能给本组成员设置备注名
        is_member = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == group_id,
            UserGroupRole.user_id == target_user_id,
        ).first()
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