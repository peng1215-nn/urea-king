from datetime import datetime
from database import SessionLocal
from models import ChipRequest
from models import PokerGame
from models import PokerGamePlayer
from models import User
from models import UserGroupRole


MAX_PLAYERS = 10


def get_ongoing_games_service(group_id: int):
    db = SessionLocal()
    try:
        games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).order_by(PokerGame.started_at.asc()).all()

        if not games:
            return {"success": True, "games": []}

        result = []
        for game in games:
            players = db.query(PokerGamePlayer, User).join(
                User, PokerGamePlayer.user_id == User.id
            ).filter(PokerGamePlayer.game_id == game.id).all()

            requests = db.query(ChipRequest, User).join(
                User, ChipRequest.user_id == User.id
            ).filter(
                ChipRequest.game_id == game.id,
                ChipRequest.status == "pending",
            ).order_by(ChipRequest.requested_at.desc()).all()

            players_data = []
            for p, u in players:
                pd = _format_player(p, u)
                if u.id == game.organizer_id:
                    breakdown = _get_buyin_breakdown(db, game.id, u.id)
                    pd["buy_in_normal"] = breakdown["normal"]
                    pd["buy_in_insurance"] = breakdown["insurance"]
                    pd["buy_in_anti"] = breakdown["anti"]
                players_data.append(pd)

            result.append({
                **_format_game(game),
                "players": players_data,
                "requests": [_format_request(r, u) for r, u in requests],
            })

        return {"success": True, "games": result}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def get_game_history_service(group_id: int):
    db = SessionLocal()
    try:
        games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "finished",
        ).order_by(PokerGame.started_at.desc()).all()

        result = []
        for game in games:
            players = db.query(PokerGamePlayer, User).join(
                User, PokerGamePlayer.user_id == User.id
            ).filter(PokerGamePlayer.game_id == game.id).all()

            players_data = []
            for p, u in players:
                pd = _format_player(p, u)
                if u.id == game.organizer_id:
                    breakdown = _get_buyin_breakdown(db, game.id, u.id)
                    pd["buy_in_normal"] = breakdown["normal"]
                    pd["buy_in_insurance"] = breakdown["insurance"]
                    pd["buy_in_anti"] = breakdown["anti"]
                players_data.append(pd)

            result.append({**_format_game(game), "players": players_data})

        return {"success": True, "games": result}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def get_group_members_for_game_service(group_id: int):
    db = SessionLocal()
    try:
        rows = db.query(UserGroupRole, User).join(
            User, UserGroupRole.user_id == User.id
        ).filter(UserGroupRole.group_id == group_id).all()

        members = [
            {
                "user_id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "role": ugr.role,
                "avatar_url": user.avatar_url,
            }
            for ugr, user in rows
        ]

        return {"success": True, "members": members}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def start_game_service(group_id: int, organizer_id: int, name: str, preselected_user_ids: list):
    db = SessionLocal()
    try:
        # 最多同时 3 个进行中的局
        ongoing_games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).all()

        if len(ongoing_games) >= 3:
            return {"success": False, "message": "tooManyOngoingGames"}

        if len(preselected_user_ids) > MAX_PLAYERS:
            return {"success": False, "message": "tooManyPlayers"}

        # 非局头用户不能同时在两个局里
        ongoing_game_ids = [g.id for g in ongoing_games]
        for uid in preselected_user_ids:
            if uid == organizer_id:
                continue
            already_in = db.query(PokerGamePlayer).filter(
                PokerGamePlayer.game_id.in_(ongoing_game_ids),
                PokerGamePlayer.user_id == uid,
                PokerGamePlayer.is_active == 1,
            ).first()
            if already_in:
                user = db.query(User).filter(User.id == uid).first()
                name_str = user.nickname or user.username if user else str(uid)
                return {"success": False, "message": f"playerAlreadyInGame:{name_str}"}

        game = PokerGame(
            group_id=group_id,
            organizer_id=organizer_id,
            name=name.strip() if name else None,
            status="ongoing",
            started_at=datetime.utcnow(),
        )
        db.add(game)
        db.flush()

        for uid in preselected_user_ids:
            user = db.query(User).filter(User.id == uid).first()
            if not user:
                continue
            member = db.query(UserGroupRole).filter(
                UserGroupRole.user_id == uid,
                UserGroupRole.group_id == group_id,
            ).first()
            if not member:
                continue
            player = PokerGamePlayer(
                game_id=game.id,
                user_id=uid,
                nickname=user.nickname or user.username,
                is_active=1,
                joined_at=datetime.utcnow(),
            )
            db.add(player)

        db.commit()
        return {"success": True, "game_id": game.id}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def add_player_to_game_service(game_id: int, group_id: int, user_id: int, organizer_id: int):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        member = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id,
            UserGroupRole.group_id == group_id,
        ).first()

        if not member:
            return {"success": False, "message": "userNotInGroup"}

        existing_player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
        ).first()

        if existing_player:
            if existing_player.is_active == 1:
                return {"success": False, "message": "playerAlreadyInGame"}
            # 加回本局不检查其他局
            existing_player.is_active = 1
            db.commit()
            return {"success": True, "rejoined": True}

        # 非局头用户不能同时在本组其他进行中牌局
        if user_id != organizer_id:
            other_game_ids = [
                g.id for g in db.query(PokerGame).filter(
                    PokerGame.group_id == group_id,
                    PokerGame.status == "ongoing",
                    PokerGame.id != game_id,
                ).all()
            ]
            if other_game_ids:
                already_in = db.query(PokerGamePlayer).filter(
                    PokerGamePlayer.game_id.in_(other_game_ids),
                    PokerGamePlayer.user_id == user_id,
                    PokerGamePlayer.is_active == 1,
                ).first()
                if already_in:
                    return {"success": False, "message": "playerAlreadyInAnotherGame"}

        active_count = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.is_active == 1,
        ).count()

        if active_count >= MAX_PLAYERS:
            return {"success": False, "message": "gameFull"}

        user = db.query(User).filter(User.id == user_id).first()
        player = PokerGamePlayer(
            game_id=game_id,
            user_id=user_id,
            nickname=user.nickname or user.username,
            is_active=1,
            joined_at=datetime.utcnow(),
        )
        db.add(player)
        db.commit()
        return {"success": True, "rejoined": False}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def remove_player_from_game_service(game_id: int, group_id: int, user_id: int):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        player.is_active = 0
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def approve_chip_request_service(request_id: int, game_id: int, group_id: int, resolver_id: int):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        req = db.query(ChipRequest).filter(
            ChipRequest.id == request_id,
            ChipRequest.game_id == game_id,
            ChipRequest.status == "pending",
        ).first()

        if not req:
            return {"success": False, "message": "requestNotFound"}

        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == req.user_id,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        req.status = "approved"
        req.resolved_at = datetime.utcnow()
        req.resolved_by = resolver_id
        player.total_buy_in += req.amount

        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def reject_chip_request_service(request_id: int, game_id: int, group_id: int, resolver_id: int):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        req = db.query(ChipRequest).filter(
            ChipRequest.id == request_id,
            ChipRequest.game_id == game_id,
            ChipRequest.status == "pending",
        ).first()

        if not req:
            return {"success": False, "message": "requestNotFound"}

        req.status = "rejected"
        req.resolved_at = datetime.utcnow()
        req.resolved_by = resolver_id

        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def organizer_buyin_service(game_id: int, group_id: int, user_id: int, amount: int, buy_type: str = "normal"):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        if amount <= 0:
            return {"success": False, "message": "invalidAmount"}

        if buy_type not in ("normal", "insurance", "anti"):
            return {"success": False, "message": "invalidBuyType"}

        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        user = db.query(User).filter(User.id == user_id).first()

        player.total_buy_in += amount

        req = ChipRequest(
            game_id=game_id,
            user_id=user_id,
            nickname=user.nickname or user.username if user else "",
            type=buy_type,
            amount=amount,
            status="approved",
            requested_at=datetime.utcnow(),
            resolved_at=datetime.utcnow(),
            resolved_by=user_id,
        )
        db.add(req)
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def finish_game_service(
    game_id: int,
    group_id: int,
    organizer_id: int,
    player_cash_outs: list,
    organizer_insurance_final: int = 0,
    organizer_anti_final: int = 0,
    force: bool = False,
):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        players = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
        ).all()

        # 写入所有人的 cash_out
        cash_out_map = {item["user_id"]: item["cash_out"] for item in player_cash_outs}

        for player in players:
            co = cash_out_map.get(player.user_id, 0)
            player.cash_out = co
            player.net = co - player.total_buy_in

        total_buy_in = sum(p.total_buy_in for p in players)
        total_cash_out = sum((p.cash_out or 0) for p in players)

        is_balanced = 1 if total_cash_out == total_buy_in else 0

        if not is_balanced and not force:
            db.rollback()
            return {
                "success": False,
                "message": "balanceCheckFailed",
                "total_buy_in": total_buy_in,
                "total_cash_out": total_cash_out,
                "diff": total_cash_out - total_buy_in,
            }

        game.status = "finished"
        game.ended_at = datetime.utcnow()
        game.total_buy_in = total_buy_in
        game.total_cash_out = total_cash_out
        game.is_balanced = is_balanced
        game.player_count = len([p for p in players if p.total_buy_in > 0 or (p.cash_out or 0) > 0])

        db.commit()

        players_refreshed = db.query(PokerGamePlayer, User).join(
            User, PokerGamePlayer.user_id == User.id
        ).filter(PokerGamePlayer.game_id == game_id).all()

        players_data = []
        for p, u in players_refreshed:
            pd = _format_player(p, u)
            if u.id == organizer_id:
                breakdown = _get_buyin_breakdown(db, game_id, u.id)
                pd["buy_in_normal"] = breakdown["normal"]
                pd["buy_in_insurance"] = breakdown["insurance"]
                pd["buy_in_anti"] = breakdown["anti"]
            players_data.append(pd)

        return {
            "success": True,
            "is_balanced": is_balanced,
            "game": _format_game(game),
            "players": players_data,
        }
    except Exception as e:
        db.rollback()
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


