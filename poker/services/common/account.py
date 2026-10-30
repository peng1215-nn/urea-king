"""
当前账号的资料：查看、改昵称、改密码。管理员、局头、普通用户共用。
"""


from database import SessionLocal
from poker.models import User
from core.validators import check_name, check_password
from poker.core.rate_limit import current_password_failures_by_user
from poker.core.validators import NICKNAME_MAX
from core.errors import safe_error
from core.security import pwd_context




def get_current_account_service(user_id):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "userNotFound"}

        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
            },
        }

    except Exception as e:
        return {"success": False, "message": safe_error(e)}

    finally:
        db.close()


def update_nickname_service(user_id, nickname):
    db = SessionLocal()

    try:
        nickname = nickname.strip()

        if not nickname:
            return {"success": False, "message": "nicknameRequired"}

        nickname, nickname_error = check_name(nickname, NICKNAME_MAX)

        if nickname_error:
            return {
                "success": False,
                "message": "nicknameTooLong" if nickname_error == "too_long" else "nicknameInvalid",
            }

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "userNotFound"}

        if user.nickname == nickname:
            return {"success": False, "message": "nicknameNoChange"}

        existing = db.query(User).filter(
            User.nickname == nickname,
            User.id != user_id,
        ).first()

        if existing:
            return {"success": False, "message": "nicknameExists"}

        user.nickname = nickname
        db.commit()

        return {
            "success": True,
            "message": "nicknameUpdateSuccess",
            "nickname": nickname,
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}

    finally:
        db.close()


def update_password_service(
    user_id,
    current_password,
    new_password,
    confirm_password,
):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "userNotFound"}

        # 限制输错当前密码的次数，防止拿到登录状态的人借此猜出密码
        limiter_key = str(user.id)
        wait = current_password_failures_by_user.retry_after(limiter_key)
        if wait:
            return {"success": False, "message": "currentPasswordTooManyAttempts", "retry_after": wait}

        if not pwd_context.verify(current_password, user.password_hash):
            current_password_failures_by_user.hit(limiter_key)
            return {"success": False, "message": "currentPasswordIncorrect"}

        password_error = check_password(new_password)

        if password_error:
            return {
                "success": False,
                "message": {
                    "too_short": "newPasswordTooShort",
                    "too_long": "newPasswordTooLong",
                    "too_weak": "newPasswordTooWeak",
                }[password_error],
            }

        if current_password == new_password:
            return {"success": False, "message": "passwordNoChange"}

        if new_password != confirm_password:
            return {"success": False, "message": "newPasswordMismatch"}

        user.password_hash = pwd_context.hash(new_password)
        db.commit()

        return {"success": True, "message": "passwordUpdateSuccessLogout"}

    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}

    finally:
        db.close()
