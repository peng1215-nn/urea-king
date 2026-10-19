from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.user.game import get_user_ongoing_games_service
from poker.services.user.game import submit_buyin_request_service
from poker.services.user.game import get_chip_auth_settings_service
from poker.services.user.game import update_chip_auth_service
from poker.services.common.common import add_no_cache_headers
from poker.template_config import templates


router = APIRouter()


def require_user(request: Request):
    return request.session.get("current_role") == "user"


def get_group_id(request: Request):
    return request.session.get("current_group_id")


def get_user_id(request: Request):
    return request.session.get("user_id")


@router.get("/user-game", response_class=HTMLResponse)
def user_game_page(request: Request):
    if not require_user(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="user/game.html",
        context={"current_page": "game"},
    )
    return add_no_cache_headers(response)


@router.get("/user/game/ongoing")
def get_user_ongoing_games(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    user_id = get_user_id(request)

    if not group_id or not user_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_user_ongoing_games_service(
        group_id=int(group_id),
        user_id=int(user_id),
    )


@router.get("/user/game/chip-auth-settings")
def get_chip_auth_settings(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    user_id = get_user_id(request)
    if not user_id:
        return {"success": False, "message": "notLoggedIn"}
    return get_chip_auth_settings_service(user_id=int(user_id))


@router.post("/user/game/chip-auth-update")
def update_chip_auth(
    request: Request,
    group_id: int = Form(...),
    allow: int = Form(...),
):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    user_id = get_user_id(request)
    if not user_id:
        return {"success": False, "message": "notLoggedIn"}
    return update_chip_auth_service(
        user_id=int(user_id),
        group_id=group_id,
        allow=allow,
    )


@router.post("/user/game/buyin-request")
def submit_buyin_request(
    request: Request,
    game_id: int = Form(...),
    amount: int = Form(...),
):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    user_id = get_user_id(request)

    if not group_id or not user_id:
        return {"success": False, "message": "noGroupSelected"}

    return submit_buyin_request_service(
        game_id=game_id,
        group_id=int(group_id),
        user_id=int(user_id),
        amount=amount,
    )