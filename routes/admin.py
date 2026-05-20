from fastapi import APIRouter

from database import SessionLocal

from models import User
from models import InvitationCode


router = APIRouter()


@router.get("/admin/stats")
def admin_stats():

    db = SessionLocal()

    try:

        total_users = db.query(
            User
        ).count()

        organizer_count = db.query(
            User
        ).filter(
            User.role == "organizer"
        ).count()

        unused_invitation_codes = db.query(
            InvitationCode
        ).filter(
            InvitationCode.is_used == 0
        ).count()

        group_count = db.query(
            User.group_id
        ).filter(
            User.group_id.isnot(None)
        ).distinct().count()

        return {

            "success": True,

            "total_users":
                total_users,

            "organizer_count":
                organizer_count,

            "unused_invitation_codes":
                unused_invitation_codes,

            "group_count":
                group_count
        }

    finally:

        db.close()