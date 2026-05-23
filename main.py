from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from routes.admin import router as admin_router
from routes.avatar import router as avatar_router
from routes.common import router as common_router
from routes.login import router as login_router
from routes.register import router as register_router


load_dotenv()

app = FastAPI()

app.include_router(register_router)
app.include_router(login_router)
app.include_router(admin_router)
app.include_router(avatar_router)
app.include_router(common_router)

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

STATIC_VERSION = datetime.utcnow().strftime("%Y%m%d%H%M%S")