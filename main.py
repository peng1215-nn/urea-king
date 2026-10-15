import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from utils.time import now_columbus_naive

# Platform REST API
from core.routes.auth import router as platform_auth_router

# Platform admin web routes
from core.routes.admin.admin import router as admin_router
from core.routes.admin.system_logs import router as system_logs_router
from core.routes.admin.invite_management import router as admin_invite_router
from core.routes.admin.announcement import router as admin_announcement_router
from core.routes.admin.change_password import router as admin_change_password_router

# Poker web routes — auth
from poker.routes.auth.login import router as login_router
from poker.routes.auth.register import router as register_router
from poker.routes.auth.group_join import router as group_join_router

# Poker web routes — organizer
from poker.routes.organizer.organizer import router as organizer_router
from poker.routes.organizer.change_password import router as organizer_change_password_router
from poker.routes.organizer.announcement import router as organizer_announcement_router
from poker.routes.organizer.invite_management import router as organizer_invite_router
from poker.routes.organizer.game_log import router as organizer_game_log_router
from poker.routes.organizer.game_management import router as game_router

# Poker web routes — user
from poker.routes.user.dashboard import router as user_dashboard_router
from poker.routes.user.game import router as user_game_router
from poker.routes.user.misc import router as user_misc_router

# Poker web routes — common
from poker.routes.common.avatar import router as avatar_router
from poker.routes.common.common import router as common_router


load_dotenv()

app = FastAPI()


@app.get("/")
def root():
    return RedirectResponse(url="/poker/login", status_code=302)

# Platform REST API (prefix /platform)
app.include_router(platform_auth_router)

# Platform admin web
app.include_router(admin_router)
app.include_router(system_logs_router)
app.include_router(admin_invite_router)
app.include_router(admin_announcement_router)
app.include_router(admin_change_password_router)

# Poker auth
app.include_router(login_router)
app.include_router(register_router)
app.include_router(group_join_router)

# Organizer
app.include_router(organizer_router)
app.include_router(organizer_change_password_router)
app.include_router(organizer_announcement_router)
app.include_router(organizer_invite_router)
app.include_router(organizer_game_log_router)
app.include_router(game_router)

# User
app.include_router(user_dashboard_router)
app.include_router(user_game_router)
app.include_router(user_misc_router)

# Common
app.include_router(avatar_router)
app.include_router(common_router)


SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "local-dev-secret-key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=60 * 60 * 24,
)

app.mount("/static/platform", StaticFiles(directory="core/static"), name="static-platform")
app.mount("/static/poker", StaticFiles(directory="poker/static"), name="static-poker")

STATIC_VERSION = now_columbus_naive().strftime("%Y%m%d%H%M%S")
