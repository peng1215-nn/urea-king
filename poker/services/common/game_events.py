"""
牌局审计记录：在各个牌局操作里调用 record_game_event()，和操作本身在同一个事务里提交。

事件类型（前端 i18n/game_report.js 里有对应的中英文说明，增加类型时一起加）：
  game_started         开局（details.players：开局时的玩家）
  player_added         加入牌局
  player_rejoined      被移出或离场后重新加入
  player_removed       被局头移出牌局
  player_exited        中途结算离场（amount：卖出数额）
  buyin_requested      玩家申请买入（amount、buy_type）
  buyin_approved       局头批准申请
  buyin_rejected       局头拒绝申请
  buyin_auto_rejected  玩家离开牌局或牌局结束时，未审批的申请被自动拒绝
  organizer_buyin      局头给自己买入
  proxy_buyin          局头代玩家买入（玩家已开启授权）
  game_finished        牌局结束（details：每位玩家的买入、卖出、盈亏，是否平衡、是否强制结束）
"""

import json

from core.time import now_columbus_naive
from poker.models import GameEvent, PokerGame, PokerGamePlayer, User


EVENT_TYPES = (
    "game_started",
    "player_added",
    "player_rejoined",
    "player_removed",
    "player_exited",
    "buyin_requested",
    "buyin_approved",
    "buyin_rejected",
    "buyin_auto_rejected",
    "organizer_buyin",
    "proxy_buyin",
    "game_finished",
)


def display_name(db, user_id):
    """用户当前的显示名（昵称，没有昵称时用用户名），作为快照存进事件。"""
    if user_id is None:
        return None
    row = db.query(User.nickname, User.username).filter(User.id == user_id).first()
    if row is None:
        return None
    return row[0] or row[1]


def record_game_event(
    db,
    game_id,
    event_type,
    actor_user_id=None,
    target_user_id=None,
    amount=None,
    buy_type=None,
    details=None,
):
    """追加一条事件（不提交，由调用方和操作一起提交）。"""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unknown game event type: {event_type}")

    db.add(GameEvent(
        game_id=game_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_name=display_name(db, actor_user_id),
        target_user_id=target_user_id,
        target_name=display_name(db, target_user_id),
        amount=amount,
        buy_type=buy_type,
        details=json.dumps(details, ensure_ascii=False) if details is not None else None,
        created_at=now_columbus_naive(),
    ))


def _format_time(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def build_game_report(db, game_id, group_id):
    """
    审计报告数据：牌局概况、事件时间线、按玩家汇总，并与结算结果核对。
    只返回该组已结束的牌局；找不到时返回 None。
    """
    game = db.query(PokerGame).filter(
        PokerGame.id == game_id,
        PokerGame.group_id == group_id,
        PokerGame.status == "finished",
    ).first()
    if game is None:
        return None

    events = db.query(GameEvent).filter(GameEvent.game_id == game_id).order_by(GameEvent.id).all()
    players = db.query(PokerGamePlayer).filter(PokerGamePlayer.game_id == game_id).all()

    # 按事件累加每位玩家的买入，用来和结算结果核对
    buy_in_from_events = {}
    buy_in_by_type = {}
    for event in events:
        if event.event_type in ("buyin_approved", "organizer_buyin", "proxy_buyin") and event.amount:
            uid = event.target_user_id
            buy_in_from_events[uid] = buy_in_from_events.get(uid, 0) + event.amount
            by_type = buy_in_by_type.setdefault(uid, {"normal": 0, "insurance": 0, "anti": 0})
            key = event.buy_type if event.buy_type in by_type else "normal"
            by_type[key] += event.amount

    summary = []
    for player in sorted(players, key=lambda p: -(p.net or 0)):
        from_events = buy_in_from_events.get(player.user_id, 0)
        summary.append({
            "user_id": player.user_id,
            "nickname": player.nickname,
            "total_buy_in": player.total_buy_in or 0,
            "buy_in_by_type": buy_in_by_type.get(player.user_id, {"normal": 0, "insurance": 0, "anti": 0}),
            "buy_in_from_events": from_events,
            "cash_out": player.cash_out or 0,
            "net": player.net or 0,
            "matches": from_events == (player.total_buy_in or 0),
        })

    has_events = bool(events)
    return {
        "success": True,
        "game": {
            "id": game.id,
            "name": game.name or "",
            "note": game.note or "",
            "started_at": _format_time(game.started_at),
            "ended_at": _format_time(game.ended_at),
            "total_buy_in": game.total_buy_in or 0,
            "total_cash_out": game.total_cash_out or 0,
            "is_balanced": bool(game.is_balanced),
        },
        "has_events": has_events,
        # 没有事件记录（审计功能上线前的牌局）时不做核对
        "all_match": has_events and all(row["matches"] for row in summary),
        "summary": summary,
        "events": [
            {
                "id": event.id,
                "time": _format_time(event.created_at),
                "type": event.event_type,
                "actor_name": event.actor_name or "",
                "target_name": event.target_name or "",
                "amount": event.amount,
                "buy_type": event.buy_type or "",
                "details": json.loads(event.details) if event.details else None,
            }
            for event in events
        ],
    }
