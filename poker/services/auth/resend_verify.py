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
RESEND_MAX_ACCOUNTS = 3
TOKEN_TTL_MINUTES = 15


def resend_verify_email_service(email: str, background_tasks=None) -> dict:
    email = (email or "").strip().lower()
    if not email:
        return {"success": False, "error_code": "resendEmailRequired"}

    db = SessionLocal()
    try:
        # 邮箱已经被某个账号验证过：不再给任何账号发验证邮件（静默返回"已发送"）
        if db.query(User.id).filter(User.email == email).first():
            return {"success": True, "error_code": "resendSent"}

        # 在等验证这个邮箱的所有账号（最多取最新的 3 个），每个账号各发一封，邮件里写明账号名。
        # 只发最新那一个的话，抢注者在你之后注册，你点"重发"收到的就是他的链接
        users = (
            db.query(User)
            .filter(User.pending_email == email, User.email_verified == 0, User.is_active == 1)
            .order_by(User.id.desc())
            .limit(RESEND_MAX_ACCOUNTS)
            .all()
        )

        now = now_columbus_naive()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_5min = now - timedelta(minutes=RESEND_INTERVAL_MINUTES)
        to_send = []

        # 每个账号各自的频率限制；超出的静默跳过，回复始终是"已发送"，防止借此判断邮箱是否注册
        for user in users:
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
                continue
            if recent_tokens and recent_tokens[0].created_at >= cutoff_5min:
                continue

            token = secrets.token_urlsafe(64)
            db.add(EmailVerification(
                user_id=user.id,
                token=token,
                purpose="verify_email",
                expires_at=now + timedelta(minutes=TOKEN_TTL_MINUTES),
                used=0,
            ))
            to_send.append((token, user.username))

        db.commit()
        for token, username in to_send:
            dispatch(background_tasks, send_verify_email, email, token, username)

        return {"success": True, "error_code": "resendSent"}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "resendFailed"}

    finally:
        db.close()
