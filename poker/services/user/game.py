from datetime import timedelta

from core.time import now_columbus_naive
from database import SessionLocal
from poker.models import ChipRequest
from poker.models import GameEvent
from poker.models import PokerGame
from poker.models import PokerGamePlayer
from poker.models import User
from poker.models import UserGroupRole
from core.errors import safe_error
from poker.services.common.game_events import record_game_event
from poker.core.validators import check_amount


# 局头代买时，申请记录和事件是在同一个操作里写入的，时间几乎相同
_PROXY_MATCH_WINDOW = timedelta(seconds=2)


def _my_status(db, game_id, player):
    """自己在这局里的状态：active 在桌上 | away 暂离 | exited 结算离场（看最近一次离开是哪一种）。"""
    if player.is_active:
        return "active"
    last_leave = db.query(GameEvent.event_type).filter(
        GameEvent.game_id == game_id,
        GameEvent.target_user_id == player.user_id,
        GameEvent.event_type.in_(("player_removed", "player_exited")),
    ).order_by(GameEvent.id.desc()).first()
    if last_leave is not None:
        return "exited" if last_leave[0] == "player_exited" else "away"
    # 没有事件记录的旧数据：有离场卖出就算结算离场
    return "exited" if player.cash_out is not None else "away"


def _my_requests(db, game_id, user_id):
    """
    自己的申请记录。source 区分来源：
      self      自己提交的申请
      proxy     局头代买（没有经过申请，直接记为已批准）
    rejected 的记录再用 rejected_by 区分：organizer 局头拒绝 | auto 离开牌局或牌局结束时自动拒绝。
    """
    reqs = db.query(ChipRequest).filter(
        ChipRequest.game_id == game_id,
        ChipRequest.user_id == user_id,
    ).order_by(ChipRequest.requested_at.desc(), ChipRequest.id.desc()).all()

    proxy_times = [
        (row[0], row[1]) for row in db.query(GameEvent.created_at, GameEvent.amount).filter(
            GameEvent.game_id == game_id,
            GameEvent.target_user_id == user_id,
            GameEvent.event_type == "proxy_buyin",
        ).all()
    ]

    def is_proxy(r):
        if r.status != "approved" or r.resolved_by is None or r.resolved_by == user_id:
            return False
        for index, (created_at, amount) in enumerate(proxy_times):
            if amount == r.amount and created_at and r.requested_at \
                    and abs(created_at - r.requested_at) <= _PROXY_MATCH_WINDOW:
                proxy_times.pop(index)
                return True
        return False

    result = []
    for r in reqs:
        item = {
            "id": r.id,
            "amount": r.amount,
            "status": r.status,
            "source": "proxy" if is_proxy(r) else "self",
            "requested_at": r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "",
        }
        if r.status == "rejected":
            item["rejected_by"] = "organizer" if r.resolved_by is not None else "auto"
        result.append(item)
    return result


