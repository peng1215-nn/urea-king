from datetime import datetime
import re

from passlib.context import CryptContext

from database import SessionLocal
from models import InvitationCode, User


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def register_user_service(username, nickname, password, confirm_password, invite_code):
    username = username.strip()
    nickname = nickname.strip()
    invite_code = invite_code.strip()

    username_pattern = r"^[A-Za-z][A-Za-z0-9_]{4,}$"

    if not re.match(username_pattern, username):
        return {"success": False, "error_code": "registerUsernameInvalid"}

    if not nickname:
        return {"success": False, "error_code": "registerNicknameRequired"}

    if len(password) < 6:
        return {"success": False, "error_code": "registerPasswordTooShort"}

    if password != confirm_password:
        return {"success": False, "error_code": "registerPasswordMismatch"}

    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.username == username).first()

        if existing_user:
            return {"success": False, "error_code": "registerUsernameExists"}

        invitation = db.query(InvitationCode).filter(
            InvitationCode.code == invite_code
        ).first()

        if not invitation:
            return {"success": False, "error_code": "registerInviteCodeNotFound"}

        if invitation.is_used == 1:
            return {"success": False, "error_code": "registerInviteCodeUsed"}

        if invitation.role != "admin" and not invitation.group_id:
            return {"success": False, "error_code": "registerInviteCodeNoGroup"}

        new_user = User(
            username=username,
            nickname=nickname,
            password_hash=pwd_context.hash(password),
            role=invitation.role,
            group_id=None if invitation.role == "admin" else invitation.group_id,
            invitation_code=invite_code,
            avatar_url="/static/images/default_avatar.jpg",
        )

        db.add(new_user)

        invitation.is_used = 1
        invitation.used_by_username = username
        invitation.used_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "error_code": "registerSuccess",
            "nickname": nickname,
        }

    except Exception as e:
        print(e)
        db.rollback()
        return {"success": False, "error_code": "registerFailed"}

    finally:
        db.close()