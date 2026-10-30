"""账号相关的防护：改邮箱、找回密码、重发验证、修改密码、邀请码、备注名。"""

import pytest

DEFAULT_PASSWORD = "Passw0rd123"


@pytest.fixture(autouse=True)
def no_real_email(monkeypatch):
    """不真正发邮件，记录发出的链接 token。"""
    sent = []
    from poker.services.auth import change_email, resend_verify, reset_password

    monkeypatch.setattr(change_email, "send_verify_email", lambda to, token: sent.append((to, token)) or True)
    monkeypatch.setattr(resend_verify, "send_verify_email", lambda to, token: sent.append((to, token)) or True)
    monkeypatch.setattr(reset_password, "send_reset_password", lambda to, token: sent.append((to, token)) or True)
    return sent


def _set_user(user_id, **fields):
    from database import SessionLocal
    from poker.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        for key, value in fields.items():
            setattr(user, key, value)
        db.commit()
    finally:
        db.close()


def _unverified_user(factory, username, email):
    user_id = factory.user(username)
    _set_user(user_id, email=None, pending_email=email, email_verified=0)
    return user_id


def _verify_tokens(user_id):
    from database import SessionLocal
    from poker.models import EmailVerification

    db = SessionLocal()
    try:
        return [
            (r.token, r.used)
            for r in db.query(EmailVerification).filter(
                EmailVerification.user_id == user_id,
                EmailVerification.purpose == "verify_email",
            ).order_by(EmailVerification.id)
        ]
    finally:
        db.close()


def _add_verify_token(user_id, token):
    from datetime import timedelta

    from core.time import now_columbus_naive
    from database import SessionLocal
    from poker.models import EmailVerification

    db = SessionLocal()
    try:
        now = now_columbus_naive()
        db.add(EmailVerification(
            user_id=user_id,
            token=token,
            purpose="verify_email",
            expires_at=now + timedelta(minutes=15),
            used=0,
            created_at=now - timedelta(minutes=10),
        ))
        db.commit()
    finally:
        db.close()


# ───────────────────────── 改邮箱 ─────────────────────────

def test_change_email_wrong_password_is_rate_limited(client, factory):
    _unverified_user(factory, "eve00001", "eve@example.com")
    form = {"username": "eve00001", "password": "wrong-password", "new_email": "new@example.com"}

    for _ in range(5):
        assert client.post("/change-email", data=form).json()["error_code"] == "changeEmailWrongCredentials"

    response = client.post("/change-email", data=form)
    assert response.status_code == 429
    assert response.json()["error_code"] == "changeEmailTooManyAttempts"


def test_changing_email_invalidates_old_verification_links(client, factory):
    user_id = _unverified_user(factory, "eve00002", "own@example.com")
    _add_verify_token(user_id, "old-link-token")

    result = client.post(
        "/change-email",
        data={"username": "eve00002", "password": DEFAULT_PASSWORD, "new_email": "other@example.com"},
    ).json()
    assert result["success"] is True

    tokens = dict(_verify_tokens(user_id))
    assert tokens["old-link-token"] == 1

    from poker.services.auth.register import verify_email_service

    assert verify_email_service("old-link-token")["error_code"] == "verifyTokenUsed"


# ───────────────────────── 不暴露邮箱是否注册 ─────────────────────────

def test_resend_verify_gives_same_reply_for_verified_and_unknown_emails(client, factory, no_real_email):
    user_id = factory.user("ver00001")
    _set_user(user_id, email="verified@example.com")

    known = client.post("/resend-verify-email", data={"email": "verified@example.com"}).json()
    unknown = client.post("/resend-verify-email", data={"email": "nobody@example.com"}).json()

    assert known == unknown == {"success": True, "error_code": "resendSent"}
    assert no_real_email == []


