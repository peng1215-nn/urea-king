from datetime import datetime
from database import SessionLocal
from poker.models import Group
from poker.models import GroupMemberAlias
from poker.models import User
from poker.models import UserGroupRole


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
                "message": "组别不存在。",
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
            "message": str(e),
        }

    finally:
        db.close()


def save_member_alias_service(group_id: int, target_user_id: int, alias: str):
    db = SessionLocal()
    try:
        alias = alias.strip()
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
            existing.updated_at = datetime.utcnow()
        else:
            db.add(GroupMemberAlias(
                group_id=group_id,
                user_id=target_user_id,
                alias=alias,
                updated_at=datetime.utcnow(),
            ))
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
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
                "message": "该成员不在本组中。",
            }

        if record.role == "organizer":
            return {
                "success": False,
                "message": "不允许移除局头。",
            }

        db.delete(record)
        db.commit()

        return {
            "success": True,
            "message": "成员已移除。",
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()