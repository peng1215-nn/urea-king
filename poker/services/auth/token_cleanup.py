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
