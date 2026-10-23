"""
用户输入的通用校验。

输出转义（前端 escapeHtml）才是防 XSS 的根本手段，这里的校验是第二道防线：
限制长度、剔除控制字符和不可见的方向控制字符，并禁止名称类字段出现尖括号。
"""

import re


# 控制字符、零宽空格、双向文本控制符（可被用来伪装显示内容）。
# 不包括 U+200C / U+200D：组合 emoji（如一家人、带火的心）依赖它们。
_INVISIBLE_RE = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f"
    "\u200b\u200e\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]"
)
_NEWLINE_RE = re.compile("[\r\n\t]")
_ANGLE_RE = re.compile("[<>]")


# 各字段长度上限（不超过数据库列宽）
NICKNAME_MAX = 50
ALIAS_MAX = 50
GAME_NAME_MAX = 50
GROUP_NAME_MAX = 50
GAME_NOTE_MAX = 500
ANNOUNCEMENT_TITLE_MAX = 200
ANNOUNCEMENT_CONTENT_MAX = 5000

PASSWORD_MIN = 8
PASSWORD_MAX = 128


def check_name(value, max_len):
    """
    名称类单行字段（昵称、别名、牌局名、组名）。
    返回 (清洗后的值, 错误原因)；错误原因为 None 表示通过。
    错误原因：'too_long' | 'invalid_chars'
    """
    value = (value or "").strip()

    if _INVISIBLE_RE.search(value) or _NEWLINE_RE.search(value) or _ANGLE_RE.search(value):
        return value, "invalid_chars"

    if len(value) > max_len:
        return value, "too_long"

    return value, None


def check_text(value, max_len):
    """
    多行文本字段（备注、公告内容）：允许换行和尖括号（前端会转义），
    但不允许不可见控制字符。
    """
    value = (value or "").strip()

    if _INVISIBLE_RE.search(value):
        return value, "invalid_chars"

    if len(value) > max_len:
        return value, "too_long"

    return value, None


def check_password(password):
    """返回错误原因：None | 'too_short' | 'too_long'"""
    password = password or ""

    if len(password) < PASSWORD_MIN:
        return "too_short"

    if len(password) > PASSWORD_MAX:
        return "too_long"

    return None
