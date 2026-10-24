import os

from poker.core import settings

DEFAULT_ADMIN_EMAIL = "admin@urea-king.com"


def get_index_context() -> dict:
    """首页模板需要的动态配置，可通过环境变量覆盖。"""
    return {
        "poker_url": settings.poker_url(),
        "admin_email": os.getenv("ADMIN_CONTACT_EMAIL", DEFAULT_ADMIN_EMAIL),
    }


def should_redirect_to_poker(host: str) -> bool:
    """
    访问 / 时是否直接去 poker 登录页。
    线上：poker 子域名是；主域名显示首页。
    测试环境：所有地址都在同一个站点上，/ 显示首页，方便测试首页和进入 poker 的过渡。
    """
    return settings.is_poker_host(host) and not settings.IS_STAGING
