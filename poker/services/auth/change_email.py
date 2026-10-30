"""
修改未验证账号的邮箱并重发验证邮件。

条件：
- 账号存在且 is_active=1
- 邮箱尚未验证（email_verified=0）
- 用户名 + 密码验证通过
- 新邮箱未被其他活跃账号占用
- 频率限制：5 分钟内不能重复操作
"""

import re
import secrets
from datetime import timedelta

from core.errors import safe_error
from core.security import verify_user_password
from core.time import now_columbus_naive
from database import SessionLocal
from poker.core.email import dispatch, send_verify_email
from poker.models import EmailVerification, User

CHANGE_EMAIL_INTERVAL_MINUTES = 5
CHANGE_EMAIL_MAX_PER_DAY = 5
TOKEN_TTL_MINUTES = 15


def change_email_service(username: str, password: str, new_email: str, background_tasks=None) -> dict:
    username = (username or "").strip()
    new_email = (new_email or "").strip().lower()

    if not username:
        return {"success": False, "error_code": "changeEmailUserRequired"}
    if not password:
        return {"success": False, "error_code": "changeEmailPasswordRequired"}

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_pattern, new_email):
        return {"success": False, "error_code": "changeEmailInvalidEmail"}

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not verify_user_password(user, password) or not user or user.is_active == 0:
            return {"success": False, "error_code": "changeEmailWrongCredentials"}

        if user.email_verified:
            # 已验证的账号不走这里（走资料页改邮箱）
            return {"success": False, "error_code": "changeEmailWrongCredentials"}

        # 频率限制：5 分钟内不能重复
        now = now_columbus_naive()
        cutoff_5min = now - timedelta(minutes=CHANGE_EMAIL_INTERVAL_MINUTES)
        recent = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user.id,
                EmailVerification.purpose == "verify_email",
                EmailVerification.created_at >= cutoff_5min,
            )
            .first()
        )
        if recent:
            wait_seconds = int(
                (recent.created_at + timedelta(minutes=CHANGE_EMAIL_INTERVAL_MINUTES) - now)
                .total_seconds()
            )
            return {
                "success": False,
                "error_code": "changeEmailTooFrequent",
                "wait_seconds": wait_seconds,
            }

        # 每天最多发 5 封验证邮件（和"重发验证邮件"一致），防止被用来给任意邮箱发信
        cutoff_24h = now - timedelta(hours=24)
        sent_today = db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.purpose == "verify_email",
            EmailVerification.created_at >= cutoff_24h,
        ).count()
        if sent_today >= CHANGE_EMAIL_MAX_PER_DAY:
            return {"success": False, "error_code": "changeEmailDailyLimit"}

        # 新邮箱不能已被别的账号验证过（未验证账号的邮箱不占用，不会挡住这里）
        if db.query(User.id).filter(User.email == new_email, User.id != user.id).first():
            return {"success": False, "error_code": "changeEmailEmailExists"}

        # 发往旧邮箱的验证链接全部作废，避免换邮箱后用旧链接把新邮箱标记为已验证
        db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.purpose == "verify_email",
            EmailVerification.used == 0,
        ).update({"used": 1}, synchronize_session=False)

        # 更新待验证邮箱（验证成功后才成为正式邮箱）
        user.pending_email = new_email

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

        dispatch(background_tasks, send_verify_email, new_email, token)

        return {"success": True, "error_code": "changeEmailSuccess"}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "changeEmailFailed"}

    finally:
        db.close()
