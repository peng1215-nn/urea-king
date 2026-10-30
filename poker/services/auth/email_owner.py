"""
邮箱归属的统一判断：注册、更换验证邮箱、点验证链接都用这一套规则。

- 只有已验证的账号占用邮箱（未验证账号的邮箱在 pending_email 里，不占用）。
- 注销的账号保留原邮箱 24 小时（冷却期），之后释放，邮箱可以重新使用。
"""

from datetime import timedelta

from core.models import User
from core.time import now_columbus_naive


DELETE_COOLDOWN_HOURS = 24


def email_blocked_by_other(db, email, exclude_user_id=None):
    """
    邮箱能用返回 None；被别的已验证账号占用返回 "taken"；属于注销不足 24 小时的账号返回 "cooldown"。
    注销超过 24 小时的账号会在这里释放邮箱（改成 deleted#id@deleted）。
    """
    holder = db.query(User).filter(User.email == email).with_for_update().first()
    if holder is None or holder.id == exclude_user_id:
        return None

    if holder.is_active == 0 and holder.deleted_at is not None:
        if holder.deleted_at > now_columbus_naive() - timedelta(hours=DELETE_COOLDOWN_HOURS):
            return "cooldown"
        holder.email = f"deleted#{holder.id}@deleted"
        db.flush()
        return None

    return "taken"
