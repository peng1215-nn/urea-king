from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database import SessionLocal
from poker.models import PokerGroup, PokerUserGroupRole
from poker.services.auth.login import login_user_service
from template_config import templates

router = APIRouter()


def render_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/login.html")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_login_page(request)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render_login_page(request)


@router.post("/login")
def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    return login_user_service(request=request, username=username, password=password)


@router.get("/group-select", response_class=HTMLResponse)
def group_select_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request=request, name="auth/group_select.html")


@router.post("/select-group")
def select_group(request: Request, group_id: int = Form(...)):
    db = SessionLocal()
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return {"success": False, "error_code": "loginRequired"}

        ugr = db.query(PokerUserGroupRole).filter(
            PokerUserGroupRole.user_id == user_id,
            PokerUserGroupRole.group_id == group_id,
        ).first()
        if not ugr:
            return {"success": False, "error_code": "groupAccessDenied"}

        group = db.query(PokerGroup).filter(PokerGroup.id == group_id).first()
        if not group:
            return {"success": False, "error_code": "groupNotFound"}

        request.session["current_group_id"] = group.id
        request.session["current_group_code"] = group.group_code
        request.session["current_role"] = ugr.role

        redirect_url = "/organizer-dashboard" if ugr.role == "organizer" else "/user-dashboard"
        return {"success": True, "role": ugr.role, "redirect_url": redirect_url}
    finally:
        db.close()
