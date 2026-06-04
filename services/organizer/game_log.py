from database import SessionLocal
from models import PokerGame
from models import PokerGamePlayer
from models import ChipRequest
from models import User
from models import UserGroupRole


PAGE_SIZE = 5


def get_game_logs_service(group_id: int, page: int = 1, viewer_user_id: int = None):
    db = SessionLocal()
    try:
        total = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
        ).count()

        games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
        ).order_by(PokerGame.ended_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()

        result = []
        for game in games:
            players = db.query(PokerGamePlayer, User).join(
                User, PokerGamePlayer.user_id == User.id
            ).filter(PokerGamePlayer.game_id == game.id).all()

            players_data = []
            top_winner = None
            top_net = None

            for p, u in players:
                net = p.net if p.net is not None else 0
                is_org = p.user_id == game.organizer_id
                pd = {
                    "user_id": p.user_id,
                    "nickname": p.nickname or u.username,
                    "is_organizer": is_org,
                    "total_buy_in": p.total_buy_in,
                    "cash_out": p.cash_out or 0,
                    "net": net,
                }

                # 每笔买入明细
                all_requests = db.query(ChipRequest).filter(
                    ChipRequest.game_id == game.id,
                    ChipRequest.user_id == p.user_id,
                    ChipRequest.status == "approved",
                ).order_by(ChipRequest.requested_at.asc()).all()

                # 局头看所有人明细，普通用户只看自己
                show_details = (viewer_user_id is None) or (p.user_id == viewer_user_id)
                pd["buyin_details"] = [
                    {
                        "amount": r.amount,
                        "type": r.type,
                        "time": r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "",
                    }
                    for r in all_requests
                ] if show_details else []

                if is_org:
                    breakdown = _get_buyin_breakdown(db, game.id, p.user_id)
                    pd["buy_in_normal"] = breakdown["normal"]
                    pd["buy_in_insurance"] = breakdown["insurance"]
                    pd["buy_in_anti"] = breakdown["anti"]

                if top_net is None or net > top_net:
                    top_net = net
                    top_winner = p.user_id

                players_data.append(pd)

            duration = ""
            if game.started_at and game.ended_at:
                delta = game.ended_at - game.started_at
                h, rem = divmod(int(delta.total_seconds()), 3600)
                m = rem // 60
                duration = f"{h}h {m}m"

            result.append({
                "id": game.id,
                "name": game.name or "",
                "started_at": game.started_at.strftime("%Y-%m-%d %H:%M") if game.started_at else "",
                "ended_at": game.ended_at.strftime("%Y-%m-%d %H:%M") if game.ended_at else "",
                "duration": duration,
                "total_buy_in": game.total_buy_in or 0,
                "total_cash_out": game.total_cash_out or 0,
                "is_balanced": game.is_balanced,
                "player_count": game.player_count or 0,
                "top_winner_id": top_winner,
                "players": players_data,
            })

        return {
            "success": True,
            "games": result,
            "total": total,
            "page": page,
            "page_size": PAGE_SIZE,
            "total_pages": max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def get_stats_service(group_id: int):
    db = SessionLocal()
    try:
        # 获取组内局头 user_id
        organizer_roles = db.query(UserGroupRole).filter(
            UserGroupRole.group_id == group_id,
            UserGroupRole.role == "organizer",
        ).all()
        organizer_ids = {r.user_id for r in organizer_roles}

        finished_games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
        ).all()

        game_ids = [g.id for g in finished_games]

        if not game_ids:
            return {"success": True, "stats": None}

        all_players = db.query(PokerGamePlayer, User).join(
            User, PokerGamePlayer.user_id == User.id
        ).filter(
            PokerGamePlayer.game_id.in_(game_ids),
        ).all()

        # 按用户聚合，排除局头
        user_stats = {}
        for p, u in all_players:
            if p.user_id in organizer_ids:
                continue
            uid = p.user_id
            net = p.net if p.net is not None else 0
            if uid not in user_stats:
                user_stats[uid] = {
                    "nickname": p.nickname or u.username,
                    "win_count": 0,
                    "lose_count": 0,
                    "total_net": 0,
                    "game_count": 0,
                }
            user_stats[uid]["game_count"] += 1
            user_stats[uid]["total_net"] += net
            if net > 0:
                user_stats[uid]["win_count"] += 1
            elif net < 0:
                user_stats[uid]["lose_count"] += 1

        if not user_stats:
            return {"success": True, "stats": None}

        # 水上次数最多（至少有1次才显示）
        most_wins = max(user_stats.values(), key=lambda x: x["win_count"])
        if most_wins["win_count"] == 0:
            most_wins_name = []
        else:
            most_wins_name = [v["nickname"] for v in user_stats.values() if v["win_count"] == most_wins["win_count"]]

        # 水下次数最多（至少有1次才显示）
        most_loses = max(user_stats.values(), key=lambda x: x["lose_count"])
        if most_loses["lose_count"] == 0:
            most_loses_name = []
        else:
            most_loses_name = [v["nickname"] for v in user_stats.values() if v["lose_count"] == most_loses["lose_count"]]

        # 总体盈利最多（net > 0 才显示）
        most_profit = max(user_stats.values(), key=lambda x: x["total_net"])
        if most_profit["total_net"] <= 0:
            most_profit_name = []
        else:
            most_profit_name = [v["nickname"] for v in user_stats.values() if v["total_net"] == most_profit["total_net"]]

        # 总体亏损最多（net < 0 才显示）
        most_loss = min(user_stats.values(), key=lambda x: x["total_net"])
        if most_loss["total_net"] >= 0:
            most_loss_name = []
        else:
            most_loss_name = [v["nickname"] for v in user_stats.values() if v["total_net"] == most_loss["total_net"]]

        # 参与次数最多
        most_games = max(user_stats.values(), key=lambda x: x["game_count"])
        most_games_name = [v["nickname"] for v in user_stats.values() if v["game_count"] == most_games["game_count"]]

        # 最长牌局
        longest_game = None
        longest_duration = 0
        for g in finished_games:
            if g.started_at and g.ended_at:
                delta = (g.ended_at - g.started_at).total_seconds()
                if delta > longest_duration:
                    longest_duration = delta
                    longest_game = g

        longest_str = ""
        if longest_duration > 0:
            h, rem = divmod(int(longest_duration), 3600)
            m = rem // 60
            longest_str = f"{h}h {m}m"

        # 最大总筹码
        max_chips_game = max(finished_games, key=lambda g: g.total_buy_in or 0)

        return {
            "success": True,
            "stats": {
                "most_wins": {"names": most_wins_name, "count": most_wins["win_count"]},
                "most_loses": {"names": most_loses_name, "count": most_loses["lose_count"]},
                "most_profit": {"names": most_profit_name, "amount": most_profit["total_net"]},
                "most_loss": {"names": most_loss_name, "amount": most_loss["total_net"]},
                "most_games": {"names": most_games_name, "count": most_games["game_count"]},
                "longest_game": {"duration": longest_str, "name": longest_game.name or longest_game.started_at.strftime("%Y-%m-%d") if longest_game else ""},
                "max_chips": {"amount": max_chips_game.total_buy_in or 0, "name": max_chips_game.name or max_chips_game.started_at.strftime("%Y-%m-%d") if max_chips_game else ""},
            },
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def _get_buyin_breakdown(db, game_id: int, user_id: int) -> dict:
    requests = db.query(ChipRequest).filter(
        ChipRequest.game_id == game_id,
        ChipRequest.user_id == user_id,
        ChipRequest.status == "approved",
    ).all()

    breakdown = {"normal": 0, "insurance": 0, "anti": 0}
    for r in requests:
        t = r.type if r.type in breakdown else "normal"
        breakdown[t] += r.amount
    return breakdown


def delete_game_log_service(game_id: int, group_id: int):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        db.query(ChipRequest).filter(ChipRequest.game_id == game_id).delete(synchronize_session=False)
        db.query(PokerGamePlayer).filter(PokerGamePlayer.game_id == game_id).delete(synchronize_session=False)
        db.delete(game)
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()