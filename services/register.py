from datetime import datetime
import re
from passlib.context import CryptContext
from database import SessionLocal
from models import User, InvitationCode


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def register_user_service(
    username,
    nickname,
    password,
    confirm_password,
    invite_code
):
    username = username.strip()
    nickname = nickname.strip()
    invite_code = invite_code.strip()

    username_pattern = r"^[A-Za-z][A-Za-z0-9_]{4,}$"

    if not re.match(username_pattern, username):
        return {
            "success": False,
            "message": "用户名必须以字母开头，且至少 5 位。"
        }

    if len(nickname) == 0:
        return {
            "success": False,
            "message": "昵称不能为空。"
        }

    if len(password) < 6:
        return {
            "success": False,
            "message": "密码长度至少为 6 位。"
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
                "message": "用户名已存在。"
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

        if invitation.role != "admin" and not invitation.group_id:
            return {
                "success": False,
                "message": "该邀请码未绑定组别，无法注册。"
            }

        hashed_password = pwd_context.hash(password)

        if invitation.role == "admin":
            user_group_id = None
        else:
            user_group_id = invitation.group_id

        new_user = User(
            username=username,
            nickname=nickname,
            password_hash=hashed_password,
            role=invitation.role,
            group_id=user_group_id,
            invitation_code=invite_code,
            avatar_url = "/static/images/default_avatar.jpg"
        )

        db.add(new_user)

        invitation.is_used = 1
        invitation.used_by_username = username
        invitation.used_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "message": f"注册成功，欢迎 {nickname}。"
        }

    except Exception as e:
        print(e)

        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()