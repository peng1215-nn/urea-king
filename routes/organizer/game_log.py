from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from services.organizer.game_log import get_game_logs_service
from services.organizer.game_log import get_stats_service
from services.organizer.game_log import delete_game_log_service
from services.common.common import add_no_cache_headers
from template_config import templates


router = APIRouter()


def require_organizer(request: Request):
    return request.session.get("current_role") == "organizer"


def get_group_id(request: Request):
    return request.session.get("current_group_id")


@router.get("/organizer-game-logs", response_class=HTMLResponse)
def game_logs_page(request: Request):
    if not require_organizer(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="organizer/game_log.html",
        context={"current_page": "game_logs"},
    )
    return add_no_cache_headers(response)


@router.get("/organizer/game-log/list")
def get_game_logs(request: Request, page: int = 1):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_game_logs_service(group_id=int(group_id), page=page)


@router.get("/organizer/game-log/stats")
def get_stats(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_stats_service(group_id=int(group_id))


@router.post("/organizer/game-log/delete")
def delete_game_log(request: Request, game_id: int = Form(...)):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return delete_game_log_service(game_id=game_id, group_id=int(group_id))