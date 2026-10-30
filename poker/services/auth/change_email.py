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
from poker.core.email import dispatch, send_change_email_confirm, send_verify_email
from poker.models import EmailVerification, User
from poker.services.auth.email_owner import email_blocked_by_other

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

        # 新邮箱不能已被别的账号验证过（未验证账号的邮箱不占用；注销超过 24 小时的会被释放）
        blocked = email_blocked_by_other(db, new_email, exclude_user_id=user.id)
        if blocked == "cooldown":
            return {"success": False, "error_code": "changeEmailCooldown"}
        if blocked == "taken":
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

        dispatch(background_tasks, send_verify_email, new_email, token, user.username)

        return {"success": True, "error_code": "changeEmailSuccess"}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "changeEmailFailed"}

    finally:
        db.close()


# ── 已验证账号更换邮箱（个人资料页） ──
#
# 流程：输入当前密码和新邮箱 → 给新邮箱发确认链接 → 点链接确认后新邮箱才生效。
# 确认之前旧邮箱照常使用（找回密码仍发到旧邮箱）；生效后旧邮箱会收到一封通知。

ACCOUNT_EMAIL_TOKEN_TTL_MINUTES = 30
EMAIL_MAX_LENGTH = 254


def get_account_email_service(user_id: int) -> dict:
    """个人资料页显示：当前邮箱，以及正在等待确认的新邮箱。"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or user.is_active == 0:
            return {"success": False, "message": "userNotFound"}

        pending = user.pending_email if user.email_verified else None
        if pending:
            # 确认链接都已过期或作废时，不再显示“等待确认”
            alive = db.query(EmailVerification.id).filter(
                EmailVerification.user_id == user.id,
                EmailVerification.purpose == "change_email",
                EmailVerification.used == 0,
                EmailVerification.expires_at >= now_columbus_naive(),
            ).first()
            if alive is None:
                pending = None

        return {
            "success": True,
            "email": user.email if user.email_verified else "",
            "pending_email": pending or "",
        }
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def request_email_change_service(user_id: int, password: str, new_email: str, background_tasks=None) -> dict:
    """
    返回的 message：
      accountEmailSent 已发送确认邮件 | accountEmailWrongPassword 当前密码不对（路由据此计入失败次数）
      其余为输入或频率问题。
    """
    new_email = (new_email or "").strip().lower()

    if not password:
        return {"success": False, "message": "accountEmailPasswordRequired"}
    if len(new_email) > EMAIL_MAX_LENGTH or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", new_email):
        return {"success": False, "message": "accountEmailInvalid"}

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        if user is None or user.is_active == 0 or user.deleted_at is not None:
            return {"success": False, "message": "userNotFound"}

        if not verify_user_password(user, password):
            return {"success": False, "message": "accountEmailWrongPassword"}

        if not user.email_verified:
            # 能登录的账号都已验证过邮箱；未验证的走注册页的“修改注册邮箱”
            return {"success": False, "message": "accountEmailNotVerified"}

        if new_email == (user.email or "").lower():
            return {"success": False, "message": "accountEmailSame"}

        now = now_columbus_naive()
        recent = db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.purpose == "change_email",
            EmailVerification.created_at >= now - timedelta(minutes=CHANGE_EMAIL_INTERVAL_MINUTES),
        ).order_by(EmailVerification.created_at.desc()).first()
        if recent:
            wait_seconds = int(
                (recent.created_at + timedelta(minutes=CHANGE_EMAIL_INTERVAL_MINUTES) - now).total_seconds()
            )
            return {"success": False, "message": "accountEmailTooFrequent", "retry_after": max(wait_seconds, 1)}

        sent_today = db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.purpose == "change_email",
            EmailVerification.created_at >= now - timedelta(hours=24),
        ).count()
        if sent_today >= CHANGE_EMAIL_MAX_PER_DAY:
            return {"success": False, "message": "accountEmailDailyLimit"}

        blocked = email_blocked_by_other(db, new_email, exclude_user_id=user.id)
        if blocked == "cooldown":
            return {"success": False, "message": "accountEmailCooldown"}
        if blocked == "taken":
            return {"success": False, "message": "accountEmailTaken"}

        # 之前发出的更换邮箱链接作废，只有最新一封有效
        db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.purpose == "change_email",
            EmailVerification.used == 0,
        ).update({"used": 1}, synchronize_session=False)

        user.pending_email = new_email
        token = secrets.token_urlsafe(64)
        db.add(EmailVerification(
            user_id=user.id,
            token=token,
            purpose="change_email",
            expires_at=now + timedelta(minutes=ACCOUNT_EMAIL_TOKEN_TTL_MINUTES),
            used=0,
        ))
        db.commit()

        dispatch(background_tasks, send_change_email_confirm, new_email, token, user.username)
        return {"success": True, "message": "accountEmailSent", "pending_email": new_email}

    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def cancel_email_change_service(user_id: int) -> dict:
    """取消还没确认的更换：确认链接作废，继续用原邮箱。"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        if user is None or user.is_active == 0:
            return {"success": False, "message": "userNotFound"}
        if user.email_verified:
            user.pending_email = None
        db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.purpose == "change_email",
            EmailVerification.used == 0,
        ).update({"used": 1}, synchronize_session=False)
        db.commit()
        return {"success": True, "message": "accountEmailCancelled"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()
