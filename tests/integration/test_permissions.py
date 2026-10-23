DEFAULT_PASSWORD = "Passw0rd123"


def _member(factory, username, group_id, role):
    user_id = factory.user(username)
    factory.role(user_id, group_id, role)
    return user_id


def test_regular_user_cannot_call_admin_api(client, factory, login_as):
    group_id = factory.group("G1")
    _member(factory, "user0001", group_id, "user")
    login_as("user0001", group_id)

    assert client.get("/admin/audit-logs").json() == {"success": False, "message": "permissionDenied"}


def test_organizer_cannot_call_admin_api(client, factory, login_as):
    group_id = factory.group("G1")
    _member(factory, "org00001", group_id, "organizer")
    login_as("org00001", group_id)

    assert client.get("/admin/audit-logs").json()["success"] is False


def test_regular_user_cannot_call_organizer_api(client, factory, login_as):
    group_id = factory.group("G1")
    _member(factory, "user0002", group_id, "user")
    login_as("user0002", group_id)

    assert client.get("/organizer/game-log/list").json() == {"success": False, "message": "permissionDenied"}


def test_admin_can_read_audit_logs(client, factory, login_as):
    group_id = factory.group("ADMIN")
    _member(factory, "admin001", group_id, "admin")
    login_as("admin001", group_id)

    assert client.get("/admin/audit-logs").json()["success"] is True


def test_organizer_only_sees_games_of_own_group(client, factory, login_as):
    group_a = factory.group("GA")
    group_b = factory.group("GB")
    org_a = _member(factory, "orga0001", group_a, "organizer")
    org_b = _member(factory, "orgb0001", group_b, "organizer")
    factory.finished_game(group_a, org_a, "A 组的牌局")
    factory.finished_game(group_b, org_b, "B 组的牌局")

    login_as("orga0001", group_a)
    data = client.get("/organizer/game-log/list").json()

    assert data["success"] is True
    assert [game["name"] for game in data["games"]] == ["A 组的牌局"]


def test_cannot_select_a_group_you_do_not_belong_to(client, factory):
    group_a = factory.group("GA")
    group_b = factory.group("GB")
    _member(factory, "user0003", group_a, "user")

    client.post("/login", data={"username": "user0003", "password": DEFAULT_PASSWORD})
    response = client.post("/select-group", data={"group_id": group_b})

    assert response.json()["success"] is False
    assert response.json()["error_code"] == "groupAccessDenied"


def test_removed_organizer_loses_access(client, factory, login_as):
    from poker.core import middleware

    group_id = factory.group("G1")
    org_id = _member(factory, "org00002", group_id, "organizer")
    login_as("org00002", group_id)
    assert client.get("/organizer/game-log/list").json()["success"] is True

    factory.remove_roles(org_id, group_id)
    middleware.clear_session_cache()

    assert client.get("/organizer/game-log/list").status_code == 401


def test_admin_password_reset_uses_random_temporary_password(client, factory, login_as):
    admin_group = factory.group("ADMIN")
    _member(factory, "admin002", admin_group, "admin")
    player_group = factory.group("G1")
    target_id = _member(factory, "target01", player_group, "user")

    login_as("admin002", admin_group)
    result = client.post("/admin/reset-user-password", data={"target_user_id": target_id}).json()

    assert result["success"] is True
    temporary = result["temporary_password"]
    assert len(temporary) == 10
    assert temporary != "000000"

    # 临时密码不能出现在审计日志里
    logs = client.get("/admin/audit-logs", params={"page_size": 20}).json()["logs"]
    assert all(temporary not in str(log) for log in logs)

    client.get("/logout")
    response = client.post("/login", data={"username": "target01", "password": temporary})
    assert response.json()["success"] is True
