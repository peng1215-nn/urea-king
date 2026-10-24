"""
出错告警（Sentry）。设置了环境变量 SENTRY_DSN 才启用，否则什么都不做。

做法：只接管日志。代码里出错的地方都会写一条 ERROR 级别的日志
（safe_error()、请求中间件里的未处理异常），这些日志会同时发到 Sentry，
Sentry 再按设置给你发邮件。
不启用 Sentry 对 FastAPI / Starlette 的自动接管，避免和框架版本绑定。
"""

import logging
import os

from poker.core import settings


logger = logging.getLogger("poker.error_reporting")


def setup_error_reporting():
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.DEPLOY_ENVIRONMENT.lower(),
        # 不发送用户 IP、Cookie、请求内容等个人信息
        send_default_pii=False,
        # 只要错误，不做性能追踪
        traces_sample_rate=0,
        auto_enabling_integrations=False,
        integrations=[
            # INFO 及以上的日志作为出错前的线索附带上去；ERROR 及以上才算一条错误
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    )
    logger.info("error reporting enabled")
    return True
