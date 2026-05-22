from fastapi import FastAPI
from fastapi import Request
from fastapi import Form
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from database import SessionLocal
from models import User
from models import InvitationCode
from routes.register import router as register_router
from routes.admin import router as admin_router
from routes.avatar import router as avatar_router
from dotenv import load_dotenv
import os


load_dotenv()

app = FastAPI()


app.include_router(avatar_router)

SESSION_SECRET_KEY = os.getenv(
    "SESSION_SECRET_KEY",
    "local-dev-secret-key"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)


app.include_router(register_router)
app.include_router(admin_router)

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@app.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):

    if request.session.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="admin/admin_dashboard.html",
        context = {
            "current_page": "dashboard"
        }
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.get("/system-monitor", response_class=HTMLResponse)
def system_monitor(request: Request):

    if request.session.get("role") != "admin":
        return RedirectResponse(
            url="/login",
            status_code=302
        )

    response = templates.TemplateResponse(
        request=request,
        name="admin/system_monitor.html",
        context={
            "current_page": "system_monitor"
        }
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.get("/user-management", response_class=HTMLResponse)
def user_management(request: Request):

    if request.session.get("role") != "admin":

        return RedirectResponse(
            url="/login",
            status_code=302
        )

    response = templates.TemplateResponse(
        request=request,
        name="admin/user_management.html",
        context = {
            "current_page": "user_management"
        }
    )

    response.headers["Cache-Control"] = \
        "no-store, no-cache, must-revalidate, max-age=0"

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    return response


@app.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):

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


@app.get("/logout")
def logout(request: Request):

    request.session.clear()

    response = RedirectResponse(
        url="/login",
        status_code=302
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response