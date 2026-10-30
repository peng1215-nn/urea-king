from core.time import now_columbus_naive

from database import SessionLocal
from poker.models import Group
from poker.models import InvitationCode
from poker.models import User
from poker.models import UserGroupRole
from poker.services.admin.audit_log import write_audit_log
from core.errors import safe_error
from core.security import verify_user_password



ADMIN_GROUP_CODE = "0"


def group_join_logged_in_service(request, user_id, invite_code):
    """已登录用户用邀请码加入组，不需要重新验证密码。"""
    db = SessionLocal()
    try:
        invite_code = invite_code.strip() if invite_code else ""
        if not invite_code:
            return {"success": False, "message": "groupJoinInviteCodeRequired"}

        user = db.query(User).filter(User.id == user_id).first()
        if not user or int(user.is_active) != 1:
            return {"success": False, "message": "groupJoinAccountDisabled"}

        admin_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user.id,
            UserGroupRole.role == "admin",
        ).first()
        if admin_role:
            return {"success": False, "message": "groupJoinAdminForbidden"}

        # 锁住这条邀请码，并发的两次使用只有一次能通过"未使用"检查
        invitation = db.query(InvitationCode).filter(
            InvitationCode.code == invite_code
        ).with_for_update().first()
        if not invitation:
            return {"success": False, "message": "groupJoinInviteCodeNotFound"}
        if int(invitation.is_used) == 1:
            return {"success": False, "message": "groupJoinInviteCodeUsed"}
        if invitation.group_code == ADMIN_GROUP_CODE:
            return {"success": False, "message": "groupJoinAdminGroupForbidden"}

        # 锁住目标组，避免两个局头邀请码同时使用时产生两个局头
        group = db.query(Group).filter(
            Group.group_code == invitation.group_code
        ).with_for_update().first()
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
                return {"success": False, "message": "groupJoinOrganizerAlreadyExists"}

        user_group_role = UserGroupRole(
            user_id=user.id,
            group_id=group.id,
            role=invitation.role,
        )
        db.add(user_group_role)

        invitation.is_used = 1
        invitation.used_by_username = user.username
        invitation.used_at = now_columbus_naive()

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
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


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

        if not verify_user_password(user, password):
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

        # 锁住这条邀请码，并发的两次使用只有一次能通过"未使用"检查
        invitation = db.query(InvitationCode).filter(
            InvitationCode.code == invite_code
        ).with_for_update().first()

        if not invitation:
            return {"success": False, "message": "groupJoinInviteCodeNotFound"}

        if int(invitation.is_used) == 1:
            return {"success": False, "message": "groupJoinInviteCodeUsed"}

        if invitation.group_code == ADMIN_GROUP_CODE:
            return {"success": False, "message": "groupJoinAdminGroupForbidden"}

        # 锁住目标组，避免两个局头邀请码同时使用时产生两个局头
        group = db.query(Group).filter(
            Group.group_code == invitation.group_code
        ).with_for_update().first()

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
        invitation.used_at = now_columbus_naive()

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
            "message": safe_error(e),
        }

    finally:
        db.close()