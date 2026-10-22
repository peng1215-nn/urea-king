from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.organizer.announcement import get_announcements_service
from poker.services.organizer.change_password import get_current_account_service
from poker.services.organizer.change_password import update_nickname_service
from poker.services.organizer.change_password import update_password_service
from fastapi.responses import Response

from poker.services.organizer.game_log import get_game_logs_service
from poker.services.organizer.game_log import get_stats_service
from poker.services.organizer.game_log import get_member_stats_service
from poker.services.organizer.game_log import get_member_trend_service
from poker.services.organizer.game_log import get_single_game_for_export
from poker.services.common.game_pdf import generate_game_pdf_bytes
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates


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


@router.get("/user/game-log/export-pdf")
def user_export_game_pdf(request: Request, game_id: int, lang: str = "zh"):
    user_id = request.session.get("user_id")
    group_id = request.session.get("current_group_id")
    if not user_id or not group_id:
        return {"success": False, "message": "permissionDenied"}

    game = get_single_game_for_export(game_id=game_id, group_id=int(group_id))
    if not game:
        return {"success": False, "message": "gameNotFound"}

    group_name = request.query_params.get("group_name", "")
    pdf_bytes = generate_game_pdf_bytes(game, group_name=group_name, lang=lang)

    filename = f"game_{game_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
