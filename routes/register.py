import re
from datetime import datetime
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from database import SessionLocal
from models import User, InvitationCode


router = APIRouter()

templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


@router.get("/login", response_class=HTMLResponse)
def back_to_login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@router.post("/register")
def register_user(
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    invite_code: str = Form(...)
):
    username_pattern = r"^[A-Za-z][A-Za-z0-9_]{4,}$"

    if not re.match(username_pattern, username):
        return {
            "success": False,
            "message": "用户名必须以字母开头，且至少 5 位，只能包含字母、数字和下划线。"
        }

    if len(password) < 6:
        return {
            "success": False,
            "message": "密码长度必须大于等于 6 位。"
        }

    if password != confirm_password:
        return {
            "success": False,
            "message": "两次输入的密码不一致。"
        }

    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.username == username
        ).first()

        if existing_user:
            return {
                "success": False,
                "message": "用户名已存在，请更换用户名。"
            }

        invitation = db.query(InvitationCode).filter(
            InvitationCode.code == invite_code
        ).first()

        if not invitation:
            return {
                "success": False,
                "message": "邀请码不存在。"
            }

        if invitation.is_used == 1:
            return {
                "success": False,
                "message": "邀请码已被使用。"
            }

        new_user = User(
            username=username,
            password_hash=pwd_context.hash(password),
            role=invitation.role,
            points=0,
            invitation_code=invite_code
        )

        db.add(new_user)

        invitation.is_used = 1
        invitation.used_by_username = username
        invitation.used_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "message": f"注册成功，身份权限：{invitation.role}"
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"注册失败：{str(e)}"
        }

    finally:
        db.close()