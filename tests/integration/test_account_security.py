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
    _set_user(user_id, email=email, email_verified=0)
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
