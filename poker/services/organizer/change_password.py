from passlib.context import CryptContext

from database import SessionLocal
from poker.models import User
from poker.core.validators import NICKNAME_MAX, check_name, check_password
from poker.core.errors import safe_error


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


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

        if not pwd_context.verify(current_password, user.password_hash):
            return {"success": False, "message": "currentPasswordIncorrect"}

        password_error = check_password(new_password)

        if password_error:
            return {
                "success": False,
                "message": "newPasswordTooShort" if password_error == "too_short" else "newPasswordTooLong",
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

def get_group_info_service(group_id: int):
    from poker.models import Group
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return {"success": False, "message": "组别不存在。"}
        return {"success": True, "group_name": group.group_name or ""}
    finally:
        db.close()


def update_group_name_service(group_id: int, group_name: str):
    from poker.models import Group
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return {"success": False, "message": "组别不存在。"}
        group_name = group_name.strip()
        if not group_name:
            return {"success": False, "message": "组名不能为空。"}
        if len(group_name) > 50:
            return {"success": False, "message": "组名不能超过50个字符。"}
        group.group_name = group_name
        db.commit()
        return {"success": True, "message": "组名修改成功。"}
    finally:
        db.close()
