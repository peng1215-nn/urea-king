from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.common.account import get_current_account_service
from poker.services.common.account import update_nickname_service
from poker.services.common.account import update_password_service
from poker.services.organizer.change_password import get_group_info_service
from poker.services.organizer.change_password import update_group_name_service
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates
from poker.core.middleware import clear_session_cache


router = APIRouter()


def require_organizer(request: Request):
    return request.session.get("current_role") == "organizer"


@router.get(
    "/organizer-change-password",
    response_class=HTMLResponse,
)
def organizer_change_password_page(request: Request):
    if not require_organizer(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="organizer/change_password.html",
        context={"current_page": "change_password"},
    )

    return add_no_cache_headers(response)


@router.get("/organizer/change-password/current")
def get_current_account(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    user_id = request.session.get("user_id")

    return get_current_account_service(user_id=user_id)


@router.post("/organizer/change-password/update-nickname")
def update_nickname(
    request: Request,
    nickname: str = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    user_id = request.session.get("user_id")

    result = update_nickname_service(
        user_id=user_id,
        nickname=nickname,
    )

    if result.get("success"):
        request.session["nickname"] = result.get("nickname")

    return result


@router.post("/organizer/change-password/update-password")
def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    user_id = request.session.get("user_id")

    result = update_password_service(
        user_id=user_id,
        current_password=current_password,
        new_password=new_password,
        confirm_password=confirm_password,
    )

    if result.get("success"):
        request.session.clear()
        # 让其他设备上的旧登录立即失效
        clear_session_cache()

    return result


@router.get("/organizer/group-info")
def get_group_info(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = request.session.get("current_group_id")
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    return get_group_info_service(group_id=int(group_id))


@router.post("/organizer/update-group-name")
def update_group_name(
    request: Request,
    group_name: str = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = request.session.get("current_group_id")
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    return update_group_name_service(group_id=int(group_id), group_name=group_name)