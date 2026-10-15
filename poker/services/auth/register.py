"""
Registration service for Poker module.
Flow: validate inputs → create PlatformUser → join group via invite code
"""
import re

from database import SessionLocal
from core.models import PlatformUser
from core.utils.security import hash_password
from poker.services.admin.audit_log import write_audit_log
from poker.services.auth.group_join import poker_group_join_service


def register_user_service(
    request,
    username: str,
    nickname: str,
    password: str,
    confirm_password: str,
    invite_code: str,
):
    username = username.strip()
    nickname = nickname.strip()
    invite_code = invite_code.strip().upper()

    username_pattern = r"^[A-Za-z][A-Za-z0-9_]{4,}$"
    if not re.match(username_pattern, username):
        return {"success": False, "error_code": "registerUsernameInvalid"}

    if not nickname:
        return {"success": False, "error_code": "registerNicknameRequired"}

    if len(password) < 6:
        return {"success": False, "error_code": "registerPasswordTooShort"}

    if password != confirm_password:
        return {"success": False, "error_code": "registerPasswordMismatch"}

    if not invite_code:
        return {"success": False, "error_code": "groupJoinInviteCodeRequired"}

    db = SessionLocal()
    try:
        existing = db.query(PlatformUser).filter(PlatformUser.username == username).first()
        if existing:
            return {"success": False, "error_code": "registerUsernameExists"}

        new_user = PlatformUser(
            username=username,
            nickname=nickname,
            password_hash=hash_password(password),
            avatar_url="/static/images/default_avatar.jpg",
            is_active=1,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Now join the group via invite code
        join_result = poker_group_join_service(
            user_id=new_user.id,
            username=new_user.username,
            invite_code=invite_code,
        )

        if not join_result.get("success"):
            # Rollback: delete the user we just created so registration is atomic
            db.delete(new_user)
            db.commit()
            return {"success": False, "error_code": join_result.get("error_code", "groupJoinFailed")}

        write_audit_log(
            request=request,
            action="REGISTER_SUCCESS",
            target_type="user",
            target_id=new_user.id,
            old_value=None,
            new_value="registered",
            operator_id=new_user.id,
            operator_username=new_user.username,
        )

        return {"success": True, "error_code": "registerSuccess", "nickname": nickname}

    except Exception as e:
        db.rollback()
        return {"success": False, "error_code": "registerFailed", "message": str(e)}
    finally:
        db.close()
