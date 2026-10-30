from contextlib import asynccontextmanager

from starlette.concurrency import run_in_threadpool
from core.time import now_columbus_naive
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# settings 会加载 .env 并校验必需的配置，必须最先导入
from core import settings
from core.logging_config import setup_logging
from core.error_reporting import setup_error_reporting
from core.errors import register_exception_handlers
from core.middleware import install_middleware
from poker.core import session as poker_session
from poker.template_config import render_error_page
from poker.services.auth.token_cleanup import delete_expired_tokens
from poker.routes.common.health import router as health_router

from root.routes.index import router as root_index_router
from poker.routes.admin.admin import router as admin_router
from poker.routes.admin import system_logs
from poker.routes.admin import invite_management
from poker.routes.admin import announcement
from poker.routes.admin.game_log import router as admin_game_log_router
from poker.routes.common.avatar import router as avatar_router
from poker.routes.common.common import router as common_router
from poker.routes.common.game_report import router as game_report_router
from poker.routes.common.account_email import router as account_email_router
from poker.routes.auth.login import router as login_router
from poker.routes.auth.register import router as register_router
from poker.routes.admin.change_password import router as admin_change_password_router
from poker.routes.organizer.change_password import router as organizer_change_password_router
from poker.routes.organizer.announcement import router as organizer_announcement_router
from poker.routes.organizer.invite_management import router as organizer_invite_router
from poker.routes.organizer.game_log import router as organizer_game_log_router
from poker.routes.organizer.organizer import router as organizer_router
from poker.routes.organizer.game_management import router as game_router
from poker.routes.auth.group_join import router as group_join_router
from poker.routes.auth.delete_account import router as delete_account_router
from poker.routes.auth.password import router as password_router
from poker.routes.auth.group import router as create_group_router
from poker.routes.user.dashboard import router as user_dashboard_router
from poker.routes.user.game import router as user_game_router
from poker.routes.user.announcement import router as user_announcement_router
from poker.routes.user.change_password import router as user_change_password_router
from poker.routes.user.game_log import router as user_game_log_router


setup_logging(settings.LOG_LEVEL)
setup_error_reporting()

# 线上（含测试环境）不公开接口文档，避免把全部接口和参数暴露给未登录的访客
@asynccontextmanager
async def lifespan(app):
    # 启动时清理一次早已过期的验证、重置链接记录
    await run_in_threadpool(delete_expired_tokens)
    yield


if settings.IS_PRODUCTION:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan)

register_exception_handlers(app, error_page_renderer=render_error_page)


# 平台健康检查请求的 Host 不是我们的域名，这些路径不做域名跳转
_HOST_AGNOSTIC_PATHS = ("/healthz", "/readyz")


async def domain_router(request: Request, call_next):
    host = request.headers.get("host", "")
    path = request.url.path
    if path in _HOST_AGNOSTIC_PATHS:
        return await call_next(request)
    # non-poker domain: only allow "/" and static assets
    if not settings.is_poker_host(host) and not host.startswith("localhost") and not host.startswith("127."):
        if path == "/" or path.startswith("/static"):
            return await call_next(request)
        return RedirectResponse(url="/")
    return await call_next(request)


app.include_router(health_router)
app.include_router(root_index_router)
app.include_router(register_router)
app.include_router(login_router)
app.include_router(group_join_router)
app.include_router(delete_account_router)
app.include_router(password_router)
app.include_router(create_group_router)
app.include_router(admin_router)
app.include_router(avatar_router)
app.include_router(common_router)
app.include_router(game_report_router)
app.include_router(account_email_router)
app.include_router(invite_management.router)
app.include_router(system_logs.router)
app.include_router(announcement.router)
app.include_router(admin_change_password_router)
app.include_router(admin_game_log_router)
app.include_router(organizer_change_password_router)
app.include_router(organizer_announcement_router)
app.include_router(organizer_invite_router)
app.include_router(organizer_game_log_router)
app.include_router(organizer_router)
app.include_router(game_router)
app.include_router(user_dashboard_router)
app.include_router(user_game_router)
app.include_router(user_announcement_router)
app.include_router(user_change_password_router)
app.include_router(user_game_log_router)


# ───── 中间件（顺序与说明见 core/middleware.py 的 install_middleware）─────
install_middleware(
    app,
    domain_router,
    public_paths=poker_session.PUBLIC_PATHS,
    session_key=poker_session.session_key,
    session_validator=poker_session.session_is_valid,
)

app.mount(
    "/static/root",
    StaticFiles(directory="root/static"),
    name="root-static"
)

app.mount(
    "/static",
    StaticFiles(directory="poker/static"),
    name="static"
)

STATIC_VERSION = now_columbus_naive().strftime("%Y%m%d%H%M%S")
