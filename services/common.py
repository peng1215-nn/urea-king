from database import SessionLocal
from models import User


def add_no_cache_headers(response):
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


def get_current_user_service(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return {"success": False, "message": "未登录。"}

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "用户不存在。"}

        return {
            "success": True,
            "username": user.username,
            "nickname": user.nickname,
            "role": user.role,
            "avatar_url": user.avatar_url,
        }

    finally:
        db.close()