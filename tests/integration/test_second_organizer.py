"""一个组最多两个局头：设为局头、卸任、两人都能给自己买入并显示保险 / Anti 明细。"""

import pytest


@pytest.fixture
def group(factory):
    group_id = factory.group("G1", name="周五局")
    org = factory.user("orgaaaa1")
    factory.role(org, group_id, "organizer")
    members = []
    for name in ("alice001", "bobby001"):
        uid = factory.user(name)
        factory.role(uid, group_id, "user")
        members.append(uid)
    return {"group": group_id, "org": org, "members": members}


def _role(user_id, group_id):
    from database import SessionLocal
    from poker.models import UserGroupRole

    db = SessionLocal()
    try:
        row = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id, UserGroupRole.group_id == group_id,
        ).first()
        return row.role if row else None
    finally:
        db.close()


def _promote(client, target):
    return client.post("/organizer/promote-member", data={"target_user_id": target}).json()


def test_promote_member_and_limit(client, group, login_as):
    alice, bob = group["members"]
    login_as("orgaaaa1", group["group"])

    members = client.get("/organizer/members").json()
    assert members["organizer_count"] == 1 and members["max_organizers"] == 2

    assert _promote(client, alice)["success"] is True
    assert _role(alice, group["group"]) == "organizer"

    # 已经是局头 / 超过上限
    assert _promote(client, alice)["message"] == "memberAlreadyOrganizer"
    result = _promote(client, bob)
    assert result["message"] == "organizerLimitReached"
    assert _role(bob, group["group"]) == "user"

    # 局头之间不能互相移出
    response = client.post("/organizer/remove-member", data={"target_user_id": alice}).json()
    assert response["message"] == "cannotRemoveOrganizer"


def test_regular_member_cannot_promote(client, group, login_as):
    alice, bob = group["members"]
    login_as("alice001", group["group"])
    assert _promote(client, bob)["message"] == "permissionDenied"
    assert _role(bob, group["group"]) == "user"


def test_promoted_member_old_session_stops_working(client, factory, group, login_as):
    from fastapi.testclient import TestClient

    import main

    alice = group["members"][0]
    with TestClient(main.app, base_url="http://localhost") as alice_client:
        response = alice_client.post("/login", data={"username": "alice001", "password": "Passw0rd123"})
        assert response.json()["success"] is True
        alice_client.post("/select-group", data={"group_id": group["group"]})
        assert alice_client.get("/user/game/ongoing").json()["success"] is True

        login_as("orgaaaa1", group["group"])
        assert _promote(client, alice)["success"] is True

        # 她还拿着“普通成员”身份的登录：立即失效，要重新登录
        response = alice_client.get("/user/game/ongoing", follow_redirects=False)
        assert response.status_code in (302, 303, 307, 401)


def test_step_down(client, group, login_as):
    alice = group["members"][0]
    login_as("orgaaaa1", group["group"])

    # 唯一的局头不能卸任
    assert client.post("/organizer/step-down").json()["message"] == "lastOrganizerCannotStepDown"
    assert _role(group["org"], group["group"]) == "organizer"

    assert _promote(client, alice)["success"] is True

    login_as("alice001", group["group"])
    assert client.post("/organizer/step-down").json()["success"] is True
    assert _role(alice, group["group"]) == "user"
    # 卸任后登录失效
    assert client.get("/organizer/members").json().get("success") is not True


def test_second_organizer_buys_in_for_themselves(group):
    from poker.services.common.game_log import get_game_logs_service
    from poker.services.organizer import game_management as gm

    alice = group["members"][0]
    _set_role(alice, group["group"], "organizer")

    start = gm.start_game_service(
        group_id=group["group"], organizer_id=group["org"], name="", preselected_user_ids=[group["org"], alice],
    )
    assert start["success"] is True, start
    game_id = start["game_id"]

    # 第二位局头给自己买保险
    result = gm.organizer_buyin_service(
        game_id=game_id, group_id=group["group"], user_id=alice, amount=300, buy_type="insurance",
    )
    assert result["success"] is True, result

    ongoing = gm.get_ongoing_games_service(group["group"])["games"][0]
    alice_row = next(p for p in ongoing["players"] if p["user_id"] == alice)
    assert alice_row["is_group_organizer"] is True
    assert alice_row["buy_in_insurance"] == 300

    finish = gm.finish_game_service(
        game_id=game_id, group_id=group["group"], organizer_id=alice,
        player_cash_outs=[{"user_id": group["org"], "cash_out": 0}, {"user_id": alice, "cash_out": 300}],
    )
    assert finish["success"] is True, finish

    logs = get_game_logs_service(group["group"])
    alice_log = next(p for p in logs["games"][0]["players"] if p["user_id"] == alice)
    assert alice_log["is_organizer"] is True
    assert alice_log["buy_in_insurance"] == 300


def _set_role(user_id, group_id, role):
    from database import SessionLocal
    from poker.models import UserGroupRole

    db = SessionLocal()
    try:
        row = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id, UserGroupRole.group_id == group_id,
        ).first()
        row.role = role
        db.commit()
    finally:
        db.close()
