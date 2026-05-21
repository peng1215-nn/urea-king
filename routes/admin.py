from fastapi import APIRouter
from database import SessionLocal
from models import User, InvitationCode
from datetime import datetime
from app_state import APP_START_TIME


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

        user_count = db.query(User).filter(
            User.role == "user"
        ).count()

        unused_invitation_codes = db.query(InvitationCode).filter(
            InvitationCode.is_used == 0
        ).count()

        return {
            "success": True,
            "total_users": total_users,
            "admin_count": admin_count,
            "organizer_count": organizer_count,
            "user_count": user_count,
            "unused_invitation_codes": unused_invitation_codes
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


@router.get("/admin/system-monitor")
def system_monitor_data():

    uptime_seconds = int(
        (datetime.utcnow() - APP_START_TIME).total_seconds()
    )

    return {
        "success": True,
        "uptime_seconds": uptime_seconds
    }