def _format_game(game):
    return {
        "id": game.id,
        "group_id": game.group_id,
        "organizer_id": game.organizer_id,
        "status": game.status,
        "name": game.name or "",
        "started_at": game.started_at.strftime("%Y-%m-%d %H:%M") if game.started_at else "",
        "ended_at": game.ended_at.strftime("%Y-%m-%d %H:%M") if game.ended_at else "",
        "total_buy_in": game.total_buy_in,
        "total_cash_out": game.total_cash_out,
        "is_balanced": game.is_balanced,
        "player_count": game.player_count,
        "note": game.note,
    }


def _format_player(player, user):
    return {
        "id": player.id,
        "game_id": player.game_id,
        "user_id": player.user_id,
        "username": user.username,
        "nickname": player.nickname,
        "avatar_url": user.avatar_url,
        "total_buy_in": player.total_buy_in,
        "cash_out": player.cash_out,
        "net": player.net,
        "is_active": player.is_active,
        "joined_at": player.joined_at.strftime("%Y-%m-%d %H:%M") if player.joined_at else "",
    }


def _format_request(req, user):
    return {
        "id": req.id,
        "game_id": req.game_id,
        "user_id": req.user_id,
        "username": user.username,
        "nickname": req.nickname,
        "type": req.type,
        "amount": req.amount,
        "status": req.status,
        "requested_at": req.requested_at.strftime("%Y-%m-%d %H:%M:%S") if req.requested_at else "",
    }


def update_cash_out_service(game_id: int, group_id: int, user_id: int, cash_out: int):
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
        ).first()

        if not game:
            return {"success": False, "message": "gameNotFound"}

        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        player.cash_out = cash_out
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()