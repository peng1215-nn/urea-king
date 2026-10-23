"""
运行环境与安全相关配置，统一从环境变量读取。

生产环境判断：APP_ENV 显式指定时以它为准；否则在 Railway 上运行（存在
RAILWAY_ENVIRONMENT_NAME / RAILWAY_ENVIRONMENT）即视为生产环境。
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
    return bool(
        os.getenv("RAILWAY_ENVIRONMENT_NAME")
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
