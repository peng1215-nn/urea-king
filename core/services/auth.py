"""Platform authentication services — register, login, verify token."""
import re
from database import SessionLocal
from core.models import PlatformUser
from core.utils.security import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
)
from jose import JWTError


def register_service(username: str, nickname: str, password: str, confirm_password: str) -> dict:
    username = username.strip()
    nickname = nickname.strip()

    if not re.match(r"^[A-Za-z][A-Za-z0-9_]{4,}$", username):
        return {"success": False, "error_code": "registerUsernameInvalid"}

    if not nickname:
        return {"success": False, "error_code": "registerNicknameRequired"}

    if len(password) < 6:
        return {"success": False, "error_code": "registerPasswordTooShort"}

    if password != confirm_password:
        return {"success": False, "error_code": "registerPasswordMismatch"}

    db = SessionLocal()
    try:
        if db.query(PlatformUser).filter(PlatformUser.username == username).first():
            return {"success": False, "error_code": "registerUsernameExists"}

        user = PlatformUser(
            username=username,
            nickname=nickname,
            password_hash=hash_password(password),
            avatar_url="/static/images/default_avatar.jpg",
            is_active=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
        }

    except Exception as e:
        db.rollback()
        print(f"[platform] register error: {e}")
        return {"success": False, "error_code": "registerFailed"}

    finally:
        db.close()


def login_service(username: str, password: str) -> dict:
    username = username.strip()
    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.username == username).first()

        if not user:
            return {"success": False, "error_code": "loginUserNotFound"}

        if not verify_password(password, user.password_hash):
            return {"success": False, "error_code": "loginPasswordIncorrect"}

        if user.is_active != 1:
            return {"success": False, "error_code": "loginAccountDisabled"}

        token = create_token(user.id, user.username)

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
        }

    except Exception as e:
        print(f"[platform] login error: {e}")
        return {"success": False, "error_code": "loginFailed"}

    finally:
        db.close()


def verify_token_service(token: str) -> dict:
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        username = payload["username"]
    except (JWTError, KeyError, ValueError):
        return {"success": False, "error_code": "tokenInvalid"}

    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
        if not user or user.is_active != 1:
            return {"success": False, "error_code": "tokenUserInvalid"}

        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
        }

    finally:
        db.close()


def get_user_service(user_id: int) -> dict:
    db = SessionLocal()
    try:
        user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
        if not user:
            return {"success": False, "error_code": "userNotFound"}

        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
        }

    finally:
        db.close()
