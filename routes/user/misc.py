from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from services.organizer.announcement import get_announcements_service
from services.organizer.change_password import get_current_account_service
from services.organizer.change_password import update_nickname_service
from services.organizer.change_password import update_password_service
from services.organizer.game_log import get_game_logs_service
from services.organizer.game_log import get_stats_service
from services.common.common import add_no_cache_headers
from template_config import templates


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


# 修改密码
@router.get("/user-change-password", response_class=HTMLResponse)
def change_password_page(request: Request):
    if not require_user(request):
        return RedirectResponse(url="/login", status_code=302)
    response = templates.TemplateResponse(
        request=request,
        name="user/change_password.html",
        context={"current_page": "change_password"},
    )
    return add_no_cache_headers(response)


@router.get("/user/change-password/current")
def get_current_account(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    return get_current_account_service(user_id=get_user_id(request))


@router.post("/user/change-password/update-nickname")
def update_nickname(request: Request, nickname: str = Form(...)):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    result = update_nickname_service(user_id=get_user_id(request), nickname=nickname)
    if result.get("success"):
        request.session["nickname"] = result.get("nickname")
    return result


@router.post("/user/change-password/update-password")
def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    result = update_password_service(
        user_id=get_user_id(request),
        current_password=current_password,
        new_password=new_password,
        confirm_password=confirm_password,
    )
    if result.get("success"):
        request.session.clear()
    return result


# 牌局日志
@router.get("/user-game-logs", response_class=HTMLResponse)
def game_logs_page(request: Request):
    if not require_user(request):
        return RedirectResponse(url="/login", status_code=302)
    response = templates.TemplateResponse(
        request=request,
        name="user/game_log.html",
        context={"current_page": "game_logs"},
    )
    return add_no_cache_headers(response)


@router.get("/user/game-log/list")
def get_game_logs(request: Request, page: int = 1):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    user_id = get_user_id(request)
    return get_game_logs_service(group_id=int(group_id), page=page, viewer_user_id=int(user_id) if user_id else None)


@router.get("/user/game-log/stats")
def get_stats(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    return get_stats_service(group_id=int(group_id))