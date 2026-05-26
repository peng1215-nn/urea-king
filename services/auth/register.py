from datetime import datetime
import re
from passlib.context import CryptContext
from database import SessionLocal
from models import Group
from models import InvitationCode
from models import User
from models import UserGroupRole
from services.admin.audit_log import write_audit_log


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def register_user_service(
    request,
    username,
    nickname,
    password,
    confirm_password,
    invite_code,
):
    username = username.strip()
    nickname = nickname.strip()
    invite_code = invite_code.strip()

    username_pattern = r"^[A-Za-z][A-Za-z0-9_]{4,}$"

    if not re.match(username_pattern, username):
        return {
            "success": False,
            "error_code": "registerUsernameInvalid",
        }

    if not nickname:
        return {
            "success": False,
            "error_code": "registerNicknameRequired",
        }

    if len(password) < 6:
        return {
            "success": False,
            "error_code": "registerPasswordTooShort",
        }

    if password != confirm_password:
        return {
            "success": False,
            "error_code": "registerPasswordMismatch",
        }

    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.username == username
        ).first()

        if existing_user:
            return {
                "success": False,
                "error_code": "registerUsernameExists",
            }

        invitation = db.query(InvitationCode).filter(
            InvitationCode.code == invite_code
        ).first()

        if not invitation:
            return {
                "success": False,
                "error_code": "registerInviteCodeNotFound",
            }

        if invitation.is_used == 1:
            return {
                "success": False,
                "error_code": "registerInviteCodeUsed",
            }

        group = db.query(Group).filter(
            Group.group_code == invitation.group_code
        ).first()

        if not group:
            return {
                "success": False,
                "error_code": "registerInviteCodeGroupNotFound",
            }

        new_user = User(
            username=username,
            nickname=nickname,
            password_hash=pwd_context.hash(password),
            invitation_code=invite_code,
            avatar_url="/static/images/default_avatar.jpg",
            is_active=1,
        )

        db.add(new_user)
        db.flush()

        user_group_role = UserGroupRole(
            user_id=new_user.id,
            group_id=group.id,
            role=invitation.role,
        )

        db.add(user_group_role)

        invitation.is_used = 1
        invitation.used_by_username = username
        invitation.used_at = datetime.utcnow()

        db.commit()

        write_audit_log(
            request=request,
            action="REGISTER_SUCCESS",
            target_type="user",
            target_id=new_user.id,
            old_value=invite_code,
            new_value=(
                f"group_code={invitation.group_code}, "
                f"role={invitation.role}"
            ),
            operator_id=new_user.id,
            operator_username=new_user.username,
        )

        return {
            "success": True,
            "error_code": "registerSuccess",
            "nickname": nickname,
        }

    except Exception as e:
        print(e)

        db.rollback()

        return {
            "success": False,
            "error_code": "registerFailed",
        }

    finally:
        db.close()