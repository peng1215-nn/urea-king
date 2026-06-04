from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from typing import List
from pydantic import BaseModel

from services.admin.audit_log import write_audit_log
from services.common.common import add_no_cache_headers
from services.organizer.game_management import add_player_to_game_service
from services.organizer.game_management import approve_chip_request_service
from services.organizer.game_management import finish_game_service
from services.organizer.game_management import get_game_history_service
from services.organizer.game_management import get_group_members_for_game_service
from services.organizer.game_management import get_ongoing_games_service
from services.organizer.game_management import organizer_buyin_service
from services.organizer.game_management import reject_chip_request_service
from services.organizer.game_management import remove_player_from_game_service
from services.organizer.game_management import start_game_service
from services.organizer.game_management import update_cash_out_service
from template_config import templates


router = APIRouter()


def require_organizer(request: Request):
    return request.session.get("current_role") == "organizer"


def get_group_id(request: Request):
    return request.session.get("current_group_id")


def get_user_id(request: Request):
    return request.session.get("user_id")


@router.get("/organizer-games", response_class=HTMLResponse)
def game_management_page(request: Request):
    if not require_organizer(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="organizer/game_management.html",
        context={"current_page": "game_management"},
    )
    return add_no_cache_headers(response)


@router.get("/organizer/game/ongoing")
def get_ongoing_games(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_ongoing_games_service(group_id=int(group_id))


@router.get("/organizer/game/history")
def get_game_history(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_game_history_service(group_id=int(group_id))


@router.get("/organizer/game/members")
def get_group_members(request: Request):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return get_group_members_for_game_service(group_id=int(group_id))


class StartGameBody(BaseModel):
    name: str = ""
    preselected_user_ids: List[int] = []


@router.post("/organizer/game/start")
def start_game(request: Request, body: StartGameBody):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    user_id = get_user_id(request)

    if not group_id or not user_id:
        return {"success": False, "message": "noGroupSelected"}

    result = start_game_service(
        group_id=int(group_id),
        organizer_id=int(user_id),
        name=body.name,
        preselected_user_ids=body.preselected_user_ids,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="START_GAME",
            target_type="poker_game",
            target_id=result.get("game_id"),
            old_value=None,
            new_value=f"group_id={group_id}, name={body.name}",
            operator_id=user_id,
            operator_username=request.session.get("username"),
        )

    return result


@router.post("/organizer/game/add-player")
def add_player(
    request: Request,
    game_id: int = Form(...),
    user_id: int = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    organizer_id = get_user_id(request)

    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return add_player_to_game_service(
        game_id=game_id,
        group_id=int(group_id),
        user_id=user_id,
        organizer_id=int(organizer_id),
    )


@router.post("/organizer/game/remove-player")
def remove_player(
    request: Request,
    game_id: int = Form(...),
    user_id: int = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return remove_player_from_game_service(
        game_id=game_id,
        group_id=int(group_id),
        user_id=user_id,
    )


@router.post("/organizer/game/approve-request")
def approve_request(
    request: Request,
    request_id: int = Form(...),
    game_id: int = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    user_id = get_user_id(request)

    if not group_id or not user_id:
        return {"success": False, "message": "noGroupSelected"}

    return approve_chip_request_service(
        request_id=request_id,
        game_id=game_id,
        group_id=int(group_id),
        resolver_id=int(user_id),
    )


@router.post("/organizer/game/reject-request")
def reject_request(
    request: Request,
    request_id: int = Form(...),
    game_id: int = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    user_id = get_user_id(request)

    if not group_id or not user_id:
        return {"success": False, "message": "noGroupSelected"}

    return reject_chip_request_service(
        request_id=request_id,
        game_id=game_id,
        group_id=int(group_id),
        resolver_id=int(user_id),
    )


@router.post("/organizer/game/organizer-buyin")
def organizer_buyin(
    request: Request,
    game_id: int = Form(...),
    user_id: int = Form(...),
    amount: int = Form(...),
    buy_type: str = Form("normal"),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return organizer_buyin_service(
        game_id=game_id,
        group_id=int(group_id),
        user_id=user_id,
        amount=amount,
        buy_type=buy_type,
    )


class FinishGameBody(BaseModel):
    game_id: int
    force: bool = False
    player_cash_outs: List[dict]
    organizer_insurance_final: int = 0
    organizer_anti_final: int = 0


@router.post("/organizer/game/finish")
def finish_game(request: Request, body: FinishGameBody):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    user_id = get_user_id(request)

    if not group_id or not user_id:
        return {"success": False, "message": "noGroupSelected"}

    result = finish_game_service(
        game_id=body.game_id,
        group_id=int(group_id),
        organizer_id=int(user_id),
        player_cash_outs=body.player_cash_outs,
        organizer_insurance_final=body.organizer_insurance_final,
        organizer_anti_final=body.organizer_anti_final,
        force=body.force,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="FINISH_GAME",
            target_type="poker_game",
            target_id=body.game_id,
            old_value="ongoing",
            new_value=f"finished, balanced={result.get('is_balanced')}",
            operator_id=user_id,
            operator_username=request.session.get("username"),
        )

    return result


@router.post("/organizer/game/update-cashout")
def update_cash_out(
    request: Request,
    game_id: int = Form(...),
    user_id: int = Form(...),
    cash_out: int = Form(...),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return update_cash_out_service(
        game_id=game_id,
        group_id=int(group_id),
        user_id=user_id,
        cash_out=cash_out,
    )