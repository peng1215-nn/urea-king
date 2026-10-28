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
        assert response.json()["error_code"] == "loginInvalidCredentials"

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
        "email": "newuser1@example.com",
        "password": "GoodPass123",
        "confirm_password": "GoodPass123",
        "invite_code": "INVITE1",
    }
    data.update(overrides)
    return client.post("/register", data=data)


def _verify_email_for(username):
    """直接在数据库中标记用户邮箱已验证（测试环境无法真实发邮件）"""
    from database import SessionLocal
    from poker.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.email_verified = 1
            db.commit()
    finally:
        db.close()


def test_register_with_invite_code_then_login(client, factory):
    factory.group("G1")
    factory.invite("INVITE1", "G1", role="user")

    response = _register(client)
    assert response.json()["success"] is True, response.json()

    _verify_email_for("newuser1")

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
    from core import middleware

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


def test_spoofed_forwarded_for_does_not_bypass_username_limit(client, factory):
    user_id = factory.user("erin001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    # 每次伪造不同的来源 IP，单个“IP+用户名”的计数永远到不了 5 次
    for i in range(20):
        client.post(
            "/login",
            data={"username": "erin001", "password": "wrong-password"},
            headers={"x-forwarded-for": f"10.0.0.{i}"},
        )

    response = client.post(
        "/login",
        data={"username": "erin001", "password": "wrong-password"},
        headers={"x-forwarded-for": "10.0.1.1"},
    )
    assert response.status_code == 429


def test_owner_is_not_locked_out_by_someone_else_guessing(client, factory):
    user_id = factory.user("frank01")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    # 账号主人先在自己的设备上正常登录过一次
    assert client.post("/login", data={"username": "frank01", "password": DEFAULT_PASSWORD}).json()["success"] is True

    # 别人轮换伪造的 IP 乱试密码
    for i in range(20):
        client.post(
            "/login",
            data={"username": "frank01", "password": "wrong-password"},
            headers={"x-forwarded-for": f"10.1.0.{i}"},
        )

    # 陌生来源被挡住，账号主人的设备照常登录
    stranger = client.post(
        "/login",
        data={"username": "frank01", "password": DEFAULT_PASSWORD},
        headers={"x-forwarded-for": "10.2.0.1"},
    )
    assert stranger.status_code == 429

    owner = client.post("/login", data={"username": "frank01", "password": DEFAULT_PASSWORD})
    assert owner.json()["success"] is True


def test_group_join_password_guessing_counts_toward_login_limit(client, factory):
    user_id = factory.user("gina001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    for _ in range(5):
        response = client.post(
            "/group-join",
            data={"username": "gina001", "password": "wrong-password", "invite_code": "ANY"},
        )
        assert response.json()["message"] == "groupJoinAccountInvalid"

    response = client.post("/login", data={"username": "gina001", "password": DEFAULT_PASSWORD})
    assert response.status_code == 429


# ───────────── 不暴露用户名是否存在 ─────────────

def test_unknown_user_and_wrong_password_get_same_message(client, factory):
    user_id = factory.user("henry01")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    unknown = client.post("/login", data={"username": "nobody99", "password": "whatever1"}).json()
    wrong = client.post("/login", data={"username": "henry01", "password": "wrong-password"}).json()

    assert unknown == wrong == {"success": False, "error_code": "loginInvalidCredentials"}


def test_unknown_user_attempts_are_rate_limited_too(client):
    for _ in range(5):
        client.post("/login", data={"username": "nobody99", "password": "whatever1"})

    assert client.post("/login", data={"username": "nobody99", "password": "whatever1"}).status_code == 429


# ───────────── 改密码后其他设备的登录失效 ─────────────

def _second_client():
    from fastapi.testclient import TestClient

    import main

    return TestClient(main.app, base_url="http://localhost")


def _login(test_client, username, group_id, password=DEFAULT_PASSWORD):
    assert test_client.post("/login", data={"username": username, "password": password}).json()["success"] is True
    assert test_client.post("/select-group", data={"group_id": group_id}).json()["success"] is True


def test_changing_password_logs_out_other_devices(client, factory):
    user_id = factory.user("ivan001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    phone = _second_client()
    _login(client, "ivan001", group_id)
    _login(phone, "ivan001", group_id)
    assert phone.get("/current-user").json()["success"] is True

    result = client.post(
        "/user/change-password/update-password",
        data={
            "current_password": DEFAULT_PASSWORD,
            "new_password": "NewPassw0rd9",
            "confirm_password": "NewPassw0rd9",
        },
    ).json()
    assert result["success"] is True, result

    # 另一台设备上的旧登录立即失效
    response = phone.get("/current-user")
    assert response.status_code == 401
    assert response.json()["message"] == "sessionExpired"

    # 用新密码重新登录正常
    _login(phone, "ivan001", group_id, password="NewPassw0rd9")
    assert phone.get("/current-user").json()["success"] is True


def test_admin_password_reset_logs_out_the_user(client, factory, login_as):
    admin_group = factory.group("0", name="管理员")
    admin_id = factory.user("admin001")
    factory.role(admin_id, admin_group, "admin")

    user_id = factory.user("judy001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")

    user_device = _second_client()
    _login(user_device, "judy001", group_id)
    assert user_device.get("/current-user").json()["success"] is True

    login_as("admin001", admin_group)
    assert client.post("/admin/reset-user-password", data={"target_user_id": user_id}).json()["success"] is True

    assert user_device.get("/current-user").status_code == 401


def test_session_without_password_fingerprint_is_rejected(client, factory, login_as):
    """部署前签发的旧会话里没有密码指纹，应要求重新登录一次。"""
    from core import middleware

    user_id = factory.user("kate001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")
    login_as("kate001", group_id)

    from poker.core.session import session_is_valid

    middleware.clear_session_cache()
    assert session_is_valid((user_id, group_id, "user", None)) is False
