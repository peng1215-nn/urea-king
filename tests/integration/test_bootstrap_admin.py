"""测试环境的第一个管理员账号。"""

DEFAULT_PASSWORD = "Passw0rd123"


def test_creates_admin_on_empty_database(client, login_as):
    from poker.scripts.bootstrap_admin import bootstrap_admin

    assert bootstrap_admin("stageadmin", "StagePassw0rd") == "created"

    result = client.post("/login", data={"username": "stageadmin", "password": "StagePassw0rd"}).json()
    assert result["success"] is True
    assert result["groups"][0]["role"] == "admin"
    assert result["groups"][0]["group_code"] == "0"


def test_does_nothing_when_an_admin_exists(factory):
    from poker.scripts.bootstrap_admin import bootstrap_admin

    group = factory.group("0", name="管理员")
    admin = factory.user("realadmin")
    factory.role(admin, group, "admin")

    assert bootstrap_admin("otheradmin", "StagePassw0rd") == "skipped_exists"


def test_rejects_bad_input(factory):
    from poker.scripts.bootstrap_admin import bootstrap_admin

    assert bootstrap_admin("1bad", "StagePassw0rd") == "invalid_username"
    assert bootstrap_admin("stageadmin", "short") == "invalid_password"

    factory.user("taken01")
    assert bootstrap_admin("taken01", "StagePassw0rd") == "username_taken"


def test_main_skips_without_configuration(monkeypatch):
    from poker.scripts import bootstrap_admin

    monkeypatch.delenv("BOOTSTRAP_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    assert bootstrap_admin.main() == 0
