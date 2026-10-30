from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from poker.core.rate_limit import invite_creates_by_user
from poker.services.organizer.invite_management import create_invite_code_service
from poker.services.organizer.invite_management import delete_invite_code_service
from poker.services.organizer.invite_management import get_invite_codes_service
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates


router = APIRouter()


def require_organizer(request: Request):
    return request.session.get("current_role") == "organizer"


def get_group_id(request: Request):
    return request.session.get("current_group_id")


@router.get("/organizer-invite-management", response_class=HTMLResponse)
def invite_management_page(request: Request):
    if not require_organizer(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="organizer/invite_management.html",
        context={"current_page": "invite_management"},
    )
    return add_no_cache_headers(response)


@router.get("/organizer/invite/list")
def get_invite_codes(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_invite_codes_service(group_id=int(group_id))


@router.post("/organizer/invite/create")
def create_invite_code(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    # 每次创建都按用户计数，防止刷邀请码
    wait, _ = invite_creates_by_user.try_hit(str(request.session.get("user_id")))
    if wait:
        return JSONResponse(
            {"success": False, "message": "inviteCreateTooFrequent", "retry_after": wait},
            status_code=429,
        )

    return create_invite_code_service(group_id=int(group_id))


@router.post("/organizer/invite/delete")
def delete_invite_code(
    request: Request,
    invite_id: int = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return delete_invite_code_service(
        invite_id=invite_id,
        group_id=int(group_id),
    )