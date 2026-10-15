from database import SessionLocal
from poker.models import PokerAnnouncement


def get_announcements_service():
    db = SessionLocal()
    try:
        items = db.query(PokerAnnouncement).order_by(PokerAnnouncement.created_at.desc()).all()
        return {
            "success": True,
            "announcements": [
                {
                    "id": a.id, "title": a.title, "content": a.content,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
                    "updated_at": a.updated_at.strftime("%Y-%m-%d %H:%M") if a.updated_at else "",
                }
                for a in items
            ],
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()
