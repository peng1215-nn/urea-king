DEFAULT_PASSWORD = "Passw0rd123"


def test_login_and_select_group(client, factory, login_as):
    user_id = factory.user("alice01")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    result = login_as("alice01", group_id)

    assert result["role"] == "user"
    assert result["redirect_url"] == "/user-dashboard"


def test_wrong_password_is_rate_limited(client, factory):
    user_id = factory.user("bob001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    for _ in range(5):
        response = client.post("/login", data={"username": "bob001", "password": "wrong-password"})
        assert response.json()["error_code"] == "loginPasswordIncorrect"

    response = client.post("/login", data={"username": "bob001", "password": "wrong-password"})
    assert response.status_code == 429
    assert response.json()["error_code"] == "loginTooManyAttempts"

    # 被锁期间，即使密码正确也要等
    response = client.post("/login", data={"username": "bob001", "password": DEFAULT_PASSWORD})
    assert response.status_code == 429


def test_successful_login_resets_failure_counter(client, factory):
    user_id = factory.user("carol01")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    for _ in range(4):
        client.post("/login", data={"username": "carol01", "password": "wrong-password"})

    assert client.post("/login", data={"username": "carol01", "password": DEFAULT_PASSWORD}).json()["success"] is True

    for _ in range(4):
        response = client.post("/login", data={"username": "carol01", "password": "wrong-password"})
        assert response.status_code == 200


def _register(client, **overrides):
    data = {
        "username": "newuser1",
        "nickname": "新玩家",
        "password": "GoodPass123",
        "confirm_password": "GoodPass123",
        "invite_code": "INVITE1",
    }
    data.update(overrides)
    return client.post("/register", data=data)


def test_register_with_invite_code_then_login(client, factory):
    factory.group("G1")
    factory.invite("INVITE1", "G1", role="user")

    response = _register(client)
    assert response.json()["success"] is True, response.json()

    response = client.post("/login", data={"username": "newuser1", "password": "GoodPass123"})
    assert response.json()["success"] is True


def test_register_rejects_html_in_nickname(client, factory):
    factory.group("G1")
    factory.invite("INVITE1", "G1")

    response = _register(client, nickname="<img src=x onerror=alert(1)>")
    assert response.json()["error_code"] == "registerNicknameInvalid"

    # 邀请码没有被消耗，正常昵称仍可注册
    assert _register(client).json()["success"] is True


def test_register_rejects_short_password(client, factory):
    factory.group("G1")
    factory.invite("INVITE1", "G1")

    response = _register(client, password="Short12", confirm_password="Short12")
    assert response.json()["error_code"] == "registerPasswordTooShort"


def test_disabled_user_loses_access_immediately(client, factory, login_as):
    from poker.core import middleware

    user_id = factory.user("dave001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")
    login_as("dave001", group_id)

    assert client.get("/current-user").json()["success"] is True

    factory.set_user_active(user_id, 0)
    middleware.clear_session_cache()  # 线上最多 15 秒后生效

    response = client.get("/current-user")
    assert response.status_code == 401
    assert response.json()["message"] == "sessionExpired"
