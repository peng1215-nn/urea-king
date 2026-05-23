from passlib.context import CryptContext
from database import SessionLocal
from models import User


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def login_user_service(request, username, password):
    db = SessionLocal()

    try:
        username = username.strip()

        user = db.query(User).filter(User.username == username).first()

        if not user:
            return {"success": False, "error_code": "loginUserNotFound"}

        if not pwd_context.verify(password, user.password_hash):
            return {"success": False, "error_code": "loginPasswordIncorrect"}

        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["role"] = user.role

        return {
            "success": True,
            "role": user.role,
            "display_name": user.nickname or user.username,
        }

    except Exception as e:
        print(e)
        return {"success": False, "error_code": "loginFailed"}

    finally:
        db.close()