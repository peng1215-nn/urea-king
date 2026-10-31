"""
清理早已过期的验证、重置链接记录。这类记录只增不减，不清理会一直堆积。
过期 7 天以上的才删除（留一段时间方便排查问题）。服务启动时执行一次。
"""

import logging
from datetime import timedelta

from core.time import now_columbus_naive
from database import SessionLocal
from poker.models import EmailVerification


logger = logging.getLogger("poker.token_cleanup")

KEEP_DAYS = 7


def delete_expired_tokens():
    db = SessionLocal()
    try:
        cutoff = now_columbus_naive() - timedelta(days=KEEP_DAYS)
        deleted = db.query(EmailVerification).filter(
            EmailVerification.expires_at < cutoff,
        ).delete(synchronize_session=False)
        db.commit()
        if deleted:
            logger.info("deleted expired email tokens", extra={"count": deleted})
        return deleted
    except Exception:
        db.rollback()
        logger.exception("failed to delete expired email tokens")
        return 0
    finally:
        db.close()


def release_deleted_account_emails():
    """
    注销的账号只在 24 小时冷却期内保留邮箱（防止注销后立刻用同一邮箱重新注册），
    过了冷却期就把邮箱清掉，不再保存。和注册时的释放规则一致（见 email_owner.py）。
    """
    from poker.models import User
    from poker.services.auth.email_owner import DELETE_COOLDOWN_HOURS

    db = SessionLocal()
    try:
        cutoff = now_columbus_naive() - timedelta(hours=DELETE_COOLDOWN_HOURS)
        rows = db.query(User).filter(
            User.deleted_at.isnot(None),
            User.deleted_at < cutoff,
            User.email.isnot(None),
            ~User.email.like("deleted#%"),
        ).all()
        for user in rows:
            user.email = f"deleted#{user.id}@deleted"
            user.pending_email = None
        db.commit()
        if rows:
            logger.info("released emails of deleted accounts", extra={"count": len(rows)})
        return len(rows)
    except Exception:
        db.rollback()
        logger.exception("failed to release emails of deleted accounts")
        return 0
    finally:
        db.close()
