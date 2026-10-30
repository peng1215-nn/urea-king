from poker.core.validators import NICKNAME_MAX
from core.validators import (
    PASSWORD_MAX_BYTES,
    PASSWORD_MIN,
    check_name,
    check_password,
    check_text,
)


def test_name_is_trimmed_and_accepts_chinese_and_emoji():
    assert check_name("  米奇 🐭  ", NICKNAME_MAX) == ("米奇 🐭", None)


def test_name_rejects_angle_brackets():
    assert check_name("<img src=x onerror=alert(1)>", NICKNAME_MAX)[1] == "invalid_chars"


def test_name_rejects_newlines_and_invisible_characters():
    assert check_name("abc\ndef", NICKNAME_MAX)[1] == "invalid_chars"
    assert check_name("evil\u202eeman", NICKNAME_MAX)[1] == "invalid_chars"  # 文字方向反转
    assert check_name("zero\u200bwidth", NICKNAME_MAX)[1] == "invalid_chars"


def test_name_allows_emoji_joined_with_zwj():
    family = "\U0001F468\u200d\U0001F469\u200d\U0001F467"
    assert check_name(family + " 一家人", NICKNAME_MAX)[1] is None


def test_name_length_limit():
    assert check_name("a" * NICKNAME_MAX, NICKNAME_MAX)[1] is None
    assert check_name("a" * (NICKNAME_MAX + 1), NICKNAME_MAX)[1] == "too_long"


def test_name_none_becomes_empty_string():
    assert check_name(None, NICKNAME_MAX) == ("", None)


def test_text_allows_newlines_and_angle_brackets():
    value, error = check_text("第一行\n第二行 <b>", 100)
    assert error is None
    assert value == "第一行\n第二行 <b>"


def test_text_rejects_control_characters_and_overlong_text():
    assert check_text("a\x00b", 100)[1] == "invalid_chars"
    assert check_text("a" * 101, 100)[1] == "too_long"


def test_password_length_rules():
    assert check_password("a" * (PASSWORD_MIN - 1)) == "too_short"
    assert check_password("a" * PASSWORD_MIN) is None
    assert check_password("a" * PASSWORD_MAX_BYTES) is None
    assert check_password("a" * (PASSWORD_MAX_BYTES + 1)) == "too_long"
    # 按 UTF-8 字节计算：24 个汉字正好 72 字节，25 个超出
    assert check_password("密" * 24) is None
    assert check_password("密" * 25) == "too_long"
    assert check_password(None) == "too_short"
