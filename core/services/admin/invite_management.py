from utils.time import now_columbus_naive
from database import SessionLocal
from core.models import PlatformGroup
from poker.models import (
    PokerGroup,
    PokerInvitationCode,
    PokerUserGroupRole,
    PokerGame,
    PokerGamePlayer,
    PokerChipRequest,
)
from poker.utils.invite import generate_invite_code


def get_group_options_service(module: str = "poker"):
    """Return groups for a given module, sourced from platform_groups registry."""
    db = SessionLocal()
    try:
        groups = (
            db.query(PlatformGroup)
            .filter(PlatformGroup.module == module)
            .order_by(PlatformGroup.id)
            .all()
        )
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


def create_group_service(group_code, group_name, admin_id=None, module="poker"):
    """Create a group: registers in platform_groups, then creates module-specific group."""
    db = SessionLocal()
    try:
        group_code = group_code.strip()
        group_name = group_name.strip()

        if not group_code:
            return {"success": False, "message": "groupCodeRequired"}
        if not group_name:
            return {"success": False, "message": "groupNameRequired"}

        # Check uniqueness in platform registry
        if db.query(PlatformGroup).filter(PlatformGroup.group_code == group_code).first():
            return {"success": False, "message": "groupCodeExists"}
        if db.query(PlatformGroup).filter(
            PlatformGroup.group_name == group_name,
            PlatformGroup.module == module,
        ).first():
            return {"success": False, "message": "groupNameExists"}

        # 1. Register in platform_groups
        platform_group = PlatformGroup(
            group_code=group_code,
            group_name=group_name,
            module=module,
            created_by_admin_id=admin_id,
            created_at=now_columbus_naive(),
        )
        db.add(platform_group)
        db.flush()  # get platform_group.id before committing

        # 2. Create module-specific group (poker)
        if module == "poker":
            poker_group = PokerGroup(
                platform_group_id=platform_group.id,
                group_code=group_code,
                group_name=group_name,
                created_at=now_columbus_naive(),
            )
            db.add(poker_group)

        db.commit()
        db.refresh(platform_group)

        return {
            "success": True,
            "message": "groupCreateSuccess",
            "group_id": platform_group.id,
            "group_code": platform_group.group_code,
            "group_name": platform_group.group_name,
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def delete_group_service(platform_group_id):
    """Delete a group (must be empty). Removes from platform_groups and poker_groups."""
    db = SessionLocal()
    try:
        pg = db.query(PlatformGroup).filter(PlatformGroup.id == platform_group_id).first()
        if not pg:
            return {"success": False, "message": "groupNotFound"}

        # Find corresponding poker group
        poker_group = db.query(PokerGroup).filter(
            PokerGroup.platform_group_id == platform_group_id
        ).first()

        if poker_group:
            member_count = db.query(PokerUserGroupRole).filter(
                PokerUserGroupRole.group_id == poker_group.id
            ).count()
            if member_count > 0:
                return {"success": False, "message": "groupHasMembers"}

            unused_invite_count = db.query(PokerInvitationCode).filter(
                PokerInvitationCode.group_id == poker_group.id,
                PokerInvitationCode.is_used == 0,
            ).count()
            if unused_invite_count > 0:
                return {"success": False, "message": "groupHasUnusedInvites"}

            db.delete(poker_group)

        code, name = pg.group_code, pg.group_name
        db.delete(pg)
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


def create_invitation_code_service(platform_group_id, role):
    """Generate a new POKER-G{id}-XXXX invite code for a poker group (admin-created)."""
    db = SessionLocal()
    try:
        if role not in ["organizer", "user"]:
            return {"success": False, "message": "inviteRoleInvalid"}

        # Resolve platform group → poker group
        pg = db.query(PlatformGroup).filter(PlatformGroup.id == platform_group_id).first()
        if not pg:
            return {"success": False, "message": "groupNotFound"}

        poker_group = db.query(PokerGroup).filter(
            PokerGroup.platform_group_id == platform_group_id
        ).first()
        if not poker_group:
            return {"success": False, "message": "pokerGroupNotFound"}

        if role == "organizer":
            existing_organizer = db.query(PokerUserGroupRole).filter(
                PokerUserGroupRole.group_id == poker_group.id,
                PokerUserGroupRole.role == "organizer",
            ).first()
            if existing_organizer:
                return {"success": False, "message": "organizerAlreadyExists"}

            pending = db.query(PokerInvitationCode).filter(
                PokerInvitationCode.group_id == poker_group.id,
                PokerInvitationCode.role == "organizer",
                PokerInvitationCode.is_used == 0,
            ).first()
            if pending:
                return {"success": False, "message": "organizerInvitePending"}

        # Generate unique code
        for _ in range(10):
            code = generate_invite_code(poker_group.id)
            if not db.query(PokerInvitationCode).filter(PokerInvitationCode.code == code).first():
                break

        invitation = PokerInvitationCode(
            code=code,
            group_id=poker_group.id,
            role=role,
            is_used=0,
            created_by="admin",
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
            "group_id": pg.id,
            "group_name": pg.group_name,
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


def force_delete_group_service(platform_group_id, expected_group_code):
    """Force-delete a group and all its data. Removes from platform_groups and poker_groups."""
    db = SessionLocal()
    try:
        pg = db.query(PlatformGroup).filter(
            PlatformGroup.id == platform_group_id
        ).with_for_update().first()
        if pg is None:
            return {"success": False, "message": "groupNotFound"}
        if expected_group_code != pg.group_code:
            return {"success": False, "message": "forceGroupCodeMismatch"}

        poker_group = db.query(PokerGroup).filter(
            PokerGroup.platform_group_id == platform_group_id
        ).first()

        counts = {"games": 0, "chip_requests": 0, "players": 0, "members": 0, "invites": 0}

        if poker_group:
            game_ids = [r[0] for r in db.query(PokerGame.id).filter(
                PokerGame.group_id == poker_group.id
            ).all()]
            counts["games"] = len(game_ids)
            if game_ids:
                counts["chip_requests"] = db.query(PokerChipRequest).filter(
                    PokerChipRequest.game_id.in_(game_ids)
                ).delete(synchronize_session=False)
                counts["players"] = db.query(PokerGamePlayer).filter(
                    PokerGamePlayer.game_id.in_(game_ids)
                ).delete(synchronize_session=False)
                db.query(PokerGame).filter(
                    PokerGame.id.in_(game_ids)
                ).delete(synchronize_session=False)

            counts["members"] = db.query(PokerUserGroupRole).filter(
                PokerUserGroupRole.group_id == poker_group.id
            ).delete(synchronize_session=False)
            counts["invites"] = db.query(PokerInvitationCode).filter(
                PokerInvitationCode.group_id == poker_group.id
            ).delete(synchronize_session=False)

            db.delete(poker_group)

        code, name = pg.group_code, pg.group_name
        db.delete(pg)
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
