"""牌局审计报告：事件记录、报告内容、查看权限。"""

import pytest


@pytest.fixture
def table(factory):
    group_id = factory.group("G1", name="周五局")
    org = factory.user("orgaaaa1")
    factory.role(org, group_id, "organizer")
    members = []
    for name in ("alice001", "bobby001", "carol001"):
        uid = factory.user(name)
        factory.role(uid, group_id, "user")
        members.append(uid)
    return {"group": group_id, "org": org, "members": members}


def _svc():
    from poker.services.organizer import game_management

    return game_management


def _request_id(game_id, user_id):
    from database import SessionLocal
    from poker.models import ChipRequest

    db = SessionLocal()
    try:
        return db.query(ChipRequest.id).filter(
            ChipRequest.game_id == game_id,
            ChipRequest.user_id == user_id,
            ChipRequest.status == "pending",
        ).order_by(ChipRequest.id.desc()).first()[0]
    finally:
        db.close()


def _play_full_game(t):
    """开局 → 申请/批准/拒绝 → 局头买入 → 代买 → 中途离场 → 结束。返回 game_id。"""
    from poker.services.user.game import submit_buyin_request_service, update_chip_auth_service

    svc = _svc()
    alice, bob, carol = t["members"]
    game_id = svc.start_game_service(
        group_id=t["group"], organizer_id=t["org"], name="周五局",
        preselected_user_ids=[t["org"], alice, bob, carol],
    )["game_id"]

    assert submit_buyin_request_service(game_id=game_id, group_id=t["group"], user_id=alice, amount=200)["success"]
    assert svc.approve_chip_request_service(_request_id(game_id, alice), game_id, t["group"], t["org"])["success"]

    assert submit_buyin_request_service(game_id=game_id, group_id=t["group"], user_id=bob, amount=50)["success"]
    assert svc.reject_chip_request_service(_request_id(game_id, bob), game_id, t["group"], t["org"])["success"]

    assert svc.organizer_buyin_service(game_id=game_id, group_id=t["group"], user_id=t["org"], amount=100, buy_type="insurance")["success"]

    assert update_chip_auth_service(bob, t["group"], 1)["success"]
    assert svc.organizer_proxy_buyin_service(game_id, t["group"], t["org"], bob, 100)["success"]

    assert svc.organizer_buyin_service(game_id=game_id, group_id=t["group"], user_id=t["org"], amount=100)["success"]
    assert svc.exit_player_from_game_service(game_id, t["group"], carol, 0, actor_id=t["org"])["success"]

    # 留一个待审批的申请，结束时会被自动拒绝
    assert submit_buyin_request_service(game_id=game_id, group_id=t["group"], user_id=alice, amount=30)["success"]

    result = svc.finish_game_service(
        game_id=game_id, group_id=t["group"], organizer_id=t["org"],
        player_cash_outs=[
            {"user_id": t["org"], "cash_out": 150},
            {"user_id": alice, "cash_out": 250},
            {"user_id": bob, "cash_out": 100},
            {"user_id": carol, "cash_out": 0},
        ],
    )
    assert result["success"] is True, result
    return game_id


def _report(game_id, group_id):
    from database import SessionLocal
    from poker.services.common.game_events import build_game_report

    db = SessionLocal()
    try:
        return build_game_report(db, game_id, group_id)
    finally:
        db.close()


def test_every_step_is_recorded_and_totals_match(table):
    t = table
    game_id = _play_full_game(t)
    report = _report(game_id, t["group"])

    types = [e["type"] for e in report["events"]]
    assert types[0] == "game_started"
    assert types[-1] == "game_finished"
    for expected in (
        "buyin_requested", "buyin_approved", "buyin_rejected", "organizer_buyin",
        "proxy_buyin", "player_exited", "buyin_auto_rejected",
    ):
        assert expected in types, expected

    assert report["has_events"] is True
    assert report["all_match"] is True

    org_row = next(row for row in report["summary"] if row["user_id"] == t["org"])
    assert org_row["buy_in_by_type"]["insurance"] == 100

    approved = next(e for e in report["events"] if e["type"] == "buyin_approved")
    assert approved["actor_name"] == "orgaaaa1"
    assert approved["target_name"] == "alice001"
    assert approved["amount"] == 200


def test_names_are_snapshots(table):
    from database import SessionLocal
    from poker.models import User

    t = table
    game_id = _play_full_game(t)

    db = SessionLocal()
    try:
        db.query(User).filter(User.id == t["members"][0]).update({"nickname": "改过的名字"})
        db.commit()
    finally:
        db.close()

    approved = next(e for e in _report(game_id, t["group"])["events"] if e["type"] == "buyin_approved")
    assert approved["target_name"] == "alice001"


def test_ongoing_game_has_no_report(table):
    t = table
    game_id = _svc().start_game_service(
        group_id=t["group"], organizer_id=t["org"], name="进行中",
        preselected_user_ids=[t["org"], t["members"][0]],
    )["game_id"]
    assert _report(game_id, t["group"]) is None


