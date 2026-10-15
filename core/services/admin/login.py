"""Platform admin web login service — session-based, queries platform_users."""
from database import SessionLocal
from core.models import PlatformUser, PlatformUserGroupRole
from core.utils.security import verify_password
from core.services.admin.audit_log import write_audit_log


def admin_login_service(request, username: str, password: str):
    db = SessionLocal()
    try:
        username = username.strip()

        user = db.query(PlatformUser).filter(PlatformUser.username == username).first()
        if not user:
            return {"success": False, "error_code": "loginUserNotFound"}

        if not verify_password(password, user.password_hash):
            return {"success": False, "error_code": "loginPasswordIncorrect"}

        if user.is_active != 1:
            return {"success": False, "error_code": "loginAccountDisabled"}

        # Must have a platform_user_group_roles entry (must be a platform admin)
        platform_role = db.query(PlatformUserGroupRole).filter(
            PlatformUserGroupRole.user_id == user.id
        ).first()
        if not platform_role:
            return {"success": False, "error_code": "loginNotPlatformAdmin"}

        # Set session
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["is_platform_admin"] = True
        request.session["current_role"] = "admin"
        request.session.pop("current_group_id", None)
        request.session.pop("current_group_code", None)

        write_audit_log(
            request=request,
            action="ADMIN_LOGIN_SUCCESS",
            target_type="platform_user",
            target_id=user.id,
            old_value=None,
            new_value="login_verified",
            operator_id=user.id,
            operator_username=user.username,
        )

        return {
            "success": True,
            "display_name": user.nickname or user.username,
            "redirect_url": "/admin-dashboard",
        }

    except Exception as e:
        return {"success": False, "error_code": "loginFailed", "message": str(e)}
    finally:
        db.close()


def admin_logout_service(request):
    request.session.clear()
    return {"success": True}
