"""
昵称在全站唯一（不区分大小写，注销的账号不算），避免有人起一个和局头一模一样的昵称冒充。
"""

from sqlalchemy import func

from core.models import User


def nickname_taken(db, nickname, exclude_user_id=None):
    query = db.query(User.id).filter(
        func.lower(User.nickname) == (nickname or "").lower(),
        User.deleted_at.is_(None),
    )
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.first() is not None
