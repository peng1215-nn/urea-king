"""找回密码：发重置邮件 + 重置密码。"""

import secrets
from datetime import timedelta

from core.errors import safe_error
from core.security import pwd_context
from core.time import now_columbus_naive
from core.validators import check_password
from database import SessionLocal
from poker.core.email import send_reset_password
from poker.models import EmailVerification, User

TOKEN_TTL_MINUTES = 15
RESET_INTERVAL_MINUTES = 5
RESET_MAX_PER_DAY = 5


def forgot_password_service(email: str):
    """
    接收邮箱，查用户，生成 reset token，发邮件。
    无论邮箱是否存在都返回相同提示，防止枚举账号。
    频率限制：5 分钟间隔，每 24 小时最多 5 次。
    """
    email = email.strip().lower()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.email_verified:
            # 静默成功，不暴露账号是否存在
            return {"success": True}

        now = now_columbus_naive()

        # 5 分钟间隔限制
        cutoff_5min = now - timedelta(minutes=RESET_INTERVAL_MINUTES)
        recent = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user.id,
                EmailVerification.purpose == "reset_password",
                EmailVerification.created_at >= cutoff_5min,
            )
            .first()
        )
        if recent:
            wait_seconds = int(
                (recent.created_at + timedelta(minutes=RESET_INTERVAL_MINUTES) - now)
                .total_seconds()
            )
            return {
                "success": False,
                "error_code": "resetTooFrequent",
                "wait_seconds": max(wait_seconds, 1),
            }

        # 24 小时内次数限制
        cutoff_24h = now - timedelta(hours=24)
        count_today = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user.id,
                EmailVerification.purpose == "reset_password",
                EmailVerification.created_at >= cutoff_24h,
            )
            .count()
        )
        if count_today >= RESET_MAX_PER_DAY:
            return {"success": False, "error_code": "resetDailyLimit"}

        token = secrets.token_urlsafe(64)
        record = EmailVerification(
            user_id=user.id,
            token=token,
            purpose="reset_password",
            expires_at=now + timedelta(minutes=TOKEN_TTL_MINUTES),
            used=0,
        )
        db.add(record)
        db.commit()

        send_reset_password(email, token)
        return {"success": True}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": True}  # 同样不暴露错误细节

    finally:
        db.close()


def reset_password_service(token: str, new_password: str, confirm_password: str):
    """用 token 重置密码。"""
    if new_password != confirm_password:
        return {"success": False, "error_code": "resetPasswordMismatch"}

    password_error = check_password(new_password)
    if password_error:
        return {
            "success": False,
            "error_code": (
                "resetPasswordTooShort"
                if password_error == "too_short"
                else "resetPasswordTooLong"
            ),
        }

    db = SessionLocal()
    try:
        record = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.token == token,
                EmailVerification.purpose == "reset_password",
            )
            .first()
        )

        if not record:
            return {"success": False, "error_code": "resetTokenInvalid"}

        if record.used:
            return {"success": False, "error_code": "resetTokenUsed"}

        if record.expires_at < now_columbus_naive():
            return {"success": False, "error_code": "resetTokenExpired"}

        user = db.query(User).filter(User.id == record.user_id).first()
        if not user:
            return {"success": False, "error_code": "resetTokenInvalid"}

        user.password_hash = pwd_context.hash(new_password)
        record.used = 1
        db.commit()
        return {"success": True}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "resetFailed"}

    finally:
        db.close()