def get_user_ongoing_games_service(group_id: int, user_id: int):
    db = SessionLocal()
    try:
        # 包括自己已经暂离或结算离场的牌局：牌局还没结束，页面上要告诉他当前的状态
        my_records = {
            p.game_id: p
            for p in db.query(PokerGamePlayer).filter(PokerGamePlayer.user_id == user_id).all()
        }

        games = db.query(PokerGame).filter(
            PokerGame.id.in_(list(my_records.keys())),
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).order_by(PokerGame.started_at.asc()).all() if my_records else []

        organizer_ids = set()
        if games:
            organizer_ids = {
                r.user_id for r in db.query(UserGroupRole).filter(
                    UserGroupRole.group_id == group_id,
                    UserGroupRole.role == "organizer",
                ).all()
            }

        result = []
        for game in games:
            my_player = my_records[game.id]
            my_status = _my_status(db, game.id, my_player)

            # 在桌上时看到所有在桌玩家；已经离开时只看到自己的记录（和以前一样，不多给别人的信息）
            players_query = db.query(PokerGamePlayer, User).join(
                User, PokerGamePlayer.user_id == User.id
            ).filter(PokerGamePlayer.game_id == game.id)
            if my_status == "active":
                players_query = players_query.filter(PokerGamePlayer.is_active == 1)
            else:
                players_query = players_query.filter(PokerGamePlayer.user_id == user_id)

            players_data = []
            for p, u in players_query.all():
                is_me = p.user_id == user_id
                players_data.append({
                    "user_id": p.user_id,
                    "nickname": p.nickname or u.username,
                    "avatar_url": u.avatar_url or "",
                    "is_organizer": p.user_id in organizer_ids,
                    "is_me": is_me,
                    "total_buy_in": p.total_buy_in or 0,
                    # 只有自己才能看到申请记录
                    "requests": _my_requests(db, game.id, user_id) if is_me else [],
                })

            # 局头排前面
            players_data.sort(key=lambda x: (not x["is_organizer"], not x["is_me"]))

            game_data = {
                "id": game.id,
                "name": game.name or "",
                "started_at": game.started_at.strftime("%Y-%m-%d %H:%M") if game.started_at else "",
                "my_buy_in": my_player.total_buy_in or 0,
                "my_status": my_status,
                "players": players_data,
            }
            if my_status == "exited":
                cash_out = my_player.left_cash_out or 0
                game_data["my_cash_out"] = cash_out
                game_data["my_net"] = cash_out - (my_player.total_buy_in or 0)
            result.append(game_data)

        # 不在任何牌局里时，告诉他组里现在有没有进行中的牌局
        group_ongoing_count = db.query(PokerGame.id).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).count()

        return {"success": True, "games": result, "group_ongoing_count": group_ongoing_count}
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def get_chip_auth_settings_service(user_id: int):
    """获取用户在所有组里的局头筹码授权状态"""
    db = SessionLocal()
    try:
        from poker.models import Group
        records = db.query(UserGroupRole, Group).join(
            Group, UserGroupRole.group_id == Group.id
        ).filter(
            UserGroupRole.user_id == user_id,
            UserGroupRole.role == "user",
        ).all()

        settings = []
        for ugr, grp in records:
            settings.append({
                "group_id": grp.id,
                "group_name": grp.group_name or grp.group_code,
                "allow_organizer_chip_op": ugr.allow_organizer_chip_op or 0,
            })

        return {"success": True, "settings": settings}
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def update_chip_auth_service(user_id: int, group_id: int, allow: int):
    """更新某个组的局头筹码授权"""
    db = SessionLocal()
    try:
        ugr = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id,
            UserGroupRole.group_id == group_id,
            UserGroupRole.role == "user",
        ).first()

        if not ugr:
            return {"success": False, "message": "recordNotFound"}

        ugr.allow_organizer_chip_op = 1 if allow else 0
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def submit_buyin_request_service(game_id: int, group_id: int, user_id: int, amount: int):
    db = SessionLocal()
    try:
        # 锁住这一局，避免申请和结算同时发生，在已结束的局里留下待处理申请
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).with_for_update().first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
            PokerGamePlayer.is_active == 1,
        ).first()

        if not player:
            return {"success": False, "message": "notInGame"}

        amount_error = check_amount(amount)
        if amount_error:
            return {"success": False, "message": amount_error}

        # 每人同时只能有一条待审批的申请，防止刷出大量申请
        pending = db.query(ChipRequest.id).filter(
            ChipRequest.game_id == game_id,
            ChipRequest.user_id == user_id,
            ChipRequest.status == "pending",
        ).first()
        if pending:
            return {"success": False, "message": "buyinRequestPending"}

        user = db.query(User).filter(User.id == user_id).first()

        req = ChipRequest(
            game_id=game_id,
            user_id=user_id,
            nickname=user.nickname or user.username if user else "",
            type="normal",
            amount=amount,
            status="pending",
            requested_at=now_columbus_naive(),
        )
        db.add(req)
        record_game_event(db, game_id, "buyin_requested", actor_user_id=user_id, target_user_id=user_id, amount=amount, buy_type="normal")
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()