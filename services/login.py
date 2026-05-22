from passlib.context import CryptContext

from database import SessionLocal
from models import User


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def login_user_service(request, username, password):
    username = username.strip()

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user:
            return {
                "success": False,
                "message": "用户不存在。"
            }

        if not pwd_context.verify(
            password,
            user.password_hash
        ):
            return {
                "success": False,
                "message": "密码错误。"
            }

        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["role"] = user.role

        display_name = user.nickname or user.username
        display_role = user.role

        return {
            "success": True,
            "message": f"{display_role}-{display_name} 登录成功，3秒后跳转。",
            "role": user.role
        }

    except Exception as e:
        print(e)

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()