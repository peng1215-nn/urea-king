"""
核心记账流程：开局、买入、批准、离场、结算，以及同时操作时金额不出错。

大部分用例直接调用业务函数（每次调用自己开数据库会话，和线上一样），
少数用例走 HTTP，验证权限和接口层。
"""

import threading

import pytest

DEFAULT_PASSWORD = "Passw0rd123"


# ───────────────────────── 辅助 ─────────────────────────

@pytest.fixture
def table(factory):
    """一个组：局头 + 3 个成员。返回各自的 id。"""
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


def _start(t, players=None, name="周五局"):
    result = _svc().start_game_service(
        group_id=t["group"],
        organizer_id=t["org"],
        name=name,
        preselected_user_ids=players if players is not None else [t["org"], *t["members"]],
    )
    assert result["success"] is True, result
    return result["game_id"]


def _player(game_id, user_id):
    from database import SessionLocal
    from poker.models import PokerGamePlayer

    db = SessionLocal()
    try:
        return db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
        ).first()
    finally:
        db.close()


def _game(game_id):
    from database import SessionLocal
    from poker.models import PokerGame

    db = SessionLocal()
    try:
        return db.query(PokerGame).filter(PokerGame.id == game_id).first()
    finally:
        db.close()


def _request_buyin(game_id, group_id, user_id, amount):
    from database import SessionLocal
    from poker.models import ChipRequest
    from poker.services.user.game import submit_buyin_request_service

    result = submit_buyin_request_service(game_id=game_id, group_id=group_id, user_id=user_id, amount=amount)
    assert result["success"] is True, result

    db = SessionLocal()
    try:
        return db.query(ChipRequest.id).filter(
            ChipRequest.game_id == game_id,
            ChipRequest.user_id == user_id,
            ChipRequest.status == "pending",
        ).order_by(ChipRequest.id.desc()).first()[0]
    finally:
        db.close()


def _buyin(t, game_id, user_id, amount):
    return _svc().organizer_buyin_service(game_id=game_id, group_id=t["group"], user_id=user_id, amount=amount)


def _finish(t, game_id, cash_outs, force=False):
    return _svc().finish_game_service(
        game_id=game_id,
        group_id=t["group"],
        organizer_id=t["org"],
        player_cash_outs=[{"user_id": uid, "cash_out": co} for uid, co in cash_outs.items()],
        force=force,
    )


def _run_concurrently(func, count):
    """count 个线程在同一时刻一起调用 func，返回所有结果。"""
    barrier = threading.Barrier(count)
    results = [None] * count

    def worker(index):
        barrier.wait()
        results[index] = func(index)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    return results


# ───────────────────────── 完整流程 ─────────────────────────

def test_full_game_flow_balances(table):
    t = table
    alice, bob, carol = t["members"]
    game_id = _start(t)

    # 玩家申请 + 局头批准；局头给自己买入
    req = _request_buyin(game_id, t["group"], alice, 200)
    assert _svc().approve_chip_request_service(req, game_id, t["group"], t["org"])["success"] is True
    assert _buyin(t, game_id, bob, 100)["success"] is True
    assert _buyin(t, game_id, carol, 100)["success"] is True
    assert _buyin(t, game_id, t["org"], 100)["success"] is True

    # carol 中途离场带走 150
    assert _svc().exit_player_from_game_service(game_id, t["group"], carol, 150)["success"] is True
    assert _player(game_id, carol).net == 50

    # 结束时只填剩余筹码：carol 已经结算离场，手上是 0，离场拿走的 150 自动计入
    result = _finish(t, game_id, {t["org"]: 0, alice: 300, bob: 50, carol: 0})
    assert result["success"] is True, result
    assert result["is_balanced"] == 1
    assert _player(game_id, carol).cash_out == 150
    assert _player(game_id, carol).net == 50

    game = _game(game_id)
    assert game.status == "finished"
    assert game.total_buy_in == 500
    assert game.total_cash_out == 500
    assert _player(game_id, alice).net == 100
    assert _player(game_id, bob).net == -50
    assert _player(game_id, t["org"]).net == -100


