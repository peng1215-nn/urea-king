from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from routes.admin.admin import router as admin_router
from routes.admin import system_logs
from routes.admin import invite_management
from routes.admin import announcement
from routes.common.avatar import router as avatar_router
from routes.common.common import router as common_router
from routes.auth.login import router as login_router
from routes.auth.register import router as register_router
from routes.admin.change_password import router as admin_change_password_router
from routes.organizer.change_password import router as organizer_change_password_router
from routes.organizer.announcement import router as organizer_announcement_router
from routes.organizer.invite_management import router as organizer_invite_router
from routes.organizer.game_log import router as organizer_game_log_router
from routes.organizer.organizer import router as organizer_router
from routes.organizer.game_management import router as game_router
from routes.auth.group_join import router as group_join_router
from routes.user.dashboard import router as user_dashboard_router
from routes.user.game import router as user_game_router
from routes.user.misc import router as user_misc_router


load_dotenv()

app = FastAPI()

app.include_router(register_router)
app.include_router(login_router)
app.include_router(group_join_router)
app.include_router(admin_router)
app.include_router(avatar_router)
app.include_router(common_router)
app.include_router(invite_management.router)
app.include_router(system_logs.router)
app.include_router(announcement.router)
app.include_router(admin_change_password_router)
app.include_router(organizer_change_password_router)
app.include_router(organizer_announcement_router)
app.include_router(organizer_invite_router)
app.include_router(organizer_game_log_router)
app.include_router(organizer_router)
app.include_router(game_router)
app.include_router(user_dashboard_router)
app.include_router(user_game_router)
app.include_router(user_misc_router)


SESSION_SECRET_KEY = os.getenv(
    "SESSION_SECRET_KEY",
    "local-dev-secret-key"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=60 * 60 * 24,
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

STATIC_VERSION = datetime.utcnow().strftime("%Y%m%d%H%M%S")