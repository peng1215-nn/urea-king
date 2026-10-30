"""
普通成员的“当前牌局”页：离开牌局后仍能看到自己的状态、申请记录的来源、未登录时的返回。
"""

import pytest


@pytest.fixture
def table(factory):
    """一个组：局头 + 2 个成员，已经开了一局。"""
    from poker.services.organizer import game_management as gm

    group_id = factory.group("G1", name="周五局")
    org = factory.user("orgaaaa1")
    factory.role(org, group_id, "organizer")
    alice = factory.user("alice001")
    bob = factory.user("bobby001")
    for uid in (alice, bob):
        factory.role(uid, group_id, "user")

    game_id = gm.start_game_service(group_id, org, "周五局", [org, alice, bob])["game_id"]
    return {"group": group_id, "org": org, "alice": alice, "bob": bob, "game": game_id}


def _ongoing(t, user_id):
    from poker.services.user.game import get_user_ongoing_games_service

    result = get_user_ongoing_games_service(group_id=t["group"], user_id=user_id)
    assert result["success"] is True, result
    return result


def _pending_id(game_id, user_id):
    from database import SessionLocal
    from poker.models import ChipRequest

    db = SessionLocal()
    try:
        return db.query(ChipRequest.id).filter(
            ChipRequest.game_id == game_id,
            ChipRequest.user_id == user_id,
            ChipRequest.status == "pending",
        ).scalar()
    finally:
        db.close()


def test_active_player_sees_the_table(table):
    t = table
    games = _ongoing(t, t["alice"])["games"]
    assert len(games) == 1
    assert games[0]["my_status"] == "active"
    assert {p["user_id"] for p in games[0]["players"]} == {t["org"], t["alice"], t["bob"]}


def test_exited_player_still_sees_own_result(table):
    from poker.services.organizer import game_management as gm

    t = table
    gm.organizer_buyin_service(t["game"], t["group"], t["org"], 10)
    from poker.services.user.game import submit_buyin_request_service

    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    assert gm.approve_chip_request_service(_pending_id(t["game"], t["alice"]), t["game"], t["group"], t["org"])["success"]
    assert gm.exit_player_from_game_service(t["game"], t["group"], t["alice"], 150, actor_id=t["org"])["success"]

    game = _ongoing(t, t["alice"])["games"][0]
    assert game["my_status"] == "exited"
    assert game["my_cash_out"] == 150
    assert game["my_net"] == 50
    # 离开后只返回自己的记录，不多给别人的信息
    assert [p["user_id"] for p in game["players"]] == [t["alice"]]


def test_away_player_sees_away_state_and_auto_rejected_request(table):
    from poker.services.organizer import game_management as gm
    from poker.services.user.game import submit_buyin_request_service

    t = table
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    assert gm.remove_player_from_game_service(t["game"], t["group"], t["alice"], actor_id=t["org"])["success"]

    game = _ongoing(t, t["alice"])["games"][0]
    assert game["my_status"] == "away"
    assert "my_cash_out" not in game
    request = game["players"][0]["requests"][0]
    assert request["status"] == "rejected"
    assert request["rejected_by"] == "auto"

    # 回到牌局后恢复成在桌上
    assert gm.add_player_to_game_service(t["game"], t["group"], t["alice"], t["org"])["success"]
    assert _ongoing(t, t["alice"])["games"][0]["my_status"] == "active"


def test_request_sources_are_labelled(table):
    from poker.services.organizer import game_management as gm
    from poker.services.user.game import submit_buyin_request_service, update_chip_auth_service

    t = table
    assert update_chip_auth_service(t["alice"], t["group"], 1)["success"]
    assert gm.organizer_proxy_buyin_service(t["game"], t["group"], t["org"], t["alice"], 300)["success"]

    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    assert gm.approve_chip_request_service(_pending_id(t["game"], t["alice"]), t["game"], t["group"], t["org"])["success"]

    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 50)["success"]
    assert gm.reject_chip_request_service(_pending_id(t["game"], t["alice"]), t["game"], t["group"], t["org"])["success"]

    me = next(p for p in _ongoing(t, t["alice"])["games"][0]["players"] if p["is_me"])
    by_amount = {r["amount"]: r for r in me["requests"]}
    assert by_amount[300]["source"] == "proxy"
    assert by_amount[100]["source"] == "self"
    assert by_amount[50]["rejected_by"] == "organizer"


