"""
牌局日志与统计：内容正确，且每页的数据库查询次数不随玩家、买入笔数增长。
"""

import pytest


@pytest.fixture
def played(factory):
    """一个组打完 6 局。第 6 局（最新）里有买入申请、局头保险买入和备注名。"""
    from poker.services.organizer import game_management as gm
    from poker.services.user.game import submit_buyin_request_service

    group_id = factory.group("G1", name="周五局")
    org = factory.user("orgaaaa1")
    factory.role(org, group_id, "organizer")
    alice = factory.user("alice001")
    bob = factory.user("bobby001")
    for uid in (alice, bob):
        factory.role(uid, group_id, "user")

    from database import SessionLocal
    from poker.models import ChipRequest, GroupMemberAlias

    db = SessionLocal()
    db.add(GroupMemberAlias(group_id=group_id, user_id=bob, alias="B哥"))
    db.commit()
    db.close()

    games = []
    for i in range(6):
        game_id = gm.start_game_service(group_id, org, f"第{i + 1}局", [org, alice, bob])["game_id"]
        gm.organizer_buyin_service(game_id, group_id, bob, 100)

        if i == 5:
            assert submit_buyin_request_service(game_id, group_id, alice, 100)["success"]
            db = SessionLocal()
            req_id = db.query(ChipRequest.id).filter(
                ChipRequest.game_id == game_id, ChipRequest.status == "pending"
            ).scalar()
            db.close()
            assert gm.approve_chip_request_service(req_id, game_id, group_id, org)["success"]
            gm.organizer_buyin_service(game_id, group_id, org, 20, buy_type="insurance")
            cash = {org: 0, alice: 220, bob: 0}  # 买入 220：alice +120, bob -100, org -20
        else:
            gm.organizer_buyin_service(game_id, group_id, alice, 100)
            cash = {org: 0, alice: 150, bob: 50}  # alice +50, bob -50

        result = gm.finish_game_service(
            game_id=game_id, group_id=group_id, organizer_id=org,
            player_cash_outs=[{"user_id": u, "cash_out": c} for u, c in cash.items()],
        )
        assert result["success"], result
        games.append(game_id)

    return {"group": group_id, "org": org, "alice": alice, "bob": bob, "games": games}


def _logs(t, page=1, viewer=None):
    from poker.services.common.game_log import get_game_logs_service

    result = get_game_logs_service(t["group"], page=page, viewer_user_id=viewer)
    assert result["success"], result
    return result


def _player(game, user_id):
    return next(p for p in game["players"] if p["user_id"] == user_id)


def test_pagination(played):
    first = _logs(played, page=1)
    assert first["total"] == 6
    assert first["total_pages"] == 2
    assert len(first["games"]) == 5
    assert len(_logs(played, page=2)["games"]) == 1


def test_game_details(played):
    t = played
    latest = _logs(t)["games"][0]
    assert latest["name"] == "第6局"
    assert latest["top_winner_id"] == t["alice"]

    alice = _player(latest, t["alice"])
    assert alice["net"] == 120
    assert [d["amount"] for d in alice["buyin_details"]] == [100]

    bob = _player(latest, t["bob"])
    assert bob["nickname"] == "bobby001（B哥）"
    assert bob["net"] == -100

    org = _player(latest, t["org"])
    assert org["is_organizer"] is True
    assert (org["buy_in_normal"], org["buy_in_insurance"], org["buy_in_anti"]) == (0, 20, 0)


def test_members_only_see_their_own_buy_in_details(played):
    t = played
    latest = _logs(t, viewer=t["alice"])["games"][0]
    assert len(_player(latest, t["alice"])["buyin_details"]) == 1
    assert _player(latest, t["bob"])["buyin_details"] == []


def test_stats(played):
    from poker.services.common.game_log import get_stats_service

    stats = get_stats_service(played["group"])["stats"]
    assert stats["best_single"] == {"nickname": "alice001", "amount": 120, "game": "第6局"}
    # 最惨单局也显示备注名（之前漏了）
    assert stats["worst_single"] == {"nickname": "bobby001（B哥）", "amount": -100, "game": "第6局"}
    assert stats["most_profit"] == {"names": ["alice001"], "amount": 370}


def _count_queries(func):
    from sqlalchemy import event

    from database import engine

    count = {"n": 0}

    def before(*args, **kwargs):
        count["n"] += 1

    event.listen(engine, "before_cursor_execute", before)
    try:
        func()
    finally:
        event.remove(engine, "before_cursor_execute", before)
    return count["n"]


def test_game_log_page_uses_a_fixed_number_of_queries(played):
    # 之前每局、每个玩家各查一次，一页 5 局 3 人要 30 多次；现在与人数、笔数无关
    assert _count_queries(lambda: _logs(played)) <= 6


def test_stats_use_a_fixed_number_of_queries(played):
    from poker.services.common.game_log import get_stats_service

    assert _count_queries(lambda: get_stats_service(played["group"])) <= 6


def test_old_history_endpoint_is_removed(client, played, login_as):
    login_as("orgaaaa1", played["group"])
    response = client.get("/organizer/game/history", headers={"accept": "application/json"})
    assert response.status_code == 404