def test_unbalanced_game_is_refused_unless_forced(table):
    t = table
    game_id = _start(t, players=[t["org"], t["members"][0]])
    _buyin(t, game_id, t["members"][0], 100)

    cash_outs = {t["org"]: 0, t["members"][0]: 80}
    result = _finish(t, game_id, cash_outs)
    assert result["success"] is False
    assert result["message"] == "balanceCheckFailed"
    assert result["diff"] == -20
    assert _game(game_id).status == "ongoing"

    result = _finish(t, game_id, cash_outs, force=True)
    assert result["success"] is True
    assert result["is_balanced"] == 0


def test_rejected_request_does_not_change_buy_in(table):
    t = table
    alice = t["members"][0]
    game_id = _start(t)
    req = _request_buyin(game_id, t["group"], alice, 100)

    assert _svc().reject_chip_request_service(req, game_id, t["group"], t["org"])["success"] is True
    assert _player(game_id, alice).total_buy_in == 0
    # 已拒绝的申请不能再批准
    assert _svc().approve_chip_request_service(req, game_id, t["group"], t["org"])["message"] == "requestNotFound"


# ───────────────────────── 结算名单与金额 ─────────────────────────

def test_finish_requires_exact_player_list(table):
    t = table
    alice, bob, carol = t["members"]
    game_id = _start(t)

    # 漏掉一个人
    result = _finish(t, game_id, {t["org"]: 0, alice: 0, bob: 0})
    assert result["message"] == "settlementPlayersMismatch"

    # 多了一个不在局里的人
    outsider = 999999
    result = _finish(t, game_id, {t["org"]: 0, alice: 0, bob: 0, carol: 0, outsider: 0})
    assert result["message"] == "settlementPlayersMismatch"

    # 同一个人出现两次
    result = _svc().finish_game_service(
        game_id=game_id, group_id=t["group"], organizer_id=t["org"],
        player_cash_outs=[{"user_id": alice, "cash_out": 0}, {"user_id": alice, "cash_out": 0}],
    )
    assert result["message"] == "settlementPlayersMismatch"
    assert _game(game_id).status == "ongoing"


@pytest.mark.parametrize("bad, code", [(-1, "invalidAmount"), (1_000_001, "amountTooLarge"), ("100", "invalidAmount")])
def test_finish_rejects_bad_cash_out(table, bad, code):
    t = table
    game_id = _start(t, players=[t["org"]])
    result = _finish(t, game_id, {t["org"]: bad})
    assert result["message"] == code
    assert _game(game_id).status == "ongoing"


@pytest.mark.parametrize("amount, code", [(0, "invalidAmount"), (-5, "invalidAmount"), (1_000_001, "amountTooLarge")])
def test_buy_in_amount_bounds(table, amount, code):
    from poker.services.user.game import submit_buyin_request_service

    t = table
    alice = t["members"][0]
    game_id = _start(t)

    assert _buyin(t, game_id, alice, amount)["message"] == code
    assert submit_buyin_request_service(game_id, t["group"], alice, amount)["message"] == code
    assert _svc().exit_player_from_game_service(game_id, t["group"], alice, -1)["message"] == "invalidAmount"
    assert _player(game_id, alice).total_buy_in == 0


def test_buy_in_at_limit_is_allowed(table):
    t = table
    game_id = _start(t)
    assert _buyin(t, game_id, t["members"][0], 1_000_000)["success"] is True


# ───────────────────────── 结束后不能再动 ─────────────────────────

def test_finished_game_cannot_be_changed(table):
    from poker.services.user.game import submit_buyin_request_service

    t = table
    alice = t["members"][0]
    game_id = _start(t, players=[t["org"], alice])
    req = _request_buyin(game_id, t["group"], alice, 50)
    assert _finish(t, game_id, {t["org"]: 0, alice: 0})["success"] is True

    assert _buyin(t, game_id, alice, 10)["message"] == "gameNotFound"
    assert _svc().approve_chip_request_service(req, game_id, t["group"], t["org"])["message"] == "gameNotFound"
    assert _svc().exit_player_from_game_service(game_id, t["group"], alice, 10)["message"] == "gameNotFound"
    assert _svc().add_player_to_game_service(game_id, t["group"], t["members"][1], t["org"])["message"] == "gameNotFound"
    assert submit_buyin_request_service(game_id, t["group"], alice, 10)["message"] == "gameNotFound"
    assert _finish(t, game_id, {t["org"]: 0, alice: 0})["message"] == "gameNotFound"
    assert _player(game_id, alice).total_buy_in == 0


