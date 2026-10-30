"""
邮箱占用规则：只有完成验证的账号才长期占用邮箱。

未验证的账号只临时占用 24 小时，给真正的邮箱主人留出收验证邮件的时间。
超过 24 小时仍未验证，别人再用这个邮箱注册（或改成这个邮箱）时，
就从那个未验证账号上收回邮箱。这样抢注别人邮箱的人最多只能占 24 小时。
"""

from datetime import timedelta

from sqlalchemy import func

from core.models import User
from core.time import now_columbus_naive
from poker.models import EmailVerification


UNVERIFIED_HOLD_HOURS = 24


def release_stale_unverified_email(db, email, exclude_user_id=None):
    """
    邮箱现在可以用了返回 True（没人占用，或者占用它的是超过 24 小时未验证的账号，已收回）。
    被已验证账号、或 24 小时内注册/改邮箱的未验证账号占用时返回 False。
    """
    holder = db.query(User).filter(User.email == email).with_for_update().first()
    if holder is None or holder.id == exclude_user_id:
        return True
    if holder.email_verified or holder.is_active == 0:
        return False

    # 占用开始的时间：最近一次发验证邮件（注册或改邮箱）的时间；没有记录就用注册时间
    last_claim = db.query(func.max(EmailVerification.created_at)).filter(
        EmailVerification.user_id == holder.id,
        EmailVerification.purpose == "verify_email",
    ).scalar() or holder.created_at

    if last_claim and last_claim > now_columbus_naive() - timedelta(hours=UNVERIFIED_HOLD_HOURS):
        return False

    holder.email = None
    db.query(EmailVerification).filter(
        EmailVerification.user_id == holder.id,
        EmailVerification.purpose == "verify_email",
        EmailVerification.used == 0,
    ).update({"used": 1}, synchronize_session=False)
    db.flush()
    return True
