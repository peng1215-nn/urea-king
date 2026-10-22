"""
从系统 NotoSansCJK TTC 中提取简中字体，输出到 poker/static/fonts/。
部署新环境时运行一次即可：
    python3 scripts/extract_fonts.py
依赖：pip install fonttools
"""
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "poker" / "static" / "fonts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = [
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2, "NotoSansSC-Regular.ttf"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",    2, "NotoSansSC-Bold.ttf"),
]

try:
    from fontTools.ttLib import TTCollection
except ImportError:
    raise SystemExit("请先安装 fonttools：pip install fonttools")

for src_path, index, out_name in SOURCES:
    out_path = OUTPUT_DIR / out_name
    if out_path.exists():
        print(f"已存在，跳过：{out_name}")
        continue
    if not os.path.exists(src_path):
        print(f"系统字体不存在，跳过：{src_path}")
        continue
    print(f"提取 {src_path} [index={index}] → {out_name} ...")
    ttc = TTCollection(src_path)
    ttc.fonts[index].save(str(out_path))
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"  完成，{size_mb:.1f} MB")

print("字体提取完毕。")
