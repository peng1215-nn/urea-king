"""
运行环境与安全相关配置，统一从环境变量读取。

生产环境判断：APP_ENV 显式指定时以它为准；否则在 Render（RENDER）或
Railway（RAILWAY_ENVIRONMENT_NAME / RAILWAY_ENVIRONMENT）上运行即视为生产环境。
"""

import logging
import os

from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger("poker.settings")


def _env_bool(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _is_production():
    app_env = os.getenv("APP_ENV", "").strip().lower()
    if app_env:
        return app_env == "production"
    # 托管平台会自动设置这些变量：Render 设置 RENDER=true，Railway 设置 RAILWAY_ENVIRONMENT_NAME
    return bool(
        os.getenv("RENDER")
        or os.getenv("RAILWAY_ENVIRONMENT_NAME")
        or os.getenv("RAILWAY_ENVIRONMENT")
    )


IS_PRODUCTION = _is_production()

DEPLOY_ENVIRONMENT = "Production" if IS_PRODUCTION else "Development"


_DEV_SESSION_SECRET = "local-dev-secret-key"

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "").strip()

if not SESSION_SECRET_KEY:
    if IS_PRODUCTION:
        # 生产环境绝不使用默认密钥：否则任何人都能伪造登录状态
        raise RuntimeError(
            "SESSION_SECRET_KEY is not set. It is required in production."
        )
    SESSION_SECRET_KEY = _DEV_SESSION_SECRET
    logger.warning(
        "SESSION_SECRET_KEY is not set; using the development default. "
        "Never run like this in production."
    )

# Cookie 只通过 HTTPS 发送；生产环境默认开启，本地 http 开发默认关闭
SESSION_HTTPS_ONLY = _env_bool("SESSION_HTTPS_ONLY", IS_PRODUCTION)

SESSION_MAX_AGE = 60 * 60 * 24

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 允许把本站页面嵌入 iframe 的来源（除本站自身外）。首页点 POKER 时会先在 iframe 里预加载
# poker 子站做过渡动画，所以需要允许主域名；其它网站一律不能嵌入（防点击劫持）。
FRAME_ANCESTORS = os.getenv(
    "FRAME_ANCESTORS",
    "https://urea-king.com https://www.urea-king.com",
).split()


def _origin(url):
    from urllib.parse import urlsplit

    parts = urlsplit(url or "")
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else ""


# 反过来，首页需要在 iframe 里加载 poker 子站（与首页的 POKER 链接同源，取自 POKER_URL）
FRAME_SOURCES = [
    origin for origin in [_origin(os.getenv("POKER_URL", "https://poker.urea-king.com"))]
    if origin
]
