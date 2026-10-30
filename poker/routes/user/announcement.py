"""普通用户：公告（显示在首页的公告卡片里）。"""

from fastapi import APIRouter
from fastapi import Request

from poker.services.common.announcement import get_announcements_service

from poker.routes.user.guard import user_api_denied


router = APIRouter()


@router.get("/user/announcements")
def get_announcements(request: Request):
    denied = user_api_denied(request)
    if denied is not None:
        return denied
    return get_announcements_service()
