from fastapi import APIRouter, Form
from passlib.context import CryptContext

from database import SessionLocal
from models import User

router = APIRouter()

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


@router.post("/login")
def login_user(
    role: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return {"success": False, "message": "用户不存在。"}

        if not pwd_context.verify(password, user.password_hash):
            return {"success": False, "message": "密码错误。"}

        if user.role != role:
            return {"success": False, "message": "身份权限选择错误。"}

        return {
            "success": True,
            "message": f"欢迎回来，{user.nickname or user.username}。",
            "username": user.username,
            "nickname": user.nickname or user.username,
            "role": user.role
        }

    finally:
        db.close()