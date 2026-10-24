"""
poker 模块的字段规则：各字段长度上限、金额上限。
通用的校验函数（check_name、check_text、check_password）在 core/validators.py。
"""

NICKNAME_MAX = 50
ALIAS_MAX = 50
GAME_NAME_MAX = 50
GROUP_NAME_MAX = 50
GAME_NOTE_MAX = 500
ANNOUNCEMENT_TITLE_MAX = 200
ANNOUNCEMENT_CONTENT_MAX = 5000

# 单次买入、带走、结算金额的上限，只用来拦住误输
MAX_AMOUNT = 1_000_000


def check_amount(amount, allow_zero=False):
    """
    金额校验。返回 None 表示通过，否则返回错误码：
    invalidAmount（不是整数、负数、或不允许为 0 时为 0）、amountTooLarge（超过上限）。
    """
    if isinstance(amount, bool) or not isinstance(amount, int):
        return "invalidAmount"
    if amount < 0 or (amount == 0 and not allow_zero):
        return "invalidAmount"
    if amount > MAX_AMOUNT:
        return "amountTooLarge"
    return None