def test_forgot_password_repeat_request_gives_same_reply(client, factory, no_real_email):
    user_id = factory.user("fp000001")
    _set_user(user_id, email="fp@example.com")

    first = client.post("/forgot-password", data={"email": "fp@example.com"}).json()
    second = client.post("/forgot-password", data={"email": "fp@example.com"}).json()

    assert first == second == {"success": True}
    # 5 分钟内只发一封
    assert len(no_real_email) == 1


def test_successful_reset_invalidates_other_reset_links(client, factory, no_real_email):
    from datetime import timedelta

    from core.time import now_columbus_naive
    from database import SessionLocal
    from poker.models import EmailVerification

    user_id = factory.user("fp000002")
    db = SessionLocal()
    try:
        now = now_columbus_naive()
        for token in ("reset-a", "reset-b"):
            db.add(EmailVerification(
                user_id=user_id, token=token, purpose="reset_password",
                expires_at=now + timedelta(minutes=15), used=0,
            ))
        db.commit()
    finally:
        db.close()

    form = {"token": "reset-a", "new_password": "newpass123", "confirm_password": "newpass123"}
    assert client.post("/reset-password", data=form).json()["success"] is True

    form["token"] = "reset-b"
    assert client.post("/reset-password", data=form).json()["error_code"] == "resetTokenUsed"


# ───────────────────────── 修改密码 ─────────────────────────

def test_wrong_current_password_is_rate_limited(client, factory, login_as):
    user_id = factory.user("cp000001")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")
    login_as("cp000001", group_id)

    form = {"current_password": "wrong-password", "new_password": "newpass123", "confirm_password": "newpass123"}
    for _ in range(5):
        result = client.post("/user/change-password/update-password", data=form).json()
        assert result["message"] == "currentPasswordIncorrect"

    form["current_password"] = DEFAULT_PASSWORD
    result = client.post("/user/change-password/update-password", data=form).json()
    assert result["message"] == "currentPasswordTooManyAttempts"


def test_password_over_72_bytes_is_rejected_cleanly(client, factory, login_as):
    user_id = factory.user("cp000002")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")
    login_as("cp000002", group_id)

    long_password = "密" * 25  # 75 字节
    form = {"current_password": DEFAULT_PASSWORD, "new_password": long_password, "confirm_password": long_password}
    result = client.post("/user/change-password/update-password", data=form).json()
    assert result["message"] == "newPasswordTooLong"


# ───────────────────────── 局头：邀请码、备注名 ─────────────────────────

def _organizer(factory, login_as, username="org00001", code="G1"):
    org = factory.user(username)
    group_id = factory.group(code)
    factory.role(org, group_id, "organizer")
    login_as(username, group_id)
    return org, group_id


def test_invite_code_creation_is_rate_limited(client, factory, login_as):
    _organizer(factory, login_as)

    for i in range(20):
        client.post("/organizer/invite/create", data={"code": f"probe-{i}"})

    response = client.post("/organizer/invite/create", data={"code": "probe-last"})
    assert response.status_code == 429
    assert response.json()["message"] == "inviteCreateTooFrequent"


def test_alias_only_for_group_members(client, factory, login_as):
    _, group_id = _organizer(factory, login_as)
    member = factory.user("mem00001")
    factory.role(member, group_id, "user")
    outsider = factory.user("out00001")

    ok = client.post("/organizer/save-member-alias", data={"target_user_id": member, "alias": "小明"}).json()
    assert ok["success"] is True

    rejected = client.post("/organizer/save-member-alias", data={"target_user_id": outsider, "alias": "路人"}).json()
    assert rejected["message"] == "memberNotInGroup"


def test_weak_new_password_is_rejected(client, factory, login_as):
    user_id = factory.user("cp000003")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")
    login_as("cp000003", group_id)

    form = {"current_password": DEFAULT_PASSWORD, "new_password": "12345678", "confirm_password": "12345678"}
    result = client.post("/user/change-password/update-password", data=form).json()
    assert result["message"] == "newPasswordTooWeak"



