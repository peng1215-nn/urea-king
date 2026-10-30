"""已验证账号在个人资料页更换邮箱。"""

import pytest

DEFAULT_PASSWORD = "Passw0rd123"


@pytest.fixture(autouse=True)
def mail(monkeypatch):
    """不真正发邮件：记录确认链接和发往旧邮箱的通知。"""
    sent = {"confirm": [], "notice": []}
    from poker.routes.auth import register as register_routes
    from poker.services.auth import change_email

    monkeypatch.setattr(
        change_email, "send_change_email_confirm",
        lambda to, token, *rest: sent["confirm"].append((to, token)) or True,
    )
    monkeypatch.setattr(
        register_routes, "send_email_changed_notice",
        lambda to, *rest: sent["notice"].append(to) or True,
    )
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


def _get_user(user_id):
    from database import SessionLocal
    from poker.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return {"email": user.email, "pending_email": user.pending_email}
    finally:
        db.close()


def _setup(factory, login_as, username="alice", email="alice@old.com"):
    user_id = factory.user(username)
    _set_user(user_id, email=email)
    group_id = factory.group("G1")
    factory.role(user_id, group_id, "user")
    login_as(username, group_id)
    return user_id


def _request(client, new_email, password=DEFAULT_PASSWORD):
    return client.post("/account/change-email", data={"new_email": new_email, "current_password": password})


def test_requires_login(client):
    assert client.get("/account/email").status_code == 401
    assert _request(client, "x@new.com").status_code == 401


def test_change_takes_effect_only_after_confirm(client, factory, login_as, mail):
    user_id = _setup(factory, login_as)

    result = _request(client, "Alice@New.com").json()
    assert result["success"] is True and result["message"] == "accountEmailSent"

    # 确认之前仍是旧邮箱，新邮箱只是待确认
    assert _get_user(user_id) == {"email": "alice@old.com", "pending_email": "alice@new.com"}
    info = client.get("/account/email").json()
    assert info["email"] == "alice@old.com" and info["pending_email"] == "alice@new.com"

    to, token = mail["confirm"][-1]
    assert to == "alice@new.com"

    page = client.get(f"/verify-email?token={token}")
    assert page.status_code == 200 and "alice" in page.text

    client.post("/verify-email", data={"token": token})
    assert _get_user(user_id) == {"email": "alice@new.com", "pending_email": None}
    assert mail["notice"] == ["alice@old.com"]

    # 链接只能用一次
    client.post("/verify-email", data={"token": token})
    assert _get_user(user_id)["email"] == "alice@new.com"
    assert mail["notice"] == ["alice@old.com"]


def test_wrong_password_and_same_email(client, factory, login_as, mail):
    _setup(factory, login_as)
    assert _request(client, "a@new.com", password="WrongPass99").json()["message"] == "accountEmailWrongPassword"
    assert _request(client, "ALICE@old.com").json()["message"] == "accountEmailSame"
    assert _request(client, "not-an-email").json()["message"] == "accountEmailInvalid"
    assert mail["confirm"] == []


def test_email_taken_by_other_verified_account(client, factory, login_as):
    other = factory.user("bob00")
    _set_user(other, email="bob@x.com")
    _setup(factory, login_as)
    assert _request(client, "bob@x.com").json()["message"] == "accountEmailTaken"


def test_only_latest_link_works_and_interval(client, factory, login_as, mail):
    from datetime import timedelta

    from database import SessionLocal
    from poker.models import EmailVerification

    user_id = _setup(factory, login_as)
    assert _request(client, "first@new.com").json()["success"] is True
    # 5 分钟内不能再发
    assert _request(client, "second@new.com").json()["message"] == "accountEmailTooFrequent"

    # 把第一封的时间往前挪，模拟过了 5 分钟
    db = SessionLocal()
    try:
        for r in db.query(EmailVerification).filter(EmailVerification.user_id == user_id):
            r.created_at = r.created_at - timedelta(minutes=10)
        db.commit()
    finally:
        db.close()

    assert _request(client, "second@new.com").json()["success"] is True
    first_token = mail["confirm"][0][1]
    second_token = mail["confirm"][1][1]

    client.post("/verify-email", data={"token": first_token})
    assert _get_user(user_id)["email"] == "alice@old.com"

    client.post("/verify-email", data={"token": second_token})
    assert _get_user(user_id)["email"] == "second@new.com"


def test_cancel(client, factory, login_as, mail):
    user_id = _setup(factory, login_as)
    _request(client, "c@new.com")
    token = mail["confirm"][-1][1]

    assert client.post("/account/change-email/cancel").json()["success"] is True
    assert _get_user(user_id) == {"email": "alice@old.com", "pending_email": None}

    client.post("/verify-email", data={"token": token})
    assert _get_user(user_id)["email"] == "alice@old.com"


def test_confirm_fails_if_email_was_taken_meanwhile(client, factory, login_as, mail):
    user_id = _setup(factory, login_as)
    _request(client, "race@new.com")
    token = mail["confirm"][-1][1]

    other = factory.user("carol0")
    _set_user(other, email="race@new.com")

    client.post("/verify-email", data={"token": token})
    assert _get_user(user_id) == {"email": "alice@old.com", "pending_email": None}
    assert mail["notice"] == []


def test_reset_links_to_old_email_stop_working(client, factory, login_as, mail):
    from datetime import timedelta

    from core.time import now_columbus_naive
    from database import SessionLocal
    from poker.models import EmailVerification

    user_id = _setup(factory, login_as)
    db = SessionLocal()
    try:
        db.add(EmailVerification(
            user_id=user_id, token="old-reset-token", purpose="reset_password",
            expires_at=now_columbus_naive() + timedelta(minutes=15), used=0,
        ))
        db.commit()
    finally:
        db.close()

    _request(client, "d@new.com")
    client.post("/verify-email", data={"token": mail["confirm"][-1][1]})

    response = client.post("/reset-password", data={
        "token": "old-reset-token", "new_password": "NewPassw0rd9", "confirm_password": "NewPassw0rd9",
    })
    assert response.json()["success"] is False
