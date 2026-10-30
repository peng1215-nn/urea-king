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
PASSWORD_MIN = 8
# bcrypt 只接受最多 72 字节的密码（bcrypt 5.0 起超长直接报错），按 UTF-8 字节数计算。
# 英文、数字、符号每个 1 字节；汉字每个 3 字节，最多 24 个。
PASSWORD_MAX_BYTES = 72


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


# 弱密码规则（前端提示文案里写明了这三条，改规则时一起改 i18n 里的 *PasswordTooWeak）：
#   1. 由 1–4 个字符反复重复组成，如 11111111、12121212、abcabcab、12341234
#   2. 整个密码是一段连续的数字、字母或键盘排列，如 12345678、87654321、abcdefgh、qwertyui
#   3. 常见密码，如 password、iloveyou、1qaz2wsx（不区分大小写）
_SEQUENCES = (
    "0123456789",
    "1234567890",
    "abcdefghijklmnopqrstuvwxyz",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
    "qwertyuiopasdfghjklzxcvbnm",
)

COMMON_PASSWORDS = frozenset({
    "password", "password1", "password12", "password123", "passw0rd", "p@ssw0rd", "p@ssword",
    "iloveyou", "iloveyou1", "sunshine", "princess", "football", "baseball", "superman",
    "welcome1", "welcome123", "letmein1", "trustno1", "computer", "internet", "starwars",
    "admin123", "admin1234", "administrator", "root1234", "test1234", "testtest",
    "abc12345", "abc123456", "a1234567", "a12345678", "a123456789", "aa123456", "aa12345678",
    "qq123456", "qwe12345", "qwer1234", "qwert123", "qwerty12", "qwerty123", "qwerty1234",
    "1qaz2wsx", "1qaz2wsx3edc", "1q2w3e4r", "1q2w3e4r5t", "1q2w3e4r5t6y", "q1w2e3r4", "q1w2e3r4t5",
    "123qweasd", "qweasdzxc", "123qwe123", "zxcvbnm1", "asdf1234", "1234qwer", "1234abcd",
    "123456abc", "123456aa", "12345678a", "123456789a", "11223344", "12344321", "1234554321",
    "5201314520", "52013145", "woaini1314", "woaini520", "iloveyou520",
    "ureaking", "ureaking123", "urea-king", "poker123", "pokerpoker", "pokerking",
})


def _is_repeated_pattern(value):
    for size in range(1, 5):
        unit = value[:size]
        if len(value) > size and (unit * (len(value) // size + 1))[: len(value)] == value:
            return True
    return False


def _is_sequence(value):
    for sequence in _SEQUENCES:
        if value in sequence or value in sequence[::-1]:
            return True
    return False


def is_weak_password(password):
    value = (password or "").lower()
    return (
        _is_repeated_pattern(value)
        or _is_sequence(value)
        or value in COMMON_PASSWORDS
    )


def check_password(password):
    """返回错误原因：None | 'too_short' | 'too_long' | 'too_weak'"""
    password = password or ""

    if len(password) < PASSWORD_MIN:
        return "too_short"

    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        return "too_long"

    if is_weak_password(password):
        return "too_weak"

    return None
