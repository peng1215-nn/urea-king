"""Welcome page — module selection entry point."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from template_config import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    # If already logged in as platform admin, redirect to dashboard
    if request.session.get("is_platform_admin"):
        return RedirectResponse(url="/admin-dashboard", status_code=302)
    # If already logged in as poker user with a group, redirect to their dashboard
    if request.session.get("user_id") and request.session.get("current_role"):
        role = request.session["current_role"]
        return RedirectResponse(
            url="/organizer-dashboard" if role == "organizer" else "/user-dashboard",
            status_code=302,
        )
    return RedirectResponse(url="/poker/login", status_code=302)