def test_members_and_organizer_can_view_report(client, table, login_as):
    t = table
    game_id = _play_full_game(t)

    login_as("alice001", t["group"])
    assert client.get("/game-report", params={"game_id": game_id}).status_code == 200
    data = client.get("/game-report/data", params={"game_id": game_id}).json()
    assert data["success"] is True
    assert data["game"]["id"] == game_id

    client.get("/logout")
    login_as("orgaaaa1", t["group"])
    assert client.get("/game-report/data", params={"game_id": game_id}).json()["success"] is True


def test_other_groups_cannot_view_report(client, factory, table, login_as):
    t = table
    game_id = _play_full_game(t)

    other_group = factory.group("G2")
    outsider = factory.user("orgbbbb1")
    factory.role(outsider, other_group, "organizer")
    login_as("orgbbbb1", other_group)

    # 非管理员传 group_id 也没用，只看会话里的当前组
    data = client.get("/game-report/data", params={"game_id": game_id, "group_id": t["group"]}).json()
    assert data == {"success": False, "message": "gameNotFound"}


def test_admin_views_report_with_group_id(client, factory, table, login_as):
    t = table
    game_id = _play_full_game(t)

    admin_group = factory.group("ADMIN")
    admin = factory.user("admin003")
    factory.role(admin, admin_group, "admin")
    login_as("admin003", admin_group)

    assert client.get("/game-report/data", params={"game_id": game_id}).json()["message"] == "noGroupSelected"
    data = client.get("/game-report/data", params={"game_id": game_id, "group_id": t["group"]}).json()
    assert data["success"] is True


def test_report_page_requires_login(client):
    response = client.get("/game-report", params={"game_id": 1}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert client.get("/game-report/data", params={"game_id": 1}).json()["message"] == "permissionDenied"


def test_deleting_game_deletes_its_events(client, factory, table, login_as):
    from database import SessionLocal
    from poker.models import GameEvent

    t = table
    game_id = _play_full_game(t)

    admin_group = factory.group("ADMIN")
    admin = factory.user("admin004")
    factory.role(admin, admin_group, "admin")
    login_as("admin004", admin_group)

    result = client.post("/admin/game-log/delete", data={"game_id": game_id, "group_id": t["group"]}).json()
    assert result["success"] is True

    db = SessionLocal()
    try:
        assert db.query(GameEvent).filter(GameEvent.game_id == game_id).count() == 0
    finally:
        db.close()


def test_rejoin_records_whether_player_stepped_away_or_cashed_out(table):
    from database import SessionLocal
    from poker.models import GameEvent

    t = table
    svc = _svc()
    alice, bob, _ = t["members"]
    game_id = svc.start_game_service(
        group_id=t["group"], organizer_id=t["org"], name="进出",
        preselected_user_ids=[t["org"], alice, bob],
    )["game_id"]

    assert svc.remove_player_from_game_service(game_id, t["group"], alice, actor_id=t["org"])["success"]
    assert svc.add_player_to_game_service(game_id, t["group"], alice, t["org"])["rejoined"] is True

    assert svc.exit_player_from_game_service(game_id, t["group"], bob, 80, actor_id=t["org"])["success"]
    assert svc.add_player_to_game_service(game_id, t["group"], bob, t["org"])["rejoined"] is True

    db = SessionLocal()
    try:
        rejoins = {
            e.target_user_id: e.details
            for e in db.query(GameEvent).filter(
                GameEvent.game_id == game_id, GameEvent.event_type == "player_rejoined",
            )
        }
    finally:
        db.close()

    import json
    assert json.loads(rejoins[alice]) == {"after": "away"}
    assert json.loads(rejoins[bob]) == {"after": "exit", "cash_out": 80}


def test_report_checks_cash_out_taken_at_exit(table):
    t = table
    svc = _svc()
    alice, bob, _ = t["members"]
    game_id = svc.start_game_service(
        group_id=t["group"], organizer_id=t["org"], name="离场",
        preselected_user_ids=[t["org"], alice, bob],
    )["game_id"]
    assert svc.organizer_buyin_service(game_id=game_id, group_id=t["group"], user_id=t["org"], amount=100)["success"]
    assert svc.exit_player_from_game_service(game_id, t["group"], alice, 0, actor_id=t["org"])["success"]
    assert svc.organizer_proxy_buyin_service(game_id, t["group"], t["org"], bob, 100)["success"] is False  # bob 未授权
    assert svc.finish_game_service(
        game_id=game_id, group_id=t["group"], organizer_id=t["org"],
        player_cash_outs=[{"user_id": t["org"], "cash_out": 60}, {"user_id": alice, "cash_out": 0}, {"user_id": bob, "cash_out": 40}],
    )["success"]

    report = _report(game_id, t["group"])
    assert report["all_match"] is True
    alice_row = next(r for r in report["summary"] if r["user_id"] == alice)
    assert alice_row["left_cash_out"] == 0 and alice_row["left_from_events"] == 0