def test_group_join_requires_verified_email(client, factory):
    user_id = factory.user("unv00001")
    _set_user(user_id, email_verified=0)
    factory.group("G9")
    factory.invite("JOINCODE9", "G9")

    result = client.post(
        "/group-join",
        data={"invite_code": "JOINCODE9", "username": "unv00001", "password": DEFAULT_PASSWORD},
    ).json()
    assert result["message"] == "groupJoinEmailNotVerified"


def test_successful_registrations_are_rate_limited(client, monkeypatch):
    from poker.services.auth import register

    monkeypatch.setattr(register, "send_verify_email", lambda to, token: True)

    for i in range(10):
        response = client.post("/register", data={
            "username": f"spam{i:04d}", "nickname": f"spam{i}", "email": f"spam{i}@example.com",
            "password": "GoodPass123", "confirm_password": "GoodPass123",
        })
        assert response.status_code == 200, response.text

    response = client.post("/register", data={
        "username": "spam9999", "nickname": "spam9999", "email": "spam9999@example.com",
        "password": "GoodPass123", "confirm_password": "GoodPass123",
    })
    assert response.status_code == 429


def test_changing_password_invalidates_pending_reset_links(client, factory, login_as):
    from datetime import timedelta

    from core.time import now_columbus_naive
    from database import SessionLocal
    from poker.models import EmailVerification

    user_id = factory.user("cp000004")
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")
    db = SessionLocal()
    try:
        db.add(EmailVerification(
            user_id=user_id, token="pending-reset", purpose="reset_password",
            expires_at=now_columbus_naive() + timedelta(minutes=15), used=0,
        ))
        db.commit()
    finally:
        db.close()

    login_as("cp000004", group_id)
    form = {"current_password": DEFAULT_PASSWORD, "new_password": "newpass123", "confirm_password": "newpass123"}
    assert client.post("/user/change-password/update-password", data=form).json()["success"] is True

    reset = {"token": "pending-reset", "new_password": "another123", "confirm_password": "another123"}
    assert client.post("/reset-password", data=reset).json()["error_code"] == "resetTokenUsed"


def test_validation_errors_do_not_echo_input(client, factory, login_as):
    org = factory.user("org00009")
    group_id = factory.group("G1")
    factory.role(org, group_id, "organizer")
    login_as("org00009", group_id)

    response = client.post("/organizer/game/organizer-buyin", data={"game_id": "abc", "amount": "secret-value"})
    assert response.status_code == 422
    assert response.json() == {"success": False, "message": "invalidRequest"}
    assert "secret-value" not in response.text


# ───────────────────────── 第七轮：邀请码、邮箱、昵称、申请 ─────────────────────────

def test_invite_codes_are_generated_and_case_insensitive(client, factory, login_as):
    from poker.services.common.invite_codes import ALPHABET, CODE_LENGTH

    _organizer(factory, login_as, username="org00021", code="G21")
    created = client.post("/organizer/invite/create", data={"code": "abc"}).json()
    assert created["success"] is True
    code = created["code"]["code"]
    assert code != "abc"
    assert len(code) == CODE_LENGTH and all(ch in ALPHABET for ch in code)

    client.get("/logout")
    joiner = factory.user("join0021")
    assert joiner
    result = client.post(
        "/group-join",
        data={"invite_code": code.lower(), "username": "join0021", "password": DEFAULT_PASSWORD},
    ).json()
    assert result["success"] is True, result


def test_change_email_has_daily_limit(client, factory):
    from datetime import timedelta

    from core.time import now_columbus_naive
    from database import SessionLocal
    from poker.models import EmailVerification

    user_id = _unverified_user(factory, "eve00031", "own31@example.com")
    db = SessionLocal()
    try:
        now = now_columbus_naive()
        for i in range(5):
            db.add(EmailVerification(
                user_id=user_id, token=f"old-{i}", purpose="verify_email",
                expires_at=now, used=1, created_at=now - timedelta(hours=2 + i),
            ))
        db.commit()
    finally:
        db.close()

    result = client.post(
        "/change-email",
        data={"username": "eve00031", "password": DEFAULT_PASSWORD, "new_email": "x31@example.com"},
    ).json()
    assert result["error_code"] == "changeEmailDailyLimit"