def test_update_cashout_endpoint_is_removed(client, table, login_as):
    login_as("orgaaaa1", table["group"])
    response = client.post("/organizer/game/update-cashout", data={"game_id": 1, "user_id": 1, "cash_out": 1})
    assert response.status_code in (404, 405)


# ───────────────────────── 人数、局数、代买、跨组 ─────────────────────────

def test_player_and_game_limits(factory, table):
    t = table
    extra = []
    for i in range(8):
        uid = factory.user(f"extra{i:03d}")
        factory.role(uid, t["group"], "user")
        extra.append(uid)

    everyone = [t["org"], *t["members"], *extra]  # 12 人
    assert _svc().start_game_service(t["group"], t["org"], "大局", everyone)["message"] == "tooManyPlayers"

    game_id = _start(t, players=everyone[:10])
    assert _svc().add_player_to_game_service(game_id, t["group"], everyone[10], t["org"])["message"] == "gameFull"

    # 同一个人不能同时在两局
    game2 = _start(t, players=[t["org"], everyone[11]], name="二号桌")
    result = _svc().add_player_to_game_service(game2, t["group"], t["members"][0], t["org"])
    assert result["message"] == "playerAlreadyInAnotherGame"

    _start(t, players=[t["org"]], name="三号桌")
    assert _svc().start_game_service(t["group"], t["org"], "四号桌", [t["org"]])["message"] == "tooManyOngoingGames"


def test_proxy_buy_in_requires_player_permission(table):
    from poker.services.user.game import update_chip_auth_service

    t = table
    alice = t["members"][0]
    game_id = _start(t)

    result = _svc().organizer_proxy_buyin_service(game_id, t["group"], t["org"], alice, 100)
    assert result["message"] == "proxyBuyinNotAuthorized"

    assert update_chip_auth_service(alice, t["group"], 1)["success"] is True
    assert _svc().organizer_proxy_buyin_service(game_id, t["group"], t["org"], alice, 100)["success"] is True
    assert _player(game_id, alice).total_buy_in == 100


def test_organizer_cannot_touch_other_groups_game(client, factory, table, login_as):
    t = table
    game_id = _start(t)

    other_group = factory.group("G2")
    other_org = factory.user("orgbbbb1")
    factory.role(other_org, other_group, "organizer")
    login_as("orgbbbb1", other_group)

    response = client.post(
        "/organizer/game/organizer-buyin",
        data={"game_id": game_id, "user_id": t["members"][0], "amount": 100},
    )
    assert response.json()["message"] == "gameNotFound"
    assert _player(game_id, t["members"][0]).total_buy_in == 0


def test_organizer_buyin_only_buys_for_the_organizer(client, table, login_as):
    t = table
    game_id = _start(t)
    alice = t["members"][0]
    login_as("orgaaaa1", t["group"])

    # 表单里填别人的 user_id 也只会记在局头本人名下
    response = client.post(
        "/organizer/game/organizer-buyin",
        data={"game_id": game_id, "user_id": alice, "amount": 100},
    )
    assert response.json()["success"] is True
    assert _player(game_id, alice).total_buy_in == 0
    assert _player(game_id, t["org"]).total_buy_in == 100


def test_buy_in_request_over_http(client, table, login_as):
    t = table
    game_id = _start(t)
    login_as("alice001", t["group"])

    response = client.post("/user/game/buyin-request", data={"game_id": game_id, "amount": 2_000_000})
    assert response.json()["message"] == "amountTooLarge"
    assert client.post("/user/game/buyin-request", data={"game_id": game_id, "amount": 100}).json()["success"] is True


# ───────────────────────── 同时操作 ─────────────────────────

