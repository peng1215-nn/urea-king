"""
集成测试的数据库与客户端。

注意：本目录下的测试文件不要在模块顶层导入应用代码（database、main、poker.*），
因为没设置 TEST_DATABASE_URL 时它们会被跳过，但收集阶段仍会导入模块。
"""

from datetime import datetime
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


DEFAULT_PASSWORD = "Passw0rd123"


@pytest.fixture(scope="session")
def migrated_db():
    """用真实的迁移脚本把测试库升级到最新，同时验证迁移本身能在空库上跑通。"""
    from alembic import command
    from alembic.config import Config

    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def clean_state(migrated_db):
    from sqlalchemy import text

    from database import Base, engine
    from core import middleware
    from poker.core import rate_limit
    import poker.models  # noqa: F401  确保所有表都注册进 metadata

    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))

    for limiter in (
        rate_limit.login_failures_by_account,
        rate_limit.login_failures_by_ip,
        rate_limit.register_failures_by_ip,
        rate_limit.group_join_failures_by_ip,
        rate_limit.login_failures_by_username,
        rate_limit.invite_failures_global,
        rate_limit.resend_verify_failures_by_ip,
        rate_limit.forgot_password_failures_by_ip,
        rate_limit.reset_password_failures_by_ip,
        rate_limit.avatar_uploads_by_user,
        rate_limit.invite_creates_by_user,
        rate_limit.current_password_failures_by_user,
        rate_limit.change_email_by_ip,
    ):
        limiter._events.clear()

    rate_limit.clear_trusted_logins()
    middleware.clear_session_cache()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    import main

    # Host 必须是 localhost：domain_router 会把其它主机名的请求跳转回首页
    with TestClient(main.app, base_url="http://localhost") as test_client:
        yield test_client


class Factory:
    """直接往测试库里造数据，绕过页面流程，让测试只关注被测的那一件事。"""

    def __init__(self):
        from core.security import pwd_context

        self._pwd = pwd_context

    def _session(self):
        from database import SessionLocal

        return SessionLocal()

    def user(self, username, password=DEFAULT_PASSWORD, nickname=None, is_active=1):
        from poker.models import User

        db = self._session()
        try:
            user = User(
                username=username,
                password_hash=self._pwd.hash(password),
                nickname=nickname or username,
                is_active=is_active,
                email_verified=1,
            )
            db.add(user)
            db.commit()
            return user.id
        finally:
            db.close()

    def group(self, code, name=None):
        from poker.models import Group

        db = self._session()
        try:
            group = Group(group_code=code, group_name=name or code)
            db.add(group)
            db.commit()
            return group.id
        finally:
            db.close()

    def role(self, user_id, group_id, role):
        from poker.models import UserGroupRole

        db = self._session()
        try:
            db.add(UserGroupRole(user_id=user_id, group_id=group_id, role=role))
            db.commit()
        finally:
            db.close()

    def invite(self, code, group_code, role="user"):
        from poker.models import InvitationCode

        db = self._session()
        try:
            db.add(InvitationCode(code=code, group_code=group_code, role=role))
            db.commit()
        finally:
            db.close()

    def finished_game(self, group_id, organizer_id, name):
        from poker.models import PokerGame

        db = self._session()
        try:
            now = datetime(2026, 1, 1, 20, 0, 0)
            game = PokerGame(
                group_id=group_id,
                organizer_id=organizer_id,
                status="finished",
                name=name,
                started_at=now,
                ended_at=now,
                total_buy_in=0,
                total_cash_out=0,
                is_balanced=1,
                player_count=0,
            )
            db.add(game)
            db.commit()
            return game.id
        finally:
            db.close()

    def set_user_active(self, user_id, is_active):
        from poker.models import User

        db = self._session()
        try:
            db.query(User).filter(User.id == user_id).update({"is_active": is_active})
            db.commit()
        finally:
            db.close()

    def remove_roles(self, user_id, group_id):
        from poker.models import UserGroupRole

        db = self._session()
        try:
            db.query(UserGroupRole).filter(
                UserGroupRole.user_id == user_id,
                UserGroupRole.group_id == group_id,
            ).delete()
            db.commit()
        finally:
            db.close()


@pytest.fixture
def factory():
    return Factory()


@pytest.fixture
def login_as(client):
    """登录并选择组，返回 select-group 的结果。"""

    def _login(username, group_id, password=DEFAULT_PASSWORD):
        response = client.post("/login", data={"username": username, "password": password})
        assert response.status_code == 200, response.text
        assert response.json()["success"] is True, response.json()

        response = client.post("/select-group", data={"group_id": group_id})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["success"] is True, result
        return result

    return _login
