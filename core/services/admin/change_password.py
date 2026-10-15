from passlib.context import CryptContext
from database import SessionLocal
from core.models import PlatformUser

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_current_account_service(user_id):
    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
        if not user:
            return {"success": False, "message": "userNotFound"}
        return {"success": True, "user": {"id": user.id, "username": user.username, "nickname": user.nickname}}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def update_nickname_service(user_id, nickname):
    db = SessionLocal()
    try:
        nickname = nickname.strip()
        if not nickname:
            return {"success": False, "message": "nicknameRequired"}
        if len(nickname) > 50:
            return {"success": False, "message": "nicknameTooLong"}

        user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
        if not user:
            return {"success": False, "message": "userNotFound"}
        if user.nickname == nickname:
            return {"success": False, "message": "nicknameNoChange"}

        if db.query(PlatformUser).filter(PlatformUser.nickname == nickname, PlatformUser.id != user_id).first():
            return {"success": False, "message": "nicknameExists"}

        user.nickname = nickname
        db.commit()
        return {"success": True, "message": "nicknameUpdateSuccess", "nickname": nickname}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def update_password_service(user_id, current_password, new_password, confirm_password):
    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
        if not user:
            return {"success": False, "message": "userNotFound"}
        if not pwd_context.verify(current_password, user.password_hash):
            return {"success": False, "message": "currentPasswordIncorrect"}
        if len(new_password) < 6:
            return {"success": False, "message": "newPasswordTooShort"}
        if current_password == new_password:
            return {"success": False, "message": "passwordNoChange"}
        if new_password != confirm_password:
            return {"success": False, "message": "newPasswordMismatch"}

        user.password_hash = pwd_context.hash(new_password)
        db.commit()
        return {"success": True, "message": "passwordUpdateSuccessLogout"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
