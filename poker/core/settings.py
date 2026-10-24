"""
运行环境与安全相关配置，统一从环境变量读取。

生产环境判断：APP_ENV 显式指定时以它为准（production、staging 都按生产环境的安全设置运行）；
否则在 Render（RENDER）或 Railway（RAILWAY_ENVIRONMENT_NAME / RAILWAY_ENVIRONMENT）上运行即视为生产环境。
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


APP_ENV = os.getenv("APP_ENV", "").strip().lower()

# 测试环境（staging）：和线上一样的安全设置，但单独标记，并在任何主机名下都提供 poker 应用
IS_STAGING = APP_ENV == "staging"


def _is_production():
    if APP_ENV:
        return APP_ENV in ("production", "staging")
    # 托管平台会自动设置这些变量：Render 设置 RENDER=true，Railway 设置 RAILWAY_ENVIRONMENT_NAME
    return bool(
        os.getenv("RENDER")
        or os.getenv("RAILWAY_ENVIRONMENT_NAME")
        or os.getenv("RAILWAY_ENVIRONMENT")
    )


IS_PRODUCTION = _is_production()

if IS_STAGING:
    DEPLOY_ENVIRONMENT = "Staging"
elif IS_PRODUCTION:
    DEPLOY_ENVIRONMENT = "Production"
else:
    DEPLOY_ENVIRONMENT = "Development"


def is_poker_host(host):
    """
    这个主机名是否直接提供 poker 应用（而不是主域名首页）。
    线上：poker. 开头的子域名；测试环境：任何主机名（用 Render 分配的 onrender.com 地址）。
    """
    return IS_STAGING or (host or "").startswith("poker.")


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
