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
        # 找本组所有进行中的局，且该用户在其中
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
            player = db.query(PokerGamePlayer).filter(
                PokerGamePlayer.game_id == game.id,
                PokerGamePlayer.user_id == user_id,
            ).first()

            # 我的买入申请记录
            my_requests = db.query(ChipRequest).filter(
                ChipRequest.game_id == game.id,
                ChipRequest.user_id == user_id,
            ).order_by(ChipRequest.requested_at.desc()).all()

            result.append({
                "id": game.id,
                "name": game.name or "",
                "started_at": game.started_at.strftime("%Y-%m-%d %H:%M") if game.started_at else "",
                "my_buy_in": player.total_buy_in if player else 0,
                "is_active": player.is_active if player else 0,
                "requests": [
                    {
                        "id": r.id,
                        "amount": r.amount,
                        "status": r.status,
                        "requested_at": r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "",
                    }
                    for r in my_requests
                ],
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