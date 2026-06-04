from datetime import datetime
from utils.time import now_columbus_naive

from database import SessionLocal
from models import Group
from models import InvitationCode
from models import UserGroupRole


ADMIN_GROUP_CODE = "0"


def get_group_options_service():
    db = SessionLocal()

    try:
        groups = db.query(Group).filter(
            Group.group_code != ADMIN_GROUP_CODE
        ).order_by(Group.id).all()

        return {
            "success": True,
            "groups": [
                {
                    "id": group.id,
                    "group_code": group.group_code,
                    "group_name": group.group_name,
                }
                for group in groups
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def get_deletable_group_options_service():
    db = SessionLocal()

    try:
        groups = db.query(Group).filter(
            Group.group_code != ADMIN_GROUP_CODE
        ).order_by(Group.id).all()

        return {
            "success": True,
            "groups": [
                {
                    "id": group.id,
                    "group_code": group.group_code,
                    "group_name": group.group_name,
                }
                for group in groups
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def get_unused_invitation_options_service():
    db = SessionLocal()

    try:
        invitations = db.query(
            InvitationCode,
            Group,
        ).join(
            Group,
            InvitationCode.group_code == Group.group_code,
        ).filter(
            InvitationCode.is_used == 0
        ).order_by(
            InvitationCode.id
        ).all()

        return {
            "success": True,
            "invitation_codes": [
                {
                    "id": invitation.id,
                    "code": invitation.code,
                    "group_code": invitation.group_code,
                    "group_name": group.group_name,
                    "role": invitation.role,
                }
                for invitation, group in invitations
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def create_group_service(
    group_code,
    group_name,
):
    db = SessionLocal()

    try:
        group_code = group_code.strip()
        group_name = group_name.strip()

        if not group_code:
            return {
                "success": False,
                "message": "groupCodeRequired",
            }

        if not group_name:
            return {
                "success": False,
                "message": "groupNameRequired",
            }

        existing_group = db.query(Group).filter(
            Group.group_code == group_code
        ).first()

        if existing_group:
            return {
                "success": False,
                "message": "groupCodeExists",
            }

        existing_group_name = db.query(Group).filter(
            Group.group_name == group_name
        ).first()

        if existing_group_name:
            return {
                "success": False,
                "message": "groupNameExists",
            }

        group = Group(
            group_code=group_code,
            group_name=group_name,
            description=None,
            created_at=now_columbus_naive(),
        )

        db.add(group)
        db.commit()
        db.refresh(group)

        return {
            "success": True,
            "message": "groupCreateSuccess",
            "group_id": group.id,
            "group_code": group.group_code,
            "group_name": group.group_name,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def delete_group_service(group_id):
    db = SessionLocal()

    try:
        group = db.query(Group).filter(
            Group.id == group_id
        ).first()

        if not group:
            return {
                "success": False,
                "message": "groupNotFound",
            }

        if group.group_code == ADMIN_GROUP_CODE:
            return {
                "success": False,
                "message": "adminGroupDeleteForbidden",
            }

        member_count = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == group.id
        ).count()

        if member_count > 0:
            return {
                "success": False,
                "message": "groupHasMembers",
            }

        unused_invite_count = db.query(InvitationCode).filter(
            InvitationCode.group_code == group.group_code,
            InvitationCode.is_used == 0,
        ).count()

        if unused_invite_count > 0:
            return {
                "success": False,
                "message": "groupHasUnusedInvites",
            }

        deleted_group_code = group.group_code
        deleted_group_name = group.group_name

        db.delete(group)
        db.commit()

        return {
            "success": True,
            "message": "groupDeleteSuccess",
            "group_code": deleted_group_code,
            "group_name": deleted_group_name,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def create_invitation_code_service(
    code,
    group_id,
    role,
):
    db = SessionLocal()

    try:
        code = code.strip()

        if not code:
            return {
                "success": False,
                "message": "inviteCodeRequired",
            }

        if role not in ["organizer", "user"]:
            return {
                "success": False,
                "message": "inviteRoleInvalid",
            }

        group = db.query(Group).filter(
            Group.id == group_id
        ).first()

        if not group:
            return {
                "success": False,
                "message": "groupNotFound",
            }

        if group.group_code == ADMIN_GROUP_CODE:
            return {
                "success": False,
                "message": "adminGroupInviteForbidden",
            }

        if role == "organizer":
            existing_organizer = db.query(UserGroupRole).filter(
                UserGroupRole.group_id == group.id,
                UserGroupRole.role == "organizer",
            ).first()

            if existing_organizer:
                return {
                    "success": False,
                    "message": "organizerAlreadyExists",
                }

            pending_organizer_invite = db.query(InvitationCode).filter(
                InvitationCode.group_code == group.group_code,
                InvitationCode.role == "organizer",
                InvitationCode.is_used == 0,
            ).first()

            if pending_organizer_invite:
                return {
                    "success": False,
                    "message": "organizerInvitePending",
                }

        existing_code = db.query(InvitationCode).filter(
            InvitationCode.code == code
        ).first()

        if existing_code:
            return {
                "success": False,
                "message": "inviteCodeExists",
            }

        invitation = InvitationCode(
            code=code,
            assigned_to=None,
            group_code=group.group_code,
            role=role,
            is_used=0,
            used_by_username=None,
            created_at=now_columbus_naive(),
            used_at=None,
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return {
            "success": True,
            "message": "inviteCreateSuccess",
            "invite_id": invitation.id,
            "code": invitation.code,
            "group_code": group.group_code,
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


def delete_invitation_code_service(invitation_id):
    db = SessionLocal()

    try:
        invitation = db.query(InvitationCode).filter(
            InvitationCode.id == invitation_id
        ).first()

        if not invitation:
            return {
                "success": False,
                "message": "inviteCodeNotFound",
            }

        if invitation.is_used == 1:
            return {
                "success": False,
                "message": "usedInviteDeleteForbidden",
            }

        deleted_code = invitation.code
        deleted_group_code = invitation.group_code
        deleted_role = invitation.role

        db.delete(invitation)
        db.commit()

        return {
            "success": True,
            "message": "inviteDeleteSuccess",
            "code": deleted_code,
            "group_code": deleted_group_code,
            "role": deleted_role,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()