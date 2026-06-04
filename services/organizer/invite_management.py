import uuid
from datetime import datetime
from utils.time import now_columbus_naive

from database import SessionLocal
from models import Group
from models import InvitationCode
from models import UserGroupRole


def get_invite_codes_service(group_id: int):
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        codes = db.query(InvitationCode).filter(
            InvitationCode.group_code == group.group_code,
        ).order_by(InvitationCode.created_at.desc()).all()

        return {
            "success": True,
            "codes": [
                {
                    "id": c.id,
                    "code": c.code,
                    "role": c.role,
                    "is_used": c.is_used,
                    "used_by_username": c.used_by_username,
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


def create_invite_code_service(group_id: int, code: str):
    db = SessionLocal()
    try:
        code = code.strip()

        if not code:
            return {"success": False, "message": "inviteCodeRequired"}

        if len(code) > 50:
            return {"success": False, "message": "inviteCodeTooLong"}

        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        existing = db.query(InvitationCode).filter(
            InvitationCode.code == code
        ).first()

        if existing:
            return {"success": False, "message": "inviteCodeExists"}

        invitation = InvitationCode(
            code=code,
            assigned_to=None,
            group_code=group.group_code,
            role="user",
            is_used=0,
            used_by_username=None,
            created_at=now_columbus_naive(),
            used_at=None,
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return {
            "success": True,
            "code": {
                "id": invitation.id,
                "code": invitation.code,
                "role": invitation.role,
                "is_used": invitation.is_used,
                "used_by_username": None,
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
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        invitation = db.query(InvitationCode).filter(
            InvitationCode.id == invite_id,
            InvitationCode.group_code == group.group_code,
        ).first()

        if not invitation:
            return {"success": False, "message": "inviteCodeNotFound"}

        if invitation.is_used == 1:
            return {"success": False, "message": "usedInviteDeleteForbidden"}

        db.delete(invitation)
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()