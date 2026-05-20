from fastapi import APIRouter

from database import SessionLocal
from models import User, InvitationCode

router = APIRouter()


@router.get("/admin/stats")
def admin_stats():
    db = SessionLocal()

    try:
        total_users = db.query(User).count()

        admin_count = db.query(User).filter(
            User.role == "admin"
        ).count()

        organizer_count = db.query(User).filter(
            User.role == "organizer"
        ).count()

        unused_invitation_codes = db.query(InvitationCode).filter(
            InvitationCode.is_used == 0
        ).count()

        return {
            "success": True,
            "total_users": total_users,
            "admin_count": admin_count,
            "organizer_count": organizer_count,
            "unused_invitation_codes": unused_invitation_codes
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()