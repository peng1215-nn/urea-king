"""
测试总配置。

- tests/unit：不需要数据库，任何环境都能跑。
- tests/integration：需要一个 **专用的测试库**，通过 TEST_DATABASE_URL 指定。
  没设置时集成测试会被跳过；库名里必须包含 "test"，因为每个测试前都会清空所有表。

必须在导入任何应用模块之前设置好环境变量，所以这些代码放在文件最上面。
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest


ROOT = Path(__file__).resolve().parent.parent

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "").strip()

if TEST_DATABASE_URL:
    # database.py 用的是 DATABASE_URL；load_dotenv 不会覆盖已存在的变量
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

os.environ.setdefault("SESSION_SECRET_KEY", "test-only-secret-key")
os.environ["APP_ENV"] = "test"

# 应用里的模板、静态文件目录都是相对仓库根目录的路径
os.chdir(ROOT)


def _is_test_database(url):
    name = urlsplit(url).path.lstrip("/")
    return "test" in name.lower()


def pytest_configure(config):
    if TEST_DATABASE_URL and not _is_test_database(TEST_DATABASE_URL):
        pytest.exit(
            "TEST_DATABASE_URL 指向的库名必须包含 'test'（测试会清空所有表）。",
            returncode=2,
        )


def pytest_collection_modifyitems(config, items):
    if TEST_DATABASE_URL:
        return

    skip = pytest.mark.skip(reason="未设置 TEST_DATABASE_URL，跳过集成测试")
    for item in items:
        if "integration" in Path(str(item.fspath)).parts:
            item.add_marker(skip)
