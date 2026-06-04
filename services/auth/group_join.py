from datetime import datetime
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

ADMIN_GROUP_CODE = "0"


def group_join_service(
    request,
    username,
    password,
    invite_code,
):
    db = SessionLocal()

    try:
        username = username.strip()
        invite_code = invite_code.strip()

        if not username:
            return {"success": False, "message": "groupJoinUsernameRequired"}

        if not password:
            return {"success": False, "message": "groupJoinPasswordRequired"}

        if not invite_code:
            return {"success": False, "message": "groupJoinInviteCodeRequired"}

        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user:
            return {"success": False, "message": "groupJoinAccountInvalid"}

        if not pwd_context.verify(password, user.password_hash):
            return {"success": False, "message": "groupJoinAccountInvalid"}

        if int(user.is_active) != 1:
            return {"success": False, "message": "groupJoinAccountDisabled"}

        admin_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user.id,
            UserGroupRole.role == "admin",
        ).first()

        if admin_role:
            return {
                "success": False,
                "message": "groupJoinAdminForbidden",
            }

        invitation = db.query(InvitationCode).filter(
            InvitationCode.code == invite_code
        ).first()

        if not invitation:
            return {"success": False, "message": "groupJoinInviteCodeNotFound"}

        if int(invitation.is_used) == 1:
            return {"success": False, "message": "groupJoinInviteCodeUsed"}

        if invitation.group_code == ADMIN_GROUP_CODE:
            return {"success": False, "message": "groupJoinAdminGroupForbidden"}

        group = db.query(Group).filter(
            Group.group_code == invitation.group_code
        ).first()

        if not group:
            return {"success": False, "message": "groupJoinTargetGroupNotFound"}

        existing_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user.id,
            UserGroupRole.group_id == group.id,
        ).first()

        if existing_role:
            return {"success": False, "message": "groupJoinAlreadyInGroup"}

        if invitation.role not in ["organizer", "user"]:
            return {"success": False, "message": "groupJoinRoleInvalid"}

        if invitation.role == "organizer":
            existing_organizer = db.query(UserGroupRole).filter(
                UserGroupRole.group_id == group.id,
                UserGroupRole.role == "organizer",
            ).first()

            if existing_organizer:
                return {
                    "success": False,
                    "message": "groupJoinOrganizerAlreadyExists",
                }

        user_group_role = UserGroupRole(
            user_id=user.id,
            group_id=group.id,
            role=invitation.role,
        )

        db.add(user_group_role)

        invitation.is_used = 1
        invitation.used_by_username = user.username
        invitation.used_at = datetime.utcnow()

        db.commit()

        write_audit_log(
            request=request,
            action="GROUP_JOIN",
            target_type="user_group_role",
            target_id=user.id,
            old_value=invite_code,
            new_value=f"group_code={invitation.group_code}, role={invitation.role}",
            operator_id=user.id,
            operator_username=user.username,
        )

        return {
            "success": True,
            "message": "groupJoinSuccess",
            "group_name": group.group_name,
            "role": invitation.role,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()