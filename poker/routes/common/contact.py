from fastapi import APIRouter, Request

from database import SessionLocal
from models import ContactMessage

router = APIRouter()


@router.post("/contact")
async def submit_contact(request: Request):
    data = await request.json()

    username = (data.get("username") or "").strip()
    description = (data.get("description") or "").strip()

    if not username or not description:
        return {"success": False, "message": "Username and description are required."}

    ip = request.client.host if request.client else None

    db = SessionLocal()
    try:
        msg = ContactMessage(
            username=username,
            description=description,
            ip_address=ip,
        )
        db.add(msg)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
