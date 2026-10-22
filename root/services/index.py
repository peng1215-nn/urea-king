import os

DEFAULT_POKER_URL = "https://poker.urea-king.com"
DEFAULT_ADMIN_EMAIL = "admin@urea-king.com"


def get_index_context() -> dict:
    """首页模板需要的动态配置，可通过环境变量覆盖。"""
    return {
        "poker_url": os.getenv("POKER_URL", DEFAULT_POKER_URL),
        "admin_email": os.getenv("ADMIN_CONTACT_EMAIL", DEFAULT_ADMIN_EMAIL),
    }


def is_poker_host(host: str) -> bool:
    return host.startswith("poker.")
