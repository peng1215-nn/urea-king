from database import SessionLocal
from poker.models import PokerGroup, PokerUserGroupRole
from core.models import PlatformUser


def get_organizer_members_service(group_id: int):
    db = SessionLocal()
    try:
        group = db.query(PokerGroup).filter(PokerGroup.id == group_id).first()
        if not group:
            return {"success": False, "message": "组别不存在。"}

        rows = (
            db.query(PokerUserGroupRole, PlatformUser)
            .join(PlatformUser, PokerUserGroupRole.user_id == PlatformUser.id)
            .filter(PokerUserGroupRole.group_id == group_id)
            .order_by(PokerUserGroupRole.role.asc(), PlatformUser.id.asc())
            .all()
        )

        members = [
            {
                "id": user.id, "username": user.username, "nickname": user.nickname,
                "role": ugr.role, "group_id": group.id,
                "group_code": group.group_code, "group_name": group.group_name,
                "avatar_url": user.avatar_url, "is_active": user.is_active,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "",
            }
            for ugr, user in rows
        ]

        return {"success": True, "members": members, "group_name": group.group_name, "group_code": group.group_code}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def remove_member_service(group_id: int, target_user_id: int):
    db = SessionLocal()
    try:
        record = db.query(PokerUserGroupRole).filter(
            PokerUserGroupRole.group_id == group_id,
            PokerUserGroupRole.user_id == target_user_id,
        ).first()
        if not record:
            return {"success": False, "message": "该成员不在本组中。"}
        if record.role == "organizer":
            return {"success": False, "message": "不允许移除局头。"}

        db.delete(record)
        db.commit()
        return {"success": True, "message": "成员已移除。"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
