from database import SessionLocal
from poker.models import Group
from poker.models import User
from poker.models import UserGroupRole
from poker.services.admin.audit_log import write_audit_log
from poker.core.errors import safe_error
from poker.core.security import password_fingerprint, verify_user_password




def login_user_service(request, username, password):
    db = SessionLocal()

    try:
        username = username.strip()

        user = db.query(User).filter(
            User.username == username
        ).first()

        # 用户名不存在和密码错误给出同一个提示，避免被用来试探哪些用户名已注册
        if not verify_user_password(user, password):
            return {
                "success": False,
                "error_code": "loginInvalidCredentials",
            }

        if user.is_active == 0:
            return {
                "success": False,
                "error_code": "loginAccountDisabled",
            }

        group_roles = db.query(
            UserGroupRole,
            Group,
        ).join(
            Group,
            UserGroupRole.group_id == Group.id,
        ).filter(
            UserGroupRole.user_id == user.id,
        ).all()

        if not group_roles:
            return {
                "success": False,
                "error_code": "loginNoGroupAvailable",
            }

        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["pw_fp"] = password_fingerprint(user.password_hash)
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
                    "role": user_group_role.role,
                }
                for user_group_role, group in group_roles
            ],
        }

    except Exception as e:
        safe_error(e)

        return {
            "success": False,
            "error_code": "loginFailed",
        }

    finally:
        db.close()