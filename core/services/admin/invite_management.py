from utils.time import now_columbus_naive
from database import SessionLocal
from poker.models import (
    PokerGroup,
    PokerInvitationCode,
    PokerUserGroupRole,
    PokerGame,
    PokerGamePlayer,
    PokerChipRequest,
)
from poker.utils.invite import generate_invite_code


def get_group_options_service():
    db = SessionLocal()
    try:
        groups = db.query(PokerGroup).order_by(PokerGroup.id).all()
        return {
            "success": True,
            "groups": [
                {"id": g.id, "group_code": g.group_code, "group_name": g.group_name}
                for g in groups
            ],
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def get_deletable_group_options_service():
    return get_group_options_service()


def get_unused_invitation_options_service():
    db = SessionLocal()
    try:
        invitations = (
            db.query(PokerInvitationCode, PokerGroup)
            .join(PokerGroup, PokerInvitationCode.group_id == PokerGroup.id)
            .filter(PokerInvitationCode.is_used == 0)
            .order_by(PokerInvitationCode.id)
            .all()
        )
        return {
            "success": True,
            "invitation_codes": [
                {
                    "id": inv.id,
                    "code": inv.code,
                    "group_id": inv.group_id,
                    "group_name": group.group_name,
                    "role": inv.role,
                }
                for inv, group in invitations
            ],
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def create_group_service(group_code, group_name):
    db = SessionLocal()
    try:
        group_code = group_code.strip()
        group_name = group_name.strip()

        if not group_code:
            return {"success": False, "message": "groupCodeRequired"}
        if not group_name:
            return {"success": False, "message": "groupNameRequired"}

        if db.query(PokerGroup).filter(PokerGroup.group_code == group_code).first():
            return {"success": False, "message": "groupCodeExists"}

        if db.query(PokerGroup).filter(PokerGroup.group_name == group_name).first():
            return {"success": False, "message": "groupNameExists"}

        group = PokerGroup(
            group_code=group_code,
            group_name=group_name,
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
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def delete_group_service(group_id):
    db = SessionLocal()
    try:
        group = db.query(PokerGroup).filter(PokerGroup.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        member_count = db.query(PokerUserGroupRole).filter(
            PokerUserGroupRole.group_id == group.id
        ).count()
        if member_count > 0:
            return {"success": False, "message": "groupHasMembers"}

        unused_invite_count = db.query(PokerInvitationCode).filter(
            PokerInvitationCode.group_id == group.id,
            PokerInvitationCode.is_used == 0,
        ).count()
        if unused_invite_count > 0:
            return {"success": False, "message": "groupHasUnusedInvites"}

        code, name = group.group_code, group.group_name
        db.delete(group)
        db.commit()
        return {
            "success": True,
            "message": "groupDeleteSuccess",
            "group_code": code,
            "group_name": name,
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def create_invitation_code_service(group_id, role):
    """Generate a new POKER-G{id}-XXXX invite code for a group."""
    db = SessionLocal()
    try:
        if role not in ["organizer", "user"]:
            return {"success": False, "message": "inviteRoleInvalid"}

        group = db.query(PokerGroup).filter(PokerGroup.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}

        if role == "organizer":
            existing_organizer = db.query(PokerUserGroupRole).filter(
                PokerUserGroupRole.group_id == group.id,
                PokerUserGroupRole.role == "organizer",
            ).first()
            if existing_organizer:
                return {"success": False, "message": "organizerAlreadyExists"}

            pending = db.query(PokerInvitationCode).filter(
                PokerInvitationCode.group_id == group.id,
                PokerInvitationCode.role == "organizer",
                PokerInvitationCode.is_used == 0,
            ).first()
            if pending:
                return {"success": False, "message": "organizerInvitePending"}

        # Generate unique code
        for _ in range(10):
            code = generate_invite_code(group.id)
            if not db.query(PokerInvitationCode).filter(PokerInvitationCode.code == code).first():
                break

        invitation = PokerInvitationCode(
            code=code,
            group_id=group.id,
            role=role,
            is_used=0,
            created_at=now_columbus_naive(),
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return {
            "success": True,
            "message": "inviteCreateSuccess",
            "invite_id": invitation.id,
            "code": invitation.code,
            "group_id": group.id,
            "group_name": group.group_name,
            "role": invitation.role,
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def delete_invitation_code_service(invitation_id):
    db = SessionLocal()
    try:
        inv = db.query(PokerInvitationCode).filter(PokerInvitationCode.id == invitation_id).first()
        if not inv:
            return {"success": False, "message": "inviteCodeNotFound"}
        if inv.is_used == 1:
            return {"success": False, "message": "usedInviteDeleteForbidden"}

        code, role = inv.code, inv.role
        db.delete(inv)
        db.commit()
        return {"success": True, "message": "inviteDeleteSuccess", "code": code, "role": role}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def force_delete_group_service(group_id, expected_group_code):
    db = SessionLocal()
    try:
        group = db.query(PokerGroup).filter(PokerGroup.id == group_id).with_for_update().first()
        if group is None:
            return {"success": False, "message": "groupNotFound"}
        if expected_group_code != group.group_code:
            return {"success": False, "message": "forceGroupCodeMismatch"}

        game_ids = [r[0] for r in db.query(PokerGame.id).filter(PokerGame.group_id == group.id).all()]
        counts = {"games": len(game_ids)}
        if game_ids:
            counts["chip_requests"] = db.query(PokerChipRequest).filter(
                PokerChipRequest.game_id.in_(game_ids)
            ).delete(synchronize_session=False)
            counts["players"] = db.query(PokerGamePlayer).filter(
                PokerGamePlayer.game_id.in_(game_ids)
            ).delete(synchronize_session=False)
            db.query(PokerGame).filter(PokerGame.id.in_(game_ids)).delete(synchronize_session=False)
        else:
            counts["chip_requests"] = 0
            counts["players"] = 0

        counts["members"] = db.query(PokerUserGroupRole).filter(
            PokerUserGroupRole.group_id == group.id
        ).delete(synchronize_session=False)
        counts["invites"] = db.query(PokerInvitationCode).filter(
            PokerInvitationCode.group_id == group.id
        ).delete(synchronize_session=False)

        code, name = group.group_code, group.group_name
        db.delete(group)
        db.commit()
        return {
            "success": True, "message": "forceGroupDeleteSuccess",
            "group_code": code, "group_name": name, "counts": counts,
        }
    except Exception:
        db.rollback()
        return {"success": False, "message": "operationFailed"}
    finally:
        db.close()
