from passlib.context import CryptContext

from database import SessionLocal
from models import Group
from models import User
from models import UserGroupRole


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def login_user_service(request, username, password):
    db = SessionLocal()

    try:
        username = username.strip()

        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user:
            return {
                "success": False,
                "error_code": "loginUserNotFound",
            }

        if not pwd_context.verify(
            password,
            user.password_hash,
        ):
            return {
                "success": False,
                "error_code": "loginPasswordIncorrect",
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

        request.session.pop("current_group_id", None)
        request.session.pop("current_group_code", None)
        request.session.pop("current_role", None)

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
        print(e)

        return {
            "success": False,
            "error_code": "loginFailed",
        }

    finally:
        db.close()