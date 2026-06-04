from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from services.organizer.announcement import get_announcements_service
from services.common.common import add_no_cache_headers
from template_config import templates


router = APIRouter()


def require_organizer(request: Request):
    return request.session.get("current_role") == "organizer"


@router.get("/organizer/announcements")
def get_announcements(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}
    return get_announcements_service()


@router.get("/organizer-announcements", response_class=HTMLResponse)
def announcements_page(request: Request):
    if not require_organizer(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="organizer/announcement.html",
        context={"current_page": "announcements"},
    )
    return add_no_cache_headers(response)