def test_member_not_in_any_game_gets_group_game_count(factory, table):
    t = table
    carol = factory.user("carol001")
    factory.role(carol, t["group"], "user")

    result = _ongoing(t, carol)
    assert result["games"] == []
    assert result["group_ongoing_count"] == 1


def test_finished_game_disappears(table):
    from poker.services.organizer import game_management as gm

    t = table
    result = gm.finish_game_service(
        game_id=t["game"], group_id=t["group"], organizer_id=t["org"],
        player_cash_outs=[{"user_id": u, "cash_out": 0} for u in (t["org"], t["alice"], t["bob"])],
    )
    assert result["success"], result
    result = _ongoing(t, t["alice"])
    assert result["games"] == []
    assert result["group_ongoing_count"] == 0


@pytest.mark.parametrize("path", [
    "/user/game/ongoing",
    "/user/game/chip-auth-settings",
    "/user/game-log/list",
    "/user/announcements",
    "/user/change-password/current",
])
def test_user_api_without_login_returns_401(client, path):
    response = client.get(path)
    assert response.status_code == 401
    assert response.json() == {"success": False, "message": "sessionExpired"}


def test_user_api_with_other_role_is_still_permission_denied(client, table, login_as):
    login_as("orgaaaa1", table["group"])
    response = client.get("/user/game/ongoing")
    assert response.status_code == 200
    assert response.json() == {"success": False, "message": "permissionDenied"}


# ───────────────────────── 撤回买入申请 ─────────────────────────

def _request_row(req_id):
    from database import SessionLocal
    from poker.models import ChipRequest

    db = SessionLocal()
    try:
        r = db.query(ChipRequest).filter(ChipRequest.id == req_id).first()
        return {"status": r.status, "resolved_by": r.resolved_by, "resolved_at": r.resolved_at}
    finally:
        db.close()


def _events(game_id, event_type):
    from database import SessionLocal
    from poker.models import GameEvent

    db = SessionLocal()
    try:
        return [
            (e.actor_user_id, e.target_user_id, e.amount)
            for e in db.query(GameEvent).filter(
                GameEvent.game_id == game_id, GameEvent.event_type == event_type,
            ).all()
        ]
    finally:
        db.close()


def _buy_in(game_id, user_id):
    from database import SessionLocal
    from poker.models import PokerGame, PokerGamePlayer

    db = SessionLocal()
    try:
        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id, PokerGamePlayer.user_id == user_id,
        ).first()
        game = db.query(PokerGame).filter(PokerGame.id == game_id).first()
        return player.total_buy_in or 0, game.total_buy_in or 0
    finally:
        db.close()


def test_player_withdraws_pending_request(table):
    from poker.services.user.game import submit_buyin_request_service, withdraw_buyin_request_service

    t = table
    before = _buy_in(t["game"], t["alice"])
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    req_id = _pending_id(t["game"], t["alice"])

    assert withdraw_buyin_request_service(req_id, t["group"], t["alice"]) == {"success": True}

    row = _request_row(req_id)
    assert row["status"] == "withdrawn"
    assert row["resolved_by"] == t["alice"]
    assert row["resolved_at"] is not None
    assert _events(t["game"], "buyin_withdrawn") == [(t["alice"], t["alice"], 100)]
    assert _buy_in(t["game"], t["alice"]) == before

    # 记录里显示为自己撤回，不会被当成代买或自动拒绝
    me = next(p for p in _ongoing(t, t["alice"])["games"][0]["players"] if p["is_me"])
    request = me["requests"][0]
    assert request["status"] == "withdrawn"
    assert request["source"] == "self"
    assert "rejected_by" not in request

    # 撤回后可以重新提交；同一条不能撤回两次
    assert withdraw_buyin_request_service(req_id, t["group"], t["alice"])["message"] == "requestAlreadyHandled"
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 50)["success"]


def test_cannot_withdraw_someone_elses_request(table):
    from poker.services.user.game import submit_buyin_request_service, withdraw_buyin_request_service

    t = table
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    req_id = _pending_id(t["game"], t["alice"])

    assert withdraw_buyin_request_service(req_id, t["group"], t["bob"])["message"] == "requestNotFound"
    assert withdraw_buyin_request_service(999999, t["group"], t["alice"])["message"] == "requestNotFound"
    assert _request_row(req_id)["status"] == "pending"
    assert _events(t["game"], "buyin_withdrawn") == []


