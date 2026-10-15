from utils.time import now_columbus_naive
from database import SessionLocal
from poker.models import PokerGroup, PokerInvitationCode, PokerUserGroupRole
from poker.utils.invite import generate_invite_code


def get_invite_codes_service(group_id: int):
    db = SessionLocal()
    try:
        group = db.query(PokerGroup).filter(PokerGroup.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        codes = db.query(PokerInvitationCode).filter(
            PokerInvitationCode.group_id == group_id,
        ).order_by(PokerInvitationCode.created_at.desc()).all()

        return {
            "success": True,
            "codes": [
                {
                    "id": c.id, "code": c.code, "role": c.role,
                    "is_used": c.is_used, "used_by_username": c.used_by_username,
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
                    "used_at": c.used_at.strftime("%Y-%m-%d %H:%M") if c.used_at else "",
                }
                for c in codes
            ],
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def create_invite_code_service(group_id: int, role: str = "user"):
    """Auto-generate a POKER-G{id}-XXXX code for this group."""
    db = SessionLocal()
    try:
        if role not in ["organizer", "user"]:
            return {"success": False, "message": "inviteRoleInvalid"}

        group = db.query(PokerGroup).filter(PokerGroup.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        for _ in range(10):
            code = generate_invite_code(group.id)
            if not db.query(PokerInvitationCode).filter(PokerInvitationCode.code == code).first():
                break

        invitation = PokerInvitationCode(
            code=code, group_id=group.id, role=role,
            is_used=0, created_at=now_columbus_naive(),
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return {
            "success": True,
            "code": {
                "id": invitation.id, "code": invitation.code, "role": invitation.role,
                "is_used": 0, "used_by_username": None,
                "created_at": invitation.created_at.strftime("%Y-%m-%d %H:%M"),
                "used_at": "",
            },
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def delete_invite_code_service(invite_id: int, group_id: int):
    db = SessionLocal()
    try:
        inv = db.query(PokerInvitationCode).filter(
            PokerInvitationCode.id == invite_id,
            PokerInvitationCode.group_id == group_id,
        ).first()
        if not inv:
            return {"success": False, "message": "inviteCodeNotFound"}
        if inv.is_used == 1:
            return {"success": False, "message": "usedInviteDeleteForbidden"}

        db.delete(inv)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
