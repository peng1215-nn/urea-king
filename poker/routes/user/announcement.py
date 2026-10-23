"""普通用户：公告。"""

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.common.announcement import get_announcements_service
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates


router = APIRouter()


def require_user(request: Request):
    return request.session.get("current_role") == "user"


def get_group_id(request: Request):
    return request.session.get("current_group_id")


def get_user_id(request: Request):
    return request.session.get("user_id")


# 公告
@router.get("/user/announcements")
def get_announcements(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    return get_announcements_service()


@router.get("/user-announcements", response_class=HTMLResponse)
def announcements_page(request: Request):
    if not require_user(request):
        return RedirectResponse(url="/login", status_code=302)
    response = templates.TemplateResponse(
        request=request,
        name="user/announcement.html",
        context={"current_page": "announcements"},
    )
    return add_no_cache_headers(response)
