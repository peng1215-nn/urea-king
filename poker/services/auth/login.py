from database import SessionLocal
from core.models import PlatformUser
from core.utils.security import verify_password
from poker.models import PokerGroup, PokerUserGroupRole
from poker.services.admin.audit_log import write_audit_log


def login_user_service(request, username: str, password: str):
    db = SessionLocal()
    try:
        username = username.strip()

        user = db.query(PlatformUser).filter(PlatformUser.username == username).first()
        if not user:
            return {"success": False, "error_code": "loginUserNotFound"}

        if not verify_password(password, user.password_hash):
            return {"success": False, "error_code": "loginPasswordIncorrect"}

        if user.is_active == 0:
            return {"success": False, "error_code": "loginAccountDisabled"}

        group_roles = (
            db.query(PokerUserGroupRole, PokerGroup)
            .join(PokerGroup, PokerUserGroupRole.group_id == PokerGroup.id)
            .filter(PokerUserGroupRole.user_id == user.id)
            .all()
        )

        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session.pop("current_group_id", None)
        request.session.pop("current_group_code", None)
        request.session.pop("current_role", None)

        write_audit_log(
            request=request,
            action="LOGIN_SUCCESS",
            target_type="user",
            target_id=user.id,
            old_value=None,
            new_value="login_verified",
            operator_id=user.id,
            operator_username=user.username,
        )

        return {
            "success": True,
            "display_name": user.nickname or user.username,
            "groups": [
                {
                    "group_id": group.id,
                    "group_code": group.group_code,
                    "group_name": group.group_name,
                    "role": ugr.role,
                }
                for ugr, group in group_roles
            ],
        }

    except Exception as e:
        return {"success": False, "error_code": "loginFailed", "message": str(e)}
    finally:
        db.close()
