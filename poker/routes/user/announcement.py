"""普通用户：公告（显示在首页的公告卡片里）。"""

from fastapi import APIRouter
from fastapi import Request

from poker.services.common.announcement import get_announcements_service


router = APIRouter()


def require_user(request: Request):
    return request.session.get("current_role") == "user"


@router.get("/user/announcements")
def get_announcements(request: Request):
    if not require_user(request):
        return {"success": False, "message": "permissionDenied"}
    return get_announcements_service()
