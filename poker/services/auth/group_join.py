"""Poker group join service.
Called after platform registration to validate invite code and assign user to group.
"""
from utils.time import now_columbus_naive
from database import SessionLocal
from poker.models import PokerGroup, PokerInvitationCode, PokerUserGroupRole


def poker_group_join_service(user_id: int, username: str, invite_code: str) -> dict:
    """
    Validate invite code and add user to a poker group.

    Args:
        user_id: Platform user ID (from platform_users)
        username: Platform username (for audit/display)
        invite_code: e.g. POKER-G001-A3K9
    """
    invite_code = invite_code.strip().upper()

    if not invite_code:
        return {"success": False, "error_code": "groupJoinInviteCodeRequired"}

    db = SessionLocal()
    try:
        invitation = db.query(PokerInvitationCode).filter(
            PokerInvitationCode.code == invite_code
        ).first()

        if not invitation:
            return {"success": False, "error_code": "groupJoinInviteCodeNotFound"}

        if int(invitation.is_used) == 1:
            return {"success": False, "error_code": "groupJoinInviteCodeUsed"}

        group = db.query(PokerGroup).filter(
            PokerGroup.id == invitation.group_id
        ).first()

        if not group:
            return {"success": False, "error_code": "groupJoinTargetGroupNotFound"}

        # Check if user already in this group
        existing_role = db.query(PokerUserGroupRole).filter(
            PokerUserGroupRole.user_id == user_id,
            PokerUserGroupRole.group_id == group.id,
        ).first()

        if existing_role:
            return {"success": False, "error_code": "groupJoinAlreadyInGroup"}

        if invitation.role not in ["organizer", "user"]:
            return {"success": False, "error_code": "groupJoinRoleInvalid"}

        if invitation.role == "organizer":
            existing_organizer = db.query(PokerUserGroupRole).filter(
                PokerUserGroupRole.group_id == group.id,
                PokerUserGroupRole.role == "organizer",
            ).first()
            if existing_organizer:
                return {"success": False, "error_code": "groupJoinOrganizerAlreadyExists"}

        # Assign role
        user_group_role = PokerUserGroupRole(
            user_id=user_id,
            group_id=group.id,
            role=invitation.role,
        )
        db.add(user_group_role)

        # Mark code as used
        invitation.is_used = 1
        invitation.used_by_user_id = user_id
        invitation.used_by_username = username
        invitation.used_at = now_columbus_naive()

        db.commit()

        return {
            "success": True,
            "error_code": "groupJoinSuccess",
            "group_id": group.id,
            "group_code": group.group_code,
            "group_name": group.group_name,
            "role": invitation.role,
        }

    except Exception as e:
        db.rollback()
        print(f"[poker] group_join error: {e}")
        return {"success": False, "error_code": "groupJoinFailed"}

    finally:
        db.close()
