"""资料页、头像、组名、管理员改身份：整理代码结构后行为保持不变。"""

DEFAULT_PASSWORD = "Passw0rd123"

PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _setup(factory):
    group_id = factory.group("G1", name="周五局")
    org = factory.user("orgaaaa1")
    factory.role(org, group_id, "organizer")
    user = factory.user("alice001")
    factory.role(user, group_id, "user")
    return group_id, org, user


def test_select_group_returns_role_and_home(client, factory, login_as):
    group_id, _, _ = _setup(factory)
    result = login_as("orgaaaa1", group_id)
    assert result == {"success": True, "role": "organizer", "redirect_url": "/organizer-dashboard"}


def test_select_group_requires_login_and_membership(client, factory):
    group_id, _, _ = _setup(factory)
    other = factory.group("G2")

    assert client.post("/select-group", data={"group_id": group_id}).json()["error_code"] == "loginRequired"

    client.post("/login", data={"username": "alice001", "password": DEFAULT_PASSWORD})
    assert client.post("/select-group", data={"group_id": other}).json()["error_code"] == "groupAccessDenied"


def test_avatar_upload_validation(client, factory, login_as):
    group_id, _, _ = _setup(factory)

    response = client.post("/upload-avatar", files={"avatar": ("a.png", PNG_HEADER, "image/png")})
    assert response.json()["message"] in ("notLoggedIn", "sessionExpired")

    login_as("alice001", group_id)
    response = client.post("/upload-avatar", files={"avatar": ("a.png", b"not an image", "image/png")})
    assert response.json() == {"success": False, "message": "avatarInvalidType"}


def test_nickname_and_password_shared_by_all_roles(client, factory, login_as):
    group_id, _, _ = _setup(factory)

    login_as("orgaaaa1", group_id)
    result = client.post("/organizer/change-password/update-nickname", data={"nickname": "老板"}).json()
    assert result["success"] is True, result
    assert client.get("/organizer/change-password/current").json()["user"]["nickname"] == "老板"

    client.get("/logout")
    login_as("alice001", group_id)
    result = client.post("/user/change-password/update-nickname", data={"nickname": "老板"}).json()
    assert result == {"success": False, "message": "nicknameExists"}

    result = client.post(
        "/user/change-password/update-password",
        data={"current_password": "wrong-pass", "new_password": "NewPassw0rd9", "confirm_password": "NewPassw0rd9"},
    ).json()
    assert result["message"] == "currentPasswordIncorrect"


def test_organizer_group_name_uses_shared_validation(client, factory, login_as):
    group_id, _, _ = _setup(factory)
    login_as("orgaaaa1", group_id)

    assert client.post("/organizer/update-group-name", data={"group_name": "<b>坏</b>"}).json()["message"] == "groupNameInvalid"
    assert client.post("/organizer/update-group-name", data={"group_name": "x" * 51}).json()["message"] == "groupNameTooLong"
    assert client.post("/organizer/update-group-name", data={"group_name": "   "}).json()["message"] == "groupNameRequired"

    result = client.post("/organizer/update-group-name", data={"group_name": "周六局"}).json()
    assert result == {"success": True, "message": "groupNameUpdateSuccess"}
    assert client.get("/organizer/group-info").json()["group_name"] == "周六局"


def test_admin_messages_are_translation_keys(client, factory, login_as):
    group_id, _, user = _setup(factory)
    admin_group = factory.group("0", name="管理员")
    admin = factory.user("admin001")
    factory.role(admin, admin_group, "admin")
    login_as("admin001", admin_group)

    result = client.post(
        "/admin/update-user-role",
        data={"target_user_id": user, "group_id": group_id, "role": "superuser"},
    ).json()
    assert result == {"success": False, "message": "roleInvalid"}

    result = client.post("/admin/reset-user-password", data={"target_user_id": admin}).json()
    assert result == {"success": False, "message": "adminPasswordResetForbidden"}


def test_user_pages_still_served(client, factory, login_as):
    group_id, _, _ = _setup(factory)
    login_as("alice001", group_id)

    for path in ("/user-announcements", "/user-change-password", "/user-game-logs"):
        response = client.get(path, headers={"accept": "text/html"})
        assert response.status_code == 200, path

    assert client.get("/user/announcements").json()["success"] is True
    assert client.get("/user/game-log/stats").json()["success"] is True
