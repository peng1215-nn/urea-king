"""
安全策略禁止内联脚本。这里检查页面和前端代码里没有重新写回：
- onclick="..." 这类内联事件；
- 没有 src 的 <script> 块；
- javascript: 链接；
并检查 data-on-* 指向的函数确实存在（否则按钮会点了没反应）。
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

TEMPLATES = list((ROOT / "poker" / "templates").rglob("*.html")) + list((ROOT / "root" / "templates").rglob("*.html"))
SCRIPTS = list((ROOT / "poker" / "static" / "js").rglob("*.js")) + list((ROOT / "root" / "static" / "js").rglob("*.js"))
DISPATCHER = ROOT / "poker" / "static" / "js" / "common" / "actions.js"

INLINE_HANDLER = re.compile(
    r"\son(click|dblclick|change|input|submit|keyup|keydown|keypress|mouseover|mouseout|mouseenter|"
    r"mouseleave|focus|blur|load|error|scroll|resize)\s*=\s*[\"']",
    re.I,
)
INLINE_SCRIPT = re.compile(r"<script(?![^>]*\ssrc=)[^>]*>", re.I)
JS_URL = re.compile(r"""href\s*=\s*["']\s*javascript:""", re.I)
ACTION = re.compile(r"""data-on-(?:click|change|input)\s*=\s*["']([A-Za-z_$][\w$]*)["']""")
FUNCTION_DECL = re.compile(r"(?:^|[\s;])(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", re.M)


def _read(path):
    return path.read_text(encoding="utf-8")


def _rel(path):
    return path.relative_to(ROOT).as_posix()


def test_no_inline_event_handlers():
    offenders = [
        f"{_rel(path)}: {m.group(0).strip()}"
        for path in TEMPLATES + SCRIPTS
        if path != DISPATCHER
        for m in INLINE_HANDLER.finditer(_read(path))
    ]
    assert not offenders, "请改用 data-on-click 等属性（见 actions.js）：\n" + "\n".join(offenders)


def test_no_inline_script_blocks():
    offenders = [_rel(path) for path in TEMPLATES if INLINE_SCRIPT.search(_read(path))]
    assert not offenders, "请把脚本移到 static/js 下的文件：" + ", ".join(offenders)


def test_no_javascript_urls():
    offenders = [_rel(path) for path in TEMPLATES + SCRIPTS if JS_URL.search(_read(path))]
    assert not offenders, ", ".join(offenders)


def test_every_action_has_a_function():
    defined = set()
    for path in SCRIPTS:
        defined.update(FUNCTION_DECL.findall(_read(path)))

    missing = sorted(
        f"{_rel(path)}: {name}"
        for path in TEMPLATES + SCRIPTS
        for name in ACTION.findall(_read(path))
        if name not in defined
    )
    assert len(defined) > 100
    assert not missing, "data-on-* 指向的函数不存在：\n" + "\n".join(missing)


def test_pages_with_actions_load_the_dispatcher():
    for path in TEMPLATES:
        text = _read(path)
        # 被其他页面 include 的片段，由所在页面加载 actions.js
        if path.name in ("sidebar.html", "language_switcher.html", "account_email_card.html") or "root" in path.parts[-3:-1]:
            continue
        assert "/static/js/common/actions.js" in text, _rel(path)
