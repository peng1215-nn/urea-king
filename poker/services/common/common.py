from database import SessionLocal
from poker.models import PokerGroup, PokerUserGroupRole
from core.models import PlatformUser


def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def get_current_user_service(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"success": False, "message": "未登录。"}

    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
        if not user:
            return {"success": False, "message": "用户不存在。"}

        current_group_id = request.session.get("current_group_id")
        group = None
        if current_group_id:
            group = db.query(PokerGroup).filter(PokerGroup.id == current_group_id).first()

        return {
            "success": True,
            "username": user.username,
            "nickname": user.nickname,
            "role": request.session.get("current_role"),
            "current_group_id": current_group_id,
            "current_group_code": request.session.get("current_group_code"),
            "current_group_name": group.group_name if group else None,
            "avatar_url": user.avatar_url,
        }
    finally:
        db.close()