def test_squatted_email_cannot_block_the_real_owner(client, monkeypatch):
    """别人先用你的邮箱注册（收不到验证邮件）也占不住：你照样能注册，先验证的归你。"""
    from database import SessionLocal
    from poker.models import EmailVerification, User
    from poker.services.auth import register
    from poker.services.auth.register import verify_email_service

    monkeypatch.setattr(register, "send_verify_email", lambda to, token: True)
    form = {"email": "victim@example.com", "password": "GoodPass123", "confirm_password": "GoodPass123"}

    assert client.post("/register", data={**form, "username": "squatter1", "nickname": "squat"}).json()["success"] is True
    # 抢注之后，真正的主人马上就能注册，不用等
    assert client.post("/register", data={**form, "username": "realowner", "nickname": "owner"}).json()["success"] is True

    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.username == "realowner").first()
        squatter = db.query(User).filter(User.username == "squatter1").first()
        owner_token = db.query(EmailVerification.token).filter(EmailVerification.user_id == owner.id).scalar()
        squatter_token = db.query(EmailVerification.token).filter(EmailVerification.user_id == squatter.id).scalar()
        owner_id, squatter_id = owner.id, squatter.id
    finally:
        db.close()

    assert verify_email_service(owner_token)["success"] is True
    # 抢注账号的验证链接（即使被骗点了）也不能再把邮箱验证到它名下
    assert verify_email_service(squatter_token)["success"] is False

    db = SessionLocal()
    try:
        assert db.query(User).get(owner_id).email == "victim@example.com"
        assert db.query(User).get(squatter_id).email is None
        assert db.query(User).get(squatter_id).email_verified == 0
    finally:
        db.close()

    # 邮箱验证过之后，再用它注册才会提示已被注册
    again = client.post("/register", data={**form, "username": "another1", "nickname": "another"}).json()
    assert again["error_code"] == "registerEmailExists"


def test_verify_page_shows_which_account(client, monkeypatch):
    from database import SessionLocal
    from poker.models import EmailVerification, User
    from poker.services.auth import register

    monkeypatch.setattr(register, "send_verify_email", lambda to, token: True)
    client.post("/register", data={
        "username": "pageuser1", "nickname": "pageuser", "email": "page@example.com",
        "password": "GoodPass123", "confirm_password": "GoodPass123",
    })
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "pageuser1").first()
        token = db.query(EmailVerification.token).filter(EmailVerification.user_id == user.id).scalar()
    finally:
        db.close()

    page = client.get("/verify-email", params={"token": token}).text
    assert "pageuser1" in page
    assert "pa***@example.com" in page


def test_nickname_must_be_unique_at_registration(client, factory, monkeypatch):
    from poker.services.auth import register

    monkeypatch.setattr(register, "send_verify_email", lambda to, token: True)
    factory.user("orgnick01", nickname="王局头")
    result = client.post("/register", data={
        "username": "copycat1", "nickname": "王局头", "email": "copy@example.com",
        "password": "GoodPass123", "confirm_password": "GoodPass123",
    }).json()
    assert result["error_code"] == "registerNicknameExists"


def test_only_one_pending_buyin_request_per_player(factory):
    from poker.services.organizer import game_management as gm
    from poker.services.user.game import submit_buyin_request_service

    group_id = factory.group("G41")
    org = factory.user("org00041")
    factory.role(org, group_id, "organizer")
    alice = factory.user("ali00041")
    factory.role(alice, group_id, "user")
    game_id = gm.start_game_service(group_id, org, "局", [org, alice])["game_id"]

    assert submit_buyin_request_service(game_id, group_id, alice, 100)["success"] is True
    assert submit_buyin_request_service(game_id, group_id, alice, 100)["message"] == "buyinRequestPending"
