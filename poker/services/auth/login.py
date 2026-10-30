from database import SessionLocal
from poker.models import Group
from poker.models import User
from poker.models import UserGroupRole
from core.models import UserModule
from poker.services.admin.audit_log import write_audit_log
from core.errors import safe_error
from core.middleware import LOGIN_AT_KEY, now_timestamp
from core.security import password_fingerprint, pwd_context, verify_user_password




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

        # 邮箱未验证则不允许登录
        if not user.email_verified:
            return {
                "success": False,
                "error_code": "loginEmailNotVerified",
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

        # 首次登录 poker 模块 → 补插模块记录（已从其他模块来的用户）
        already = db.query(UserModule).filter(
            UserModule.user_id == user.id,
            UserModule.module == "poker",
        ).first()
        if not already:
            db.add(UserModule(user_id=user.id, module="poker"))
            db.commit()

        # 旧 pbkdf2_sha256 哈希在首次登录成功时静默升级为 bcrypt。
        # 升级失败（例如旧密码超过 bcrypt 的 72 字节上限）不影响本次登录，下次再试。
        if user.password_hash.startswith("$pbkdf2-sha256$"):
            try:
                user.password_hash = pwd_context.hash(password)
                db.commit()
            except Exception as e:
                db.rollback()
                safe_error(e)

        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["pw_fp"] = password_fingerprint(user.password_hash)
        # 登录状态最长保持 SESSION_ABSOLUTE_MAX_AGE，从此刻开始计算（见 core/middleware.py）
        request.session[LOGIN_AT_KEY] = now_timestamp()
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
            db=db,
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
            # 没有任何组时，前端引导用户创建或加入
            "has_groups": len(group_roles) > 0,
        }

    except Exception as e:
        safe_error(e)

        return {
            "success": False,
            "error_code": "loginFailed",
        }

    finally:
        db.close()


ROLE_HOME = {
    "admin": "/admin-dashboard",
    "organizer": "/organizer-dashboard",
    "user": "/user-dashboard",
}


def select_group_service(user_id, group_id):
    """登录后选择进入哪个组。返回该组信息和身份，由路由写入会话。"""
    db = SessionLocal()

    try:
        user_group_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id,
            UserGroupRole.group_id == group_id,
        ).first()

        if not user_group_role:
            return {"success": False, "error_code": "groupAccessDenied"}

        group = db.query(Group).filter(Group.id == group_id).first()

        if not group:
            return {"success": False, "error_code": "groupNotFound"}

        return {
            "success": True,
            "group_id": group.id,
            "group_code": group.group_code,
            "role": user_group_role.role,
            "redirect_url": ROLE_HOME.get(user_group_role.role, "/user-dashboard"),
        }

    finally:
        db.close()


def get_user_groups_service(user_id):
    """获取用户加入的所有组（用于 group_select 页面服务端渲染）。"""
    db = SessionLocal()
    try:
        group_roles = db.query(
            UserGroupRole,
            Group,
        ).join(
            Group,
            UserGroupRole.group_id == Group.id,
        ).filter(
            UserGroupRole.user_id == user_id,
        ).all()

        return [
            {
                "group_id": group.id,
                "group_code": group.group_code,
                "group_name": group.group_name,
                "role": user_group_role.role,
            }
            for user_group_role, group in group_roles
        ]
    except Exception as e:
        safe_error(e)
        return []
    finally:
        db.close()
