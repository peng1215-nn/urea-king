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
from poker.core.email import send_verify_email
from poker.models import EmailVerification, User

CHANGE_EMAIL_INTERVAL_MINUTES = 5
TOKEN_TTL_MINUTES = 15


def change_email_service(username: str, password: str, new_email: str) -> dict:
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

        # 新邮箱不能被其他活跃账号占用
        conflict = (
            db.query(User)
            .filter(User.email == new_email, User.id != user.id, User.is_active == 1)
            .first()
        )
        if conflict:
            return {"success": False, "error_code": "changeEmailEmailExists"}

        # 更新邮箱
        user.email = new_email

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

        send_verify_email(new_email, token)

        return {"success": True, "error_code": "changeEmailSuccess"}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "changeEmailFailed"}

    finally:
        db.close()
