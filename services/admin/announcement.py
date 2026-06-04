from datetime import datetime
from utils.time import now_columbus_naive

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
                        if item.created_at
                        else ""
                    ),
                    "updated_at": (
                        item.updated_at.strftime("%Y-%m-%d %H:%M")
                        if item.updated_at
                        else ""
                    ),
                }
                for item in announcements
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def create_announcement_service(title, content):
    db = SessionLocal()

    try:
        title = title.strip()
        content = content.strip()

        if not title:
            return {
                "success": False,
                "message": "announcementTitleRequired",
            }

        if not content:
            return {
                "success": False,
                "message": "announcementContentRequired",
            }

        announcement = Announcement(
            title=title,
            content=content,
            created_at=now_columbus_naive(),
            updated_at=now_columbus_naive(),
        )

        db.add(announcement)
        db.commit()
        db.refresh(announcement)

        return {
            "success": True,
            "message": "announcementCreateSuccess",
            "announcement_id": announcement.id,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def update_announcement_service(
    announcement_id,
    title,
    content,
):
    db = SessionLocal()

    try:
        announcement = db.query(Announcement).filter(
            Announcement.id == announcement_id
        ).first()

        if not announcement:
            return {
                "success": False,
                "message": "announcementNotFound",
            }

        title = title.strip()
        content = content.strip()

        if not title:
            return {
                "success": False,
                "message": "announcementTitleRequired",
            }

        if not content:
            return {
                "success": False,
                "message": "announcementContentRequired",
            }

        announcement.title = title
        announcement.content = content
        announcement.updated_at = now_columbus_naive()

        db.commit()

        return {
            "success": True,
            "message": "announcementUpdateSuccess",
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def delete_announcement_service(announcement_id):
    db = SessionLocal()

    try:
        announcement = db.query(Announcement).filter(
            Announcement.id == announcement_id
        ).first()

        if not announcement:
            return {
                "success": False,
                "message": "announcementNotFound",
            }

        db.delete(announcement)
        db.commit()

        return {
            "success": True,
            "message": "announcementDeleteSuccess",
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()