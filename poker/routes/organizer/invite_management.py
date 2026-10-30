from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from poker.core.rate_limit import GLOBAL_KEY, invite_creates_by_user, invite_failures_global, reserve
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
def create_invite_code(
    request: Request,
    code: str = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    # 每次创建都按用户计数；撞到已存在的邀请码相当于猜中别组的码，还计入全站猜码上限
    user_key = str(request.session.get("user_id"))
    attempt = reserve([
        (invite_creates_by_user, user_key, True),
        (invite_failures_global, GLOBAL_KEY, True),
    ])
    if attempt.wait:
        return JSONResponse(
            {"success": False, "message": "inviteCreateTooFrequent", "retry_after": attempt.wait},
            status_code=429,
        )

    result = create_invite_code_service(group_id=int(group_id), code=code)
    if result.get("message") != "inviteCodeExists":
        # 只退回全站猜码名额；按用户的创建次数照常计入
        invite_failures_global.undo(GLOBAL_KEY, attempt.stamp_of(invite_failures_global))
    return result


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