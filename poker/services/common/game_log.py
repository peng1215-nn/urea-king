from database import SessionLocal
from poker.models import GroupMemberAlias
from poker.models import PokerGame
from poker.models import PokerGamePlayer
from poker.models import ChipRequest
from poker.models import GameEvent
from poker.models import User
from poker.models import UserGroupRole
from core.errors import safe_error


def _get_aliases(db, group_id: int) -> dict:
    rows = db.query(GroupMemberAlias).filter(
        GroupMemberAlias.group_id == group_id
    ).all()
    return {r.user_id: r.alias for r in rows}


def _display(nickname: str, alias: str) -> str:
    return f"{nickname}（{alias}）" if alias else nickname


PAGE_SIZE = 5


def _game_label(game):
    """牌局的显示名：有名字用名字，否则用开始日期。"""
    if game is None:
        return ""
    return game.name or (game.started_at.strftime("%Y-%m-%d") if game.started_at else "")


def get_game_logs_service(group_id: int, page: int = 1, viewer_user_id: int = None, q: str = ""):
    db = SessionLocal()
    try:
        aliases = _get_aliases(db, group_id)
        base_filter = [
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
        ]
        if q:
            from sqlalchemy import or_
            base_filter.append(or_(
                PokerGame.name.ilike(f"%{q}%"),
                PokerGame.note.ilike(f"%{q}%"),
            ))

        total = db.query(PokerGame).filter(*base_filter).count()

        games = db.query(PokerGame).filter(*base_filter).order_by(PokerGame.ended_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()

        # 一次取出本页所有牌局的玩家和买入记录，避免每局、每个玩家各查一次数据库
        game_ids = [game.id for game in games]

        players_by_game = {}
        requests_by_player = {}
        if game_ids:
            for p, u in db.query(PokerGamePlayer, User).join(
                User, PokerGamePlayer.user_id == User.id
            ).filter(PokerGamePlayer.game_id.in_(game_ids)).order_by(PokerGamePlayer.id).all():
                players_by_game.setdefault(p.game_id, []).append((p, u))

            for r in db.query(ChipRequest).filter(
                ChipRequest.game_id.in_(game_ids),
                ChipRequest.status == "approved",
            ).order_by(ChipRequest.requested_at.asc(), ChipRequest.id.asc()).all():
                requests_by_player.setdefault((r.game_id, r.user_id), []).append(r)

        result = []
        for game in games:
            players_data = []
            top_winner = None
            top_net = None

            for p, u in players_by_game.get(game.id, []):
                net = p.net if p.net is not None else 0
                is_org = p.user_id == game.organizer_id
                raw_nick = p.nickname or u.username
                pd = {
                    "user_id": p.user_id,
                    "nickname": _display(raw_nick, aliases.get(p.user_id, "")),
                    "is_organizer": is_org,
                    "total_buy_in": p.total_buy_in,
                    "cash_out": p.cash_out or 0,
                    "net": net,
                    # 是不是正在查看的人自己（只有普通成员的日志接口会传 viewer_user_id）
                    "is_me": viewer_user_id is not None and p.user_id == viewer_user_id,
                }

                # 每笔买入明细
                all_requests = requests_by_player.get((game.id, p.user_id), [])

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
                    breakdown = _sum_by_type(all_requests)
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

            my_row = next((pd for pd in players_data if pd["is_me"]), None)

            result.append({
                "id": game.id,
                "name": game.name or "",
                "note": game.note or "",
                # 查看者自己这局的盈亏；没参加这局时为 None
                "my_net": my_row["net"] if my_row else None,
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
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def get_stats_service(group_id: int):
    db = SessionLocal()
    try:
        aliases = _get_aliases(db, group_id)
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
        games_by_id = {g.id: g for g in finished_games}

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
                raw_nick = p.nickname or u.username
                user_stats[uid] = {
                    "nickname": _display(raw_nick, aliases.get(uid, "")),
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

        # 最高单局盈利
        best_single = None
        best_single_net = 0
        best_single_nickname = ""
        for p, u in all_players:
            if p.user_id in organizer_ids:
                continue
            net = p.net if p.net is not None else 0
            if net > best_single_net:
                best_single_net = net
                best_single_nickname = _display(p.nickname or u.username, aliases.get(p.user_id, ""))
                best_single = _game_label(games_by_id.get(p.game_id))

        # 最惨单局亏损
        worst_single = None
        worst_single_net = 0
        worst_single_nickname = ""
        for p, u in all_players:
            if p.user_id in organizer_ids:
                continue
            net = p.net if p.net is not None else 0
            if net < worst_single_net:
                worst_single_net = net
                worst_single_nickname = _display(p.nickname or u.username, aliases.get(p.user_id, ""))
                worst_single = _game_label(games_by_id.get(p.game_id))

        # 每个玩家水上率水下率
        player_rates = []
        for uid, stats in user_stats.items():
            gc = stats["game_count"]
            win_rate = round(stats["win_count"] / gc * 100) if gc > 0 else 0
            lose_rate = round(stats["lose_count"] / gc * 100) if gc > 0 else 0
            player_rates.append({
                "nickname": stats["nickname"],
                "game_count": gc,
                "win_count": stats["win_count"],
                "lose_count": stats["lose_count"],
                "win_rate": win_rate,
                "lose_rate": lose_rate,
                "total_net": stats["total_net"],
            })
        player_rates.sort(key=lambda x: x["win_rate"], reverse=True)

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
                "best_single": {"nickname": best_single_nickname, "amount": best_single_net, "game": best_single or ""},
                "worst_single": {"nickname": worst_single_nickname, "amount": worst_single_net, "game": worst_single or ""},
                "player_rates": player_rates,
            },
        }
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def _sum_by_type(requests) -> dict:
    breakdown = {"normal": 0, "insurance": 0, "anti": 0}
    for r in requests:
        t = r.type if r.type in breakdown else "normal"
        breakdown[t] += r.amount
    return breakdown


def _get_buyin_breakdown(db, game_id: int, user_id: int) -> dict:
    requests = db.query(ChipRequest).filter(
        ChipRequest.game_id == game_id,
        ChipRequest.user_id == user_id,
        ChipRequest.status == "approved",
    ).all()
    return _sum_by_type(requests)


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

        db.query(GameEvent).filter(GameEvent.game_id == game_id).delete(synchronize_session=False)
        db.query(ChipRequest).filter(ChipRequest.game_id == game_id).delete(synchronize_session=False)
        db.query(PokerGamePlayer).filter(PokerGamePlayer.game_id == game_id).delete(synchronize_session=False)
        db.delete(game)
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()

def get_member_stats_service(group_id: int):
    db = SessionLocal()
    try:
        finished_games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
        ).all()

        game_ids = [g.id for g in finished_games]

        if not game_ids:
            return {"success": True, "members": []}

        all_players = db.query(PokerGamePlayer, User).join(
            User, PokerGamePlayer.user_id == User.id
        ).filter(
            PokerGamePlayer.game_id.in_(game_ids),
        ).all()

        aliases = _get_aliases(db, group_id)
        user_stats = {}
        for p, u in all_players:
            uid = p.user_id
            net = p.net if p.net is not None else 0
            if uid not in user_stats:
                raw_nick = p.nickname or u.username
                user_stats[uid] = {
                    "user_id": uid,
                    "nickname": _display(raw_nick, aliases.get(uid, "")),
                    "win_count": 0,
                    "lose_count": 0,
                    "game_count": 0,
                    "total_net": 0,
                }
            user_stats[uid]["game_count"] += 1
            user_stats[uid]["total_net"] += net
            if net > 0:
                user_stats[uid]["win_count"] += 1
            elif net < 0:
                user_stats[uid]["lose_count"] += 1

        members = []
        for uid, s in user_stats.items():
            game_count = s["game_count"]
            win_rate = round(s["win_count"] / game_count * 100, 1) if game_count > 0 else 0
            lose_rate = round(s["lose_count"] / game_count * 100, 1) if game_count > 0 else 0
            members.append({
                "user_id": uid,
                "nickname": s["nickname"],
                "game_count": game_count,
                "win_count": s["win_count"],
                "lose_count": s["lose_count"],
                "win_rate": win_rate,
                "lose_rate": lose_rate,
                "total_net": s["total_net"],
            })

        # 按总盈亏降序排列
        members.sort(key=lambda x: x["total_net"], reverse=True)

        return {"success": True, "members": members}
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def get_member_trend_service(group_id: int, user_id: int):
    db = SessionLocal()
    try:
        records = db.query(PokerGame, PokerGamePlayer).join(
            PokerGamePlayer, PokerGame.id == PokerGamePlayer.game_id
        ).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
            PokerGamePlayer.user_id == user_id,
        ).order_by(PokerGame.ended_at.asc()).all()

        points = []
        cumulative = 0
        for game, player in records:
            net = player.net if player.net is not None else 0
            cumulative += net
            points.append({
                "game_name": game.name or game.started_at.strftime("%m/%d") if game.started_at else str(game.id),
                "date": game.ended_at.strftime("%Y-%m-%d") if game.ended_at else "",
                "net": net,
                "cumulative": cumulative,
                "buy_in": player.total_buy_in or 0,
                "cash_out": player.cash_out or 0,
            })

        return {"success": True, "points": points}
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()
