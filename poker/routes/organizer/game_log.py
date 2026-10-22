from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response

from poker.services.organizer.game_log import get_game_logs_service
from poker.services.organizer.game_log import get_stats_service
from poker.services.organizer.game_log import delete_game_log_service
from poker.services.organizer.game_log import get_member_stats_service
from poker.services.organizer.game_log import get_member_trend_service
from poker.services.organizer.game_log import get_single_game_for_export
from poker.services.common.game_pdf import generate_game_pdf_bytes
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates


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
def get_game_logs(request: Request, page: int = 1, q: str = ""):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_game_logs_service(group_id=int(group_id), page=page, q=q)


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

@router.get("/organizer/game-log/member-stats")
def get_member_stats(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_member_stats_service(group_id=int(group_id))


@router.get("/organizer/game-log/member-trend")
def get_member_trend(request: Request, user_id: int):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}
    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}
    return get_member_trend_service(group_id=int(group_id), user_id=user_id)


@router.get("/organizer/game-log/export-pdf")
def export_game_pdf(request: Request, game_id: int, lang: str = "zh"):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    game = get_single_game_for_export(game_id=game_id, group_id=int(group_id))
    if not game:
        return {"success": False, "message": "gameNotFound"}

    # 组名从 session 里取不到，留空（前端传 group_name 参数）
    group_name = request.query_params.get("group_name", "")
    pdf_bytes = generate_game_pdf_bytes(game, group_name=group_name, lang=lang)

    filename = f"game_{game_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
