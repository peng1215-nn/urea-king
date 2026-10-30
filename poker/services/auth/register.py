import re
import secrets

from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from core.time import now_columbus_naive

from core.validators import check_name, check_password
from poker.services.common.nicknames import nickname_taken
from poker.services.auth.email_owner import email_blocked_by_other
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

        if nickname_taken(db, nickname):
            return {"success": False, "error_code": "registerNicknameExists"}

        # 只有已验证的账号才占用邮箱；未验证账号的邮箱在 pending_email 里，不会挡住这里
        blocked = email_blocked_by_other(db, email)
        if blocked == "cooldown":
            return {"success": False, "error_code": "registerEmailCooldown"}
        if blocked == "taken":
            return {"success": False, "error_code": "registerEmailExists"}

        # 邮箱先放在"待验证"里，不占用：别人用你的邮箱抢注也占不住，谁先完成验证归谁
        new_user = User(
            username=username,
            nickname=nickname,
            email=None,
            pending_email=email,
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
        send_verify_email(email, token, username)

        write_audit_log(
            request=request,
            action="REGISTER_SUCCESS",
            target_type="user",
            target_id=new_user.id,
            old_value=None,
            new_value=f"email={email}",
            operator_id=new_user.id,
            operator_username=new_user.username,
            db=db,
        )

        return {"success": True, "error_code": "registerSuccess", "nickname": nickname}

    except IntegrityError as e:
        # 两个人同一瞬间注册同一个用户名或昵称：由数据库的唯一约束兜底
        db.rollback()
        if "nickname" in str(getattr(e, "orig", e)):
            return {"success": False, "error_code": "registerNicknameExists"}
        return {"success": False, "error_code": "registerUsernameExists"}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "registerFailed"}

    finally:
        db.close()


def verify_target_service(token: str):
    """验证确认页显示"即将验证哪个账号的哪个邮箱"，防止被骗点了别人账号的验证链接。"""
    from poker.core.email import mask_email

    db = SessionLocal()
    try:
        record = db.query(EmailVerification).filter(
            EmailVerification.token == token,
            EmailVerification.purpose == "verify_email",
        ).first() if token else None
        if record is None:
            return {"error_code": "verifyTokenInvalid"}
        if record.used:
            return {"error_code": "verifyTokenUsed"}
        if record.expires_at < now_columbus_naive():
            return {"error_code": "verifyTokenExpired"}
        user = db.query(User).filter(User.id == record.user_id).first()
        if user is None or not user.pending_email:
            return {"error_code": "verifyTokenInvalid"}
        return {"username": user.username, "email": mask_email(user.pending_email)}
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

        user = db.query(User).filter(User.id == record.user_id).with_for_update().first()
        if user is None or user.is_active == 0:
            return {"success": False, "error_code": "verifyTokenInvalid"}

        if not user.email_verified:
            target = user.pending_email
            if not target:
                return {"success": False, "error_code": "verifyTokenInvalid"}

            # 按编号顺序锁住所有和这个邮箱有关的账号：两个账号同时验证同一个邮箱时排队执行，
            # 后执行的那个会看到邮箱已被验证，而不是互相等待或撞上唯一约束
            db.query(User.id).filter(
                (User.pending_email == target) | (User.email == target)
            ).order_by(User.id).with_for_update().all()

            # 这个邮箱已经被别的账号验证过了：谁先验证归谁（注销超过 24 小时的会被释放）
            if email_blocked_by_other(db, target, exclude_user_id=user.id):
                record.used = 1
                db.commit()
                return {"success": False, "error_code": "verifyEmailTaken"}

            user.email = target
            user.pending_email = None
            user.email_verified = 1

            # 其他还在等验证同一个邮箱的账号（如抢注的）不再能验证它
            others = db.query(User).filter(
                User.pending_email == target,
                User.id != user.id,
                User.email_verified == 0,
            ).all()
            for other in others:
                other.pending_email = None
                db.query(EmailVerification).filter(
                    EmailVerification.user_id == other.id,
                    EmailVerification.purpose == "verify_email",
                    EmailVerification.used == 0,
                ).update({"used": 1}, synchronize_session=False)

        record.used = 1
        if user:
            # 首次完成邮箱验证 → 记录用户加入 poker 模块
            already = db.query(UserModule).filter(
                UserModule.user_id == user.id,
                UserModule.module == "poker",
            ).first()
            if not already:
                db.add(UserModule(user_id=user.id, module="poker"))

        db.commit()
        return {"success": True}

    except IntegrityError:
        # 极少数情况下仍撞上邮箱唯一约束：说明邮箱刚被别的账号验证
        db.rollback()
        return {"success": False, "error_code": "verifyEmailTaken"}

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "verifyFailed"}

    finally:
        db.close()