def test_double_approve_adds_only_once(table):
    t = table
    alice = t["members"][0]
    game_id = _start(t)
    req = _request_buyin(game_id, t["group"], alice, 100)

    results = _run_concurrently(
        lambda _: _svc().approve_chip_request_service(req, game_id, t["group"], t["org"]),
        5,
    )

    assert sum(1 for r in results if r["success"]) == 1
    assert _player(game_id, alice).total_buy_in == 100


def test_concurrent_buy_ins_are_all_counted(table):
    t = table
    alice = t["members"][0]
    game_id = _start(t)

    results = _run_concurrently(lambda i: _buyin(t, game_id, alice, 10 + i), 8)

    assert all(r["success"] for r in results), results
    assert _player(game_id, alice).total_buy_in == sum(10 + i for i in range(8))


def test_approve_and_reject_race_has_one_winner(table):
    t = table
    alice = t["members"][0]
    game_id = _start(t)
    req = _request_buyin(game_id, t["group"], alice, 100)

    def act(i):
        if i % 2 == 0:
            return ("approve", _svc().approve_chip_request_service(req, game_id, t["group"], t["org"]))
        return ("reject", _svc().reject_chip_request_service(req, game_id, t["group"], t["org"]))

    results = _run_concurrently(act, 6)
    winners = [kind for kind, r in results if r["success"]]
    assert len(winners) == 1
    assert _player(game_id, alice).total_buy_in == (100 if winners[0] == "approve" else 0)


def test_double_finish_settles_once(table):
    t = table
    alice = t["members"][0]
    game_id = _start(t, players=[t["org"], alice])
    _buyin(t, game_id, alice, 100)

    results = _run_concurrently(lambda _: _finish(t, game_id, {t["org"]: 0, alice: 100}), 4)
    assert sum(1 for r in results if r["success"]) == 1


def test_concurrent_add_same_player_once(table):
    t = table
    game_id = _start(t, players=[t["org"]])
    alice = t["members"][0]

    results = _run_concurrently(
        lambda _: _svc().add_player_to_game_service(game_id, t["group"], alice, t["org"]),
        5,
    )
    assert sum(1 for r in results if r["success"]) == 1


def test_concurrent_game_starts_respect_limit(table):
    t = table
    results = _run_concurrently(
        lambda i: _svc().start_game_service(t["group"], t["org"], f"桌{i}", [t["org"]]),
        6,
    )
    assert sum(1 for r in results if r["success"]) == 3


# ───────────────────────── 数据库规则 ─────────────────────────

def test_database_rejects_duplicates_and_negative_amounts(table):
    from sqlalchemy.exc import IntegrityError

    from database import SessionLocal
    from poker.models import ChipRequest, GroupMemberAlias, PokerGamePlayer, UserGroupRole

    t = table
    alice, bob = t["members"][0], t["members"][1]
    game_id = _start(t, players=[t["org"], alice])

    def must_fail(obj):
        db = SessionLocal()
        try:
            db.add(obj)
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()
        finally:
            db.close()

    must_fail(UserGroupRole(user_id=alice, group_id=t["group"], role="user"))
    must_fail(PokerGamePlayer(game_id=game_id, user_id=alice, nickname="x", total_buy_in=0, is_active=1))
    must_fail(PokerGamePlayer(game_id=game_id, user_id=bob, nickname="x", total_buy_in=-1, is_active=1))
    must_fail(PokerGamePlayer(game_id=game_id, user_id=bob, nickname="x", total_buy_in=0, cash_out=-1, is_active=1))
    must_fail(ChipRequest(game_id=game_id, user_id=alice, amount=0, status="pending"))

    db = SessionLocal()
    try:
        db.add(GroupMemberAlias(group_id=t["group"], user_id=alice, alias="A"))
        db.commit()
    finally:
        db.close()
    must_fail(GroupMemberAlias(group_id=t["group"], user_id=alice, alias="B"))


# ───────────────────────── 玩家进出 ─────────────────────────

def _request_status(req_id):
    from database import SessionLocal
    from poker.models import ChipRequest

    db = SessionLocal()
    try:
        return db.query(ChipRequest.status).filter(ChipRequest.id == req_id).scalar()
    finally:
        db.close()


