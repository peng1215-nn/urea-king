"""
重发邮箱验证邮件服务。

频率限制（与注销冷却独立）：
- 同一邮箱两次重发间隔 >= 5 分钟
- 同一邮箱 24 小时内最多发 5 次（含注册时的第一次）
"""

import secrets
from datetime import timedelta

from core.errors import safe_error
from core.time import now_columbus_naive
from database import SessionLocal
from poker.core.email import dispatch, send_verify_email
from poker.models import EmailVerification, User

RESEND_INTERVAL_MINUTES = 5
RESEND_MAX_PER_DAY = 5
TOKEN_TTL_MINUTES = 15


def resend_verify_email_service(email: str, background_tasks=None) -> dict:
    email = (email or "").strip().lower()
    if not email:
        return {"success": False, "error_code": "resendEmailRequired"}

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        # 故意不区分"邮箱不存在"和"已验证"，防止邮箱枚举
        if not user or user.is_active == 0:
            return {"success": True, "error_code": "resendSent"}  # 假装发送成功

        # 已验证、发送太频繁、超出每日上限时都静默返回"已发送"，
        # 和邮箱不存在时的回复完全一样，防止借此判断邮箱是否注册
        if user.email_verified:
            return {"success": True, "error_code": "resendSent"}

        now = now_columbus_naive()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_5min = now - timedelta(minutes=RESEND_INTERVAL_MINUTES)

        recent_tokens = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user.id,
                EmailVerification.purpose == "verify_email",
                EmailVerification.created_at >= cutoff_24h,
            )
            .order_by(EmailVerification.created_at.desc())
            .all()
        )

        if len(recent_tokens) >= RESEND_MAX_PER_DAY:
            return {"success": True, "error_code": "resendSent"}

        if recent_tokens and recent_tokens[0].created_at >= cutoff_5min:
            return {"success": True, "error_code": "resendSent"}

        token = secrets.token_urlsafe(64)
        verification = EmailVerification(
            user_id=user.id,
            token=token,
            purpose="verify_email",
            expires_at=now + timedelta(minutes=TOKEN_TTL_MINUTES),
            used=0,
        )
        db.add(verification)
        db.commit()

        dispatch(background_tasks, send_verify_email, email, token)

        return {"success": True, "error_code": "resendSent"}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "resendFailed"}

    finally:
        db.close()
