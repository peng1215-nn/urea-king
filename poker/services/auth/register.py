import re
import secrets
from datetime import timedelta

from core.time import now_columbus_naive

DELETE_COOLDOWN_HOURS = 24
from core.validators import check_name, check_password
from core.errors import safe_error
from core.security import pwd_context
from database import SessionLocal
from poker.core.validators import NICKNAME_MAX
from poker.core.email import send_verify_email
from poker.models import EmailVerification, User
from core.models import UserModule
from poker.services.admin.audit_log import write_audit_log

TOKEN_TTL_MINUTES = 15


def register_user_service(
    request,
    username,
    nickname,
    email,
    password,
    confirm_password,
):
    username = username.strip()
    nickname = nickname.strip()
    email = email.strip().lower()

    username_pattern = r"^[A-Za-z][A-Za-z0-9_]{4,}$"
    if not re.match(username_pattern, username):
        return {"success": False, "error_code": "registerUsernameInvalid"}

    if not nickname:
        return {"success": False, "error_code": "registerNicknameRequired"}

    nickname, nickname_error = check_name(nickname, NICKNAME_MAX)
    if nickname_error:
        return {
            "success": False,
            "error_code": (
                "registerNicknameTooLong"
                if nickname_error == "too_long"
                else "registerNicknameInvalid"
            ),
        }

    # 简单邮箱格式校验
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_pattern, email):
        return {"success": False, "error_code": "registerEmailInvalid"}

    password_error = check_password(password)
    if password_error:
        return {
            "success": False,
            "error_code": {
                "too_short": "registerPasswordTooShort",
                "too_long": "registerPasswordTooLong",
                "too_weak": "registerPasswordTooWeak",
            }[password_error],
        }

    if password != confirm_password:
        return {"success": False, "error_code": "registerPasswordMismatch"}

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            return {"success": False, "error_code": "registerUsernameExists"}

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            # 邮箱存在：区分"注销冷却中"和"真正被占用"
            if existing.is_active == 0 and existing.deleted_at is not None:
                cooldown_cutoff = now_columbus_naive() - timedelta(hours=DELETE_COOLDOWN_HOURS)
                if existing.deleted_at > cooldown_cutoff:
                    # 注销不足 24 小时，禁止重新注册
                    return {"success": False, "error_code": "registerEmailCooldown"}
                # 超过 24 小时：允许重新注册，清空旧记录的邮箱让本次注册通过唯一约束
                existing.email = f"deleted#{existing.id}@deleted"
                db.flush()
            else:
                return {"success": False, "error_code": "registerEmailExists"}

        new_user = User(
            username=username,
            nickname=nickname,
            email=email,
            email_verified=0,
            password_hash=pwd_context.hash(password),
            avatar_url="/static/images/default_avatar.jpg",
            is_active=1,
        )
        db.add(new_user)
        db.flush()  # 拿到 new_user.id

        token = secrets.token_urlsafe(64)
        verification = EmailVerification(
            user_id=new_user.id,
            token=token,
            purpose="verify_email",
            expires_at=now_columbus_naive() + timedelta(minutes=TOKEN_TTL_MINUTES),
            used=0,
        )
        db.add(verification)
        db.commit()

        # 发验证邮件（发送失败不回滚，账号已创建，用户可以重新请求）
        send_verify_email(email, token)

        write_audit_log(
            request=request,
            action="REGISTER_SUCCESS",
            target_type="user",
            target_id=new_user.id,
            old_value=None,
            new_value=f"email={email}",
            operator_id=new_user.id,
            operator_username=new_user.username,
        )

        return {"success": True, "error_code": "registerSuccess", "nickname": nickname}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "registerFailed"}

    finally:
        db.close()


def verify_email_service(token: str):
    """点击邮件链接后调用，验证 token 并标记邮箱已验证。"""
    db = SessionLocal()
    try:
        record = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.token == token,
                EmailVerification.purpose == "verify_email",
            )
            .with_for_update()
            .first()
        )

        if not record:
            return {"success": False, "error_code": "verifyTokenInvalid"}

        if record.used:
            return {"success": False, "error_code": "verifyTokenUsed"}

        if record.expires_at < now_columbus_naive():
            return {"success": False, "error_code": "verifyTokenExpired"}

        record.used = 1
        user = db.query(User).filter(User.id == record.user_id).first()
        if user:
            user.email_verified = 1

            # 首次完成邮箱验证 → 记录用户加入 poker 模块
            already = db.query(UserModule).filter(
                UserModule.user_id == user.id,
                UserModule.module == "poker",
            ).first()
            if not already:
                db.add(UserModule(user_id=user.id, module="poker"))

        db.commit()
        return {"success": True}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "verifyFailed"}

    finally:
        db.close()
