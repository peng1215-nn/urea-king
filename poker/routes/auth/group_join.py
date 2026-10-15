from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from database import SessionLocal
from core.models import PlatformUser
from core.utils.security import verify_password
from poker.services.auth.group_join import poker_group_join_service
from template_config import templates

router = APIRouter()


@router.get("/group-join", response_class=HTMLResponse)
def group_join_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/group_join.html")


@router.post("/group-join")
def group_join(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
):
    """Verify credentials then join a group via invite code."""
    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.username == username.strip()).first()
        if not user:
            return {"success": False, "error_code": "loginUserNotFound"}
        if not verify_password(password, user.password_hash):
            return {"success": False, "error_code": "loginPasswordIncorrect"}
        if user.is_active == 0:
            return {"success": False, "error_code": "loginAccountDisabled"}
    finally:
        db.close()

    return poker_group_join_service(
        user_id=user.id,
        username=user.username,
        invite_code=invite_code,
    )