def test_rejoining_player_still_respects_table_limit(factory, table):
    t = table
    game_id = _start(t)
    # 补满到 10 人
    for i in range(10 - 4):
        uid = factory.user(f"extra{i:03d}")
        factory.role(uid, t["group"], "user")
        assert _svc().add_player_to_game_service(game_id, t["group"], uid, t["org"])["success"] is True

    alice = t["members"][0]
    assert _svc().remove_player_from_game_service(game_id, t["group"], alice)["success"] is True
    newcomer = factory.user("newcomer1")
    factory.role(newcomer, t["group"], "user")
    assert _svc().add_player_to_game_service(game_id, t["group"], newcomer, t["org"])["success"] is True

    result = _svc().add_player_to_game_service(game_id, t["group"], alice, t["org"])
    assert result["message"] == "gameFull"


def test_rejoining_player_cannot_be_in_two_games(table):
    t = table
    alice, bob, carol = t["members"]
    first = _start(t, players=[t["org"], alice, bob])
    assert _svc().remove_player_from_game_service(first, t["group"], alice)["success"] is True
    second = _start(t, players=[t["org"], alice, carol], name="第二局")
    assert _player(second, alice).is_active == 1

    result = _svc().add_player_to_game_service(first, t["group"], alice, t["org"])
    assert result["message"] == "playerAlreadyInAnotherGame"


def test_removing_player_rejects_their_pending_requests(table):
    t = table
    alice = t["members"][0]
    game_id = _start(t)
    req = _request_buyin(game_id, t["group"], alice, 100)

    assert _svc().remove_player_from_game_service(game_id, t["group"], alice)["success"] is True
    assert _request_status(req) == "rejected"
    assert _svc().approve_chip_request_service(req, game_id, t["group"], t["org"])["message"] == "requestNotFound"
    assert _player(game_id, alice).total_buy_in == 0


def test_finishing_game_rejects_pending_requests(table):
    t = table
    alice, bob, carol = t["members"]
    game_id = _start(t)
    req = _request_buyin(game_id, t["group"], alice, 100)

    result = _finish(t, game_id, {t["org"]: 0, alice: 0, bob: 0, carol: 0})
    assert result["success"] is True, result
    assert _request_status(req) == "rejected"


def test_member_in_ongoing_game_cannot_be_removed_from_group(table):
    from poker.services.organizer.member_management import remove_member_service

    t = table
    alice = t["members"][0]
    _start(t)
    assert remove_member_service(t["group"], alice)["message"] == "removeMemberOngoingGame"


def test_organizer_cannot_delete_game_log(client, table, login_as):
    t = table
    game_id = _start(t)
    alice, bob, carol = t["members"]
    assert _finish(t, game_id, {t["org"]: 0, alice: 0, bob: 0, carol: 0})["success"] is True

    login_as("orgaaaa1", t["group"])
    response = client.post("/organizer/game-log/delete", data={"game_id": game_id})
    assert response.status_code in (404, 405)
    assert _game(game_id) is not None


def test_cash_out_taken_at_exit_is_added_at_finish(table):
    t = table
    alice, bob, carol = t["members"]
    game_id = _start(t)
    assert _buyin(t, game_id, t["org"], 100)["success"] is True
    req = _request_buyin(game_id, t["group"], alice, 100)
    assert _svc().approve_chip_request_service(req, game_id, t["group"], t["org"])["success"] is True

    # alice 结算离场拿走 80，回来后又买入 50，最后剩 70
    assert _svc().exit_player_from_game_service(game_id, t["group"], alice, 80)["success"] is True
    assert _svc().add_player_to_game_service(game_id, t["group"], alice, t["org"])["success"] is True
    req = _request_buyin(game_id, t["group"], alice, 50)
    assert _svc().approve_chip_request_service(req, game_id, t["group"], t["org"])["success"] is True

    result = _finish(t, game_id, {t["org"]: 100, alice: 70, bob: 0, carol: 0})
    assert result["success"] is True, result
    player = _player(game_id, alice)
    assert player.total_buy_in == 150
    assert player.left_cash_out == 80
    assert player.cash_out == 150  # 80 离场 + 70 结束时剩余
    assert player.net == 0
