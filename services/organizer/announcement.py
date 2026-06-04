from database import SessionLocal
from models import Announcement


def get_announcements_service():
    db = SessionLocal()
    try:
        announcements = db.query(Announcement).order_by(
            Announcement.created_at.desc()
        ).all()

        return {
            "success": True,
            "announcements": [
                {
                    "id": item.id,
                    "title": item.title,
                    "content": item.content,
                    "created_at": (
                        item.created_at.strftime("%Y-%m-%d %H:%M")
                        if item.created_at else ""
                    ),
                    "updated_at": (
                        item.updated_at.strftime("%Y-%m-%d %H:%M")
                        if item.updated_at else ""
                    ),
                }
                for item in announcements
            ],
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()