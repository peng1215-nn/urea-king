"""普通用户：牌局日志与统计。"""

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.common.game_log import get_game_logs_service
from poker.services.common.game_log import get_stats_service
from poker.services.common.game_log import get_member_stats_service
from poker.services.common.game_log import get_member_trend_service
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates


router = APIRouter()


def require_user(request: Request):
    return request.session.get("current_role") == "user"


def get_group_id(request: Request):
    return request.session.get("current_group_id")


def get_user_id(request: Request):
    return request.session.get("user_id")


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
def get_game_logs(request: Request, page: int = 1, q: str = ""):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    user_id = get_user_id(request)
    return get_game_logs_service(group_id=int(group_id), page=page, viewer_user_id=int(user_id) if user_id else None, q=q)


@router.get("/user/game-log/stats")
def get_stats(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    return get_stats_service(group_id=int(group_id))

@router.get("/user/game-log/member-stats")
def get_member_stats(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    return get_member_stats_service(group_id=int(group_id))


@router.get("/user/game-log/member-trend")
def get_member_trend(request: Request, user_id: int):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    return get_member_trend_service(group_id=int(group_id), user_id=user_id)
