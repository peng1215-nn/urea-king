from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.services.admin.change_password import (
    get_current_account_service,
    update_nickname_service,
    update_password_service,
)
from poker.services.common.common import add_no_cache_headers
from template_config import templates

router = APIRouter()


def require_admin(request: Request):
    return request.session.get("is_platform_admin") is True


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(request: Request):
    if not require_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    response = templates.TemplateResponse(
        request=request,
        name="admin/change_password.html",
        context={"current_page": "change_password"},
    )
    return add_no_cache_headers(response)


@router.get("/change-password/current")
def get_current_account(request: Request):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    return get_current_account_service(user_id=request.session.get("user_id"))


@router.post("/change-password/update-nickname")
def update_nickname(request: Request, nickname: str = Form(...)):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    result = update_nickname_service(user_id=request.session.get("user_id"), nickname=nickname)
    if result.get("success"):
        request.session["nickname"] = result.get("nickname")
    return result


@router.post("/change-password/update-password")
def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    result = update_password_service(
        user_id=request.session.get("user_id"),
        current_password=current_password,
        new_password=new_password,
        confirm_password=confirm_password,
    )
    if result.get("success"):
        request.session.clear()
    return result