def test_cannot_withdraw_from_another_group(factory, table):
    from poker.services.user.game import submit_buyin_request_service, withdraw_buyin_request_service

    t = table
    other = factory.group("G2")
    factory.role(t["alice"], other, "user")
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    req_id = _pending_id(t["game"], t["alice"])

    assert withdraw_buyin_request_service(req_id, other, t["alice"])["message"] == "gameNotFound"
    assert _request_row(req_id)["status"] == "pending"


def test_cannot_withdraw_approved_or_rejected_request(table):
    from poker.services.organizer import game_management as gm
    from poker.services.user.game import submit_buyin_request_service, withdraw_buyin_request_service

    t = table
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    approved = _pending_id(t["game"], t["alice"])
    assert gm.approve_chip_request_service(approved, t["game"], t["group"], t["org"])["success"]
    assert withdraw_buyin_request_service(approved, t["group"], t["alice"])["message"] == "requestAlreadyHandled"
    assert _request_row(approved)["status"] == "approved"

    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 50)["success"]
    rejected = _pending_id(t["game"], t["alice"])
    assert gm.reject_chip_request_service(rejected, t["game"], t["group"], t["org"])["success"]
    assert withdraw_buyin_request_service(rejected, t["group"], t["alice"])["message"] == "requestAlreadyHandled"
    assert _request_row(rejected)["status"] == "rejected"

    assert _events(t["game"], "buyin_withdrawn") == []
    assert _buy_in(t["game"], t["alice"])[0] == 100


def test_organizer_cannot_approve_withdrawn_request(table):
    from poker.services.organizer import game_management as gm
    from poker.services.user.game import submit_buyin_request_service, withdraw_buyin_request_service

    t = table
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    req_id = _pending_id(t["game"], t["alice"])
    assert withdraw_buyin_request_service(req_id, t["group"], t["alice"])["success"]

    assert gm.approve_chip_request_service(req_id, t["game"], t["group"], t["org"])["message"] == "requestNotFound"
    assert gm.reject_chip_request_service(req_id, t["game"], t["group"], t["org"])["message"] == "requestNotFound"
    assert _request_row(req_id)["status"] == "withdrawn"
    assert _buy_in(t["game"], t["alice"])[0] == 0

    # 局头的待审批列表里也不再出现
    for game in gm.get_ongoing_games_service(t["group"])["games"]:
        assert all(r["id"] != req_id for r in game.get("requests", []))


def test_withdraw_and_approve_race_has_one_winner(table):
    import threading

    from poker.services.organizer import game_management as gm
    from poker.services.user.game import submit_buyin_request_service, withdraw_buyin_request_service

    t = table
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    req_id = _pending_id(t["game"], t["alice"])

    barrier = threading.Barrier(2)
    results = {}

    def withdraw():
        barrier.wait()
        results["withdraw"] = withdraw_buyin_request_service(req_id, t["group"], t["alice"])

    def approve():
        barrier.wait()
        results["approve"] = gm.approve_chip_request_service(req_id, t["game"], t["group"], t["org"])

    threads = [threading.Thread(target=withdraw), threading.Thread(target=approve)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    winners = [k for k, r in results.items() if r["success"]]
    assert len(winners) == 1, results
    if winners[0] == "withdraw":
        assert results["approve"]["message"] == "requestNotFound"
        assert _buy_in(t["game"], t["alice"])[0] == 0
    else:
        assert results["withdraw"]["message"] == "requestAlreadyHandled"
        assert _buy_in(t["game"], t["alice"])[0] == 100


def test_withdraw_over_http(client, table, login_as):
    from poker.services.user.game import submit_buyin_request_service

    t = table
    assert submit_buyin_request_service(t["game"], t["group"], t["alice"], 100)["success"]
    req_id = _pending_id(t["game"], t["alice"])

    assert client.post("/user/game/buyin-request/withdraw", data={"request_id": req_id}).status_code == 401

    login_as("bobby001", t["group"])
    assert client.post("/user/game/buyin-request/withdraw", data={"request_id": req_id}).json()["message"] == "requestNotFound"
    client.get("/logout")

    login_as("alice001", t["group"])
    assert client.post("/user/game/buyin-request/withdraw", data={"request_id": req_id}).json() == {"success": True}
    assert _request_row(req_id)["status"] == "withdrawn"
