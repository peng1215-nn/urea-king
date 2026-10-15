from utils.time import now_columbus_naive
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
                    "id": a.id,
                    "title": a.title,
                    "content": a.content,
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


def create_announcement_service(title, content):
    db = SessionLocal()
    try:
        title, content = title.strip(), content.strip()
        if not title:
            return {"success": False, "message": "announcementTitleRequired"}
        if not content:
            return {"success": False, "message": "announcementContentRequired"}

        a = PokerAnnouncement(title=title, content=content, created_at=now_columbus_naive(), updated_at=now_columbus_naive())
        db.add(a)
        db.commit()
        db.refresh(a)
        return {"success": True, "message": "announcementCreateSuccess", "announcement_id": a.id}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def update_announcement_service(announcement_id, title, content):
    db = SessionLocal()
    try:
        a = db.query(PokerAnnouncement).filter(PokerAnnouncement.id == announcement_id).first()
        if not a:
            return {"success": False, "message": "announcementNotFound"}
        title, content = title.strip(), content.strip()
        if not title:
            return {"success": False, "message": "announcementTitleRequired"}
        if not content:
            return {"success": False, "message": "announcementContentRequired"}
        a.title = title
        a.content = content
        a.updated_at = now_columbus_naive()
        db.commit()
        return {"success": True, "message": "announcementUpdateSuccess"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def delete_announcement_service(announcement_id):
    db = SessionLocal()
    try:
        a = db.query(PokerAnnouncement).filter(PokerAnnouncement.id == announcement_id).first()
        if not a:
            return {"success": False, "message": "announcementNotFound"}
        db.delete(a)
        db.commit()
        return {"success": True, "message": "announcementDeleteSuccess"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
