from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from services.admin.announcement import create_announcement_service
from services.admin.announcement import delete_announcement_service
from services.admin.announcement import get_announcements_service
from services.admin.announcement import update_announcement_service
from services.common.common import add_no_cache_headers
from template_config import templates


router = APIRouter()


def require_admin(request: Request):
    return request.session.get("current_role") == "admin"


@router.get(
    "/announcement-management",
    response_class=HTMLResponse,
)
def announcement_management_page(request: Request):
    if not require_admin(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    response = templates.TemplateResponse(
        request=request,
        name="admin/announcement_management.html",
        context={
            "current_page": "announcement_management",
        },
    )

    return add_no_cache_headers(response)


@router.get("/admin/announcements")
def get_announcements(request: Request):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return get_announcements_service()


@router.post("/admin/announcements/create")
def create_announcement(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return create_announcement_service(
        title=title,
        content=content,
    )


@router.post("/admin/announcements/update")
def update_announcement(
    request: Request,
    announcement_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return update_announcement_service(
        announcement_id=announcement_id,
        title=title,
        content=content,
    )


@router.post("/admin/announcements/delete")
def delete_announcement(
    request: Request,
    announcement_id: int = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return delete_announcement_service(
        announcement_id=announcement_id,
    )