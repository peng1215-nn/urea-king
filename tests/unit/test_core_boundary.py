"""core/ 是所有模块共用的基础代码，不能反过来依赖任何模块。"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULES = ("poker", "root")


def test_core_does_not_import_modules():
    pattern = re.compile(r"^\s*(?:from|import)\s+(" + "|".join(MODULES) + r")\b", re.M)
    offenders = [
        f"{path.relative_to(ROOT).as_posix()}: {m.group(0).strip()}"
        for path in (ROOT / "core").glob("*.py")
        for m in pattern.finditer(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, "\n".join(offenders)
