"""
后端返回给前端的错误码 / 提示码，都必须在前端翻译文件里有对应文字。
否则前端 t(key) 找不到翻译，会把英文键名直接显示给用户。
同时禁止在返回值里直接写中文提示（英文界面会显示中文）。
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

BACKEND_DIRS = [ROOT / "poker" / "services", ROOT / "poker" / "routes", ROOT / "poker" / "core"]

KEY_PATTERNS = [
    re.compile(r'"(?:message|error_code)"\s*:\s*\(?\s*"([A-Za-z][A-Za-z0-9]+)"'),
    re.compile(r'_fail\(\s*"([A-Za-z][A-Za-z0-9]+)"'),
    # 三元表达式与校验函数里返回的错误码（只认驼峰命名，避免误伤普通字符串）
    re.compile(r'"([a-z]+[A-Z][A-Za-z0-9]*)"\s+if\s'),
    re.compile(r'else\s+"([a-z]+[A-Z][A-Za-z0-9]*)"'),
    re.compile(r'return\s+"([a-z]+[A-Z][A-Za-z0-9]*)"'),
]

CHINESE_MESSAGE = re.compile(r'"(?:message|error_code)"\s*:\s*"[^"]*[一-鿿]')


def _backend_files():
    for directory in BACKEND_DIRS:
        yield from directory.rglob("*.py")


def _backend_keys():
    keys = {}
    for path in _backend_files():
        text = path.read_text(encoding="utf-8")
        for pattern in KEY_PATTERNS:
            for match in pattern.finditer(text):
                keys.setdefault(match.group(1), path.relative_to(ROOT).as_posix())
    return keys


def _translation_keys():
    keys = set()
    for path in (ROOT / "poker" / "static" / "js" / "i18n").glob("*.js"):
        keys.update(re.findall(r"^\s*([A-Za-z0-9_]+)\s*:", path.read_text(encoding="utf-8"), re.M))
    return keys


def test_backend_finds_message_keys():
    # 防止正则写错导致下面的检查形同虚设
    assert len(_backend_keys()) > 80


def test_every_backend_message_has_a_translation():
    translations = _translation_keys()
    missing = {key: where for key, where in _backend_keys().items() if key not in translations}
    assert not missing, f"这些提示码在前端翻译文件里找不到：{missing}"


def test_no_hardcoded_chinese_messages():
    offenders = []
    for path in _backend_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if CHINESE_MESSAGE.search(line):
                offenders.append(f"{path.relative_to(ROOT).as_posix()}:{number}")
    assert not offenders, f"返回值里直接写了中文提示，请改成翻译键：{offenders}"
