from datetime import datetime
from database import SessionLocal
from models import ChipRequest
from models import PokerGame
from models import PokerGamePlayer
from models import User
from models import UserGroupRole


def get_user_ongoing_games_service(group_id: int, user_id: int):
    db = SessionLocal()
    try:
        player_records = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.user_id == user_id,
            PokerGamePlayer.is_active == 1,
        ).all()

        game_ids = [p.game_id for p in player_records]

        games = db.query(PokerGame).filter(
            PokerGame.id.in_(game_ids),
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).order_by(PokerGame.started_at.asc()).all()

        result = []
        for game in games:
            # 当前用户的记录
            my_player = db.query(PokerGamePlayer).filter(
                PokerGamePlayer.game_id == game.id,
                PokerGamePlayer.user_id == user_id,
            ).first()

            # 所有玩家
            all_players_q = db.query(PokerGamePlayer, User).join(
                User, PokerGamePlayer.user_id == User.id
            ).filter(
                PokerGamePlayer.game_id == game.id,
                PokerGamePlayer.is_active == 1,
            ).all()

            # 局头角色
            organizer_roles = db.query(UserGroupRole).filter(
                UserGroupRole.group_id == group_id,
                UserGroupRole.role == "organizer",
            ).all()
            organizer_ids = {r.user_id for r in organizer_roles}

            players_data = []
            for p, u in all_players_q:
                is_organizer = p.user_id in organizer_ids
                is_me = p.user_id == user_id

                # 只有自己才能看到申请记录
                my_requests = []
                if is_me:
                    reqs = db.query(ChipRequest).filter(
                        ChipRequest.game_id == game.id,
                        ChipRequest.user_id == user_id,
                    ).order_by(ChipRequest.requested_at.desc()).all()
                    my_requests = [
                        {
                            "id": r.id,
                            "amount": r.amount,
                            "status": r.status,
                            "requested_at": r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "",
                        }
                        for r in reqs
                    ]

                players_data.append({
                    "user_id": p.user_id,
                    "nickname": p.nickname or u.username,
                    "avatar_url": u.avatar_url or "",
                    "is_organizer": is_organizer,
                    "is_me": is_me,
                    "total_buy_in": p.total_buy_in or 0,
                    "requests": my_requests,
                })

            # 局头排前面
            players_data.sort(key=lambda x: (not x["is_organizer"], not x["is_me"]))

            result.append({
                "id": game.id,
                "name": game.name or "",
                "started_at": game.started_at.strftime("%Y-%m-%d %H:%M") if game.started_at else "",
                "my_buy_in": my_player.total_buy_in if my_player else 0,
                "players": players_data,
            })

        return {"success": True, "games": result}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


def submit_buyin_request_service(game_id: int, group_id: int, user_id: int, amount: int):
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
            PokerGamePlayer.is_active == 1,
        ).first()

        if not player:
            return {"success": False, "message": "notInGame"}

        if amount <= 0:
            return {"success": False, "message": "invalidAmount"}

        user = db.query(User).filter(User.id == user_id).first()

        req = ChipRequest(
            game_id=game_id,
            user_id=user_id,
            nickname=user.nickname or user.username if user else "",
            type="normal",
            amount=amount,
            status="pending",
            requested_at=datetime.utcnow(),
        )
        db.add(req)
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()