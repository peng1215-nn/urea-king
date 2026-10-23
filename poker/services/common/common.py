from database import SessionLocal
from poker.models import Group
from poker.models import User
from poker.models import PokerGame, PokerGamePlayer


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
        return {
            "success": False,
            "message": "notLoggedIn",
        }

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if not user:
            return {
                "success": False,
                "message": "userNotFound",
            }

        current_group_id = request.session.get(
            "current_group_id"
        )

        group = None

        if current_group_id:
            group = db.query(Group).filter(
                Group.id == current_group_id
            ).first()

        return {
            "success": True,
            "username": user.username,
            "nickname": user.nickname,
            "role": request.session.get("current_role"),
            "current_group_id": current_group_id,
            "current_group_code": request.session.get("current_group_code"),
            "current_group_name": (
                group.group_name
                if group
                else None
            ),
            "avatar_url": user.avatar_url,
        }

    finally:
        db.close()


def user_in_ongoing_game(db, user_id, group_id=None):
    """该用户是否在进行中的牌局里（可限定某个组）。用调用方的数据库会话。"""
    query = db.query(PokerGamePlayer.id).join(
        PokerGame, PokerGame.id == PokerGamePlayer.game_id
    ).filter(
        PokerGamePlayer.user_id == user_id,
        PokerGame.status == "ongoing",
    )
    if group_id is not None:
        query = query.filter(PokerGame.group_id == group_id)
    return query.first() is not None
