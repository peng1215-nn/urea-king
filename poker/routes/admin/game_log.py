from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.organizer.game_log import get_game_logs_service
from poker.services.organizer.game_log import get_stats_service
from poker.services.organizer.game_log import delete_game_log_service
from poker.services.organizer.game_log import get_member_stats_service
from poker.services.organizer.game_log import get_member_trend_service
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates


router = APIRouter()


def require_admin(request: Request):
    return request.session.get("current_role") == "admin"


@router.get("/admin-game-logs", response_class=HTMLResponse)
def admin_game_logs_page(request: Request):
    if not require_admin(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="admin/game_log.html",
        context={"current_page": "game_logs"},
    )
    return add_no_cache_headers(response)


@router.get("/admin/game-log/list")
def admin_get_game_logs(request: Request, group_id: int, page: int = 1, q: str = ""):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}

    return get_game_logs_service(group_id=group_id, page=page, q=q)


@router.get("/admin/game-log/stats")
def admin_get_stats(request: Request, group_id: int):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}

    return get_stats_service(group_id=group_id)


@router.get("/admin/game-log/member-stats")
def admin_get_member_stats(request: Request, group_id: int):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}

    return get_member_stats_service(group_id=group_id)


@router.get("/admin/game-log/member-trend")
def admin_get_member_trend(request: Request, group_id: int, user_id: int):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}

    return get_member_trend_service(group_id=group_id, user_id=user_id)


@router.post("/admin/game-log/delete")
def admin_delete_game_log(request: Request, game_id: int = Form(...), group_id: int = Form(...)):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}

    return delete_game_log_service(game_id=game_id, group_id=group_id)
