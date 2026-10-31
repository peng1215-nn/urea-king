"""
牌局审计报告：牌局日志里每一局都可以打开对应的报告页（单独页面）。

- 局头、普通成员：只能看自己当前所在组的牌局（组取自会话，不接受参数）。
- 管理员：可以看任意组的牌局，需要传 group_id。
- 只提供已结束的牌局。
"""

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.errors import safe_error
from database import SessionLocal
from poker.services.common.common import add_no_cache_headers
from poker.services.common.game_events import build_game_report
from poker.template_config import templates


router = APIRouter()

REPORT_ROLES = ("admin", "organizer", "user")

GAME_LOG_PAGES = {
    "admin": "/admin-game-logs",
    "organizer": "/organizer-game-logs",
    "user": "/user-game-logs",
}


def _role(request: Request):
    if not request.session.get("user_id"):
        return None
    role = request.session.get("current_role")
    return role if role in REPORT_ROLES else None


def _report_group_id(request: Request, role, group_id):
    """管理员用参数里的组；其他角色只能用会话里的当前组。"""
    if role == "admin":
        return group_id
    current = request.session.get("current_group_id")
    return int(current) if current else None


@router.get("/game-report", response_class=HTMLResponse)
def game_report_page(request: Request):
    role = _role(request)
    if role is None:
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="common/game_report.html",
        # role 决定页面背景：局头看到局头的背景，普通成员看到成员的背景
        context={"back_url": GAME_LOG_PAGES[role], "role": role},
    )
    return add_no_cache_headers(response)


@router.get("/game-report/data")
def game_report_data(request: Request, game_id: int, group_id: Optional[int] = None):
    role = _role(request)
    if role is None:
        return {"success": False, "message": "permissionDenied"}

    report_group_id = _report_group_id(request, role, group_id)
    if not report_group_id:
        return {"success": False, "message": "noGroupSelected"}

    db = SessionLocal()
    try:
        report = build_game_report(db, game_id, report_group_id)
        if report is None:
            return {"success": False, "message": "gameNotFound"}
        return report
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()
