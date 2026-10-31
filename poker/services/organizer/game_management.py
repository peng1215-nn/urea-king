from core.time import now_columbus_naive
from database import SessionLocal
from poker.models import ChipRequest
from poker.models import GameEvent
from poker.models import Group
from poker.models import GroupMemberAlias
from poker.models import PokerGame
from poker.models import PokerGamePlayer
from poker.models import User
from poker.models import UserGroupRole
from core.validators import check_name, check_text
from poker.core.validators import GAME_NAME_MAX, GAME_NOTE_MAX, check_amount
from core.errors import safe_error
from poker.services.common.game_events import record_game_event


MAX_PLAYERS = 10


# ───────────── 并发保护 ─────────────
# 所有修改牌局数据的操作都先锁住这一局（SELECT ... FOR UPDATE），
# 同一局的操作因此排队执行，不会互相覆盖。
# 需要跨局检查的操作（开局、加人）先锁组再锁局，加锁顺序固定，避免死锁。

def _lock_group(db, group_id):
    db.query(Group.id).filter(Group.id == group_id).with_for_update().first()


def _lock_ongoing_game(db, game_id, group_id):
    return db.query(PokerGame).filter(
        PokerGame.id == game_id,
        PokerGame.group_id == group_id,
        PokerGame.status == "ongoing",
    ).with_for_update().first()


def _reject_pending_requests(db, game_id, user_id=None):
    """
    把待审批的买入申请标记为已拒绝（玩家离开牌局、牌局结束时调用）。
    resolved_by 留空，表示由系统自动处理。
    """
    query = db.query(ChipRequest).filter(
        ChipRequest.game_id == game_id,
        ChipRequest.status == "pending",
    )
    if user_id is not None:
        query = query.filter(ChipRequest.user_id == user_id)
    for req in query.with_for_update().all():
        req.status = "rejected"
        req.resolved_at = now_columbus_naive()
        record_game_event(
            db, game_id, "buyin_auto_rejected",
            target_user_id=req.user_id, amount=req.amount, buy_type=req.type,
        )


def _get_aliases(db, group_id):
    """本组成员的备注名 {user_id: alias}（成员管理里设置）。"""
    rows = db.query(GroupMemberAlias).filter(GroupMemberAlias.group_id == group_id).all()
    return {r.user_id: r.alias for r in rows}


def _display_name(nickname, alias):
    """和牌局日志一致的显示名："昵称（备注）"。"""
    return f"{nickname}（{alias}）" if alias else nickname


def _last_leave_types(db, game_id):
    """
    每个玩家最近一次离开是"暂离"还是"结算离场"：{user_id: "away" | "exit"}。
    以操作记录为准（同一玩家可能结算离场、回来、再暂离）。
    """
    events = db.query(GameEvent.target_user_id, GameEvent.event_type).filter(
        GameEvent.game_id == game_id,
        GameEvent.event_type.in_(("player_removed", "player_exited")),
    ).order_by(GameEvent.id.asc()).all()
    result = {}
    for user_id, event_type in events:
        result[user_id] = "exit" if event_type == "player_exited" else "away"
    return result


def _add_to_buy_in(db, player_id, amount):
    """在数据库里直接累加，不经过“读出来、加好、写回去”。"""
    db.query(PokerGamePlayer).filter(PokerGamePlayer.id == player_id).update(
        {PokerGamePlayer.total_buy_in: PokerGamePlayer.total_buy_in + amount},
        synchronize_session=False,
    )


def get_ongoing_games_service(group_id: int):
    db = SessionLocal()
    try:
        games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).order_by(PokerGame.started_at.asc()).all()

        if not games:
            return {"success": True, "games": []}

        aliases = _get_aliases(db, group_id)

        result = []
        for game in games:
            leave_types = _last_leave_types(db, game.id)
            players = db.query(PokerGamePlayer, User).join(
                User, PokerGamePlayer.user_id == User.id
            ).filter(PokerGamePlayer.game_id == game.id).all()

            requests = db.query(ChipRequest, User).join(
                User, ChipRequest.user_id == User.id
            ).filter(
                ChipRequest.game_id == game.id,
                ChipRequest.status == "pending",
            ).order_by(ChipRequest.requested_at.desc()).all()

            # 查询本组有哪些用户授权了局头代买
            auth_records = db.query(UserGroupRole).filter(
                UserGroupRole.group_id == game.group_id,
                UserGroupRole.role == "user",
            ).all()
            auth_map = {r.user_id: r.allow_organizer_chip_op for r in auth_records}

            # 组里的局头（最多两个）：都可以给自己买入保险 / Anti，都显示买入明细
            group_organizer_ids = {
                r.user_id for r in db.query(UserGroupRole.user_id).filter(
                    UserGroupRole.group_id == game.group_id,
                    UserGroupRole.role == "organizer",
                ).all()
            }

            players_data = []
            for p, u in players:
                pd = _format_player(p, u)
                pd["is_group_organizer"] = u.id in group_organizer_ids or u.id == game.organizer_id
                if pd["is_group_organizer"]:
                    breakdown = _get_buyin_breakdown(db, game.id, u.id)
                    pd["buy_in_normal"] = breakdown["normal"]
                    pd["buy_in_insurance"] = breakdown["insurance"]
                    pd["buy_in_anti"] = breakdown["anti"]
                pd["allow_organizer_chip_op"] = auth_map.get(u.id, 0)
                pd["alias"] = aliases.get(u.id, "")
                # 不在桌上的玩家：区分"暂离"（筹码还在手上）、"已结算离场"和"只管理"（局头没上桌）
                if p.is_active != 1 and p.manager_only:
                    pd["leave_type"] = "manager"
                elif p.is_active != 1:
                    pd["leave_type"] = leave_types.get(
                        u.id, "exit" if (p.left_cash_out or 0) > 0 else "away"
                    )
                else:
                    pd["leave_type"] = None
                players_data.append(pd)

            requests_data = []
            for r, u in requests:
                rd = _format_request(r, u)
                rd["alias"] = aliases.get(r.user_id, "")
                requests_data.append(rd)

            result.append({
                **_format_game(game),
                "players": players_data,
                "requests": requests_data,
            })

        return {"success": True, "games": result}
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def get_group_members_for_game_service(group_id: int):
    db = SessionLocal()
    try:
        rows = db.query(UserGroupRole, User).join(
            User, UserGroupRole.user_id == User.id
        ).filter(UserGroupRole.group_id == group_id).all()

        aliases = _get_aliases(db, group_id)

        # 每个成员当前在本组哪些进行中的牌局里（仍在桌上），前端据此把
        # "在其他牌局中"的成员置灰，不用等提交后才报错
        active_rows = db.query(PokerGamePlayer.user_id, PokerGamePlayer.game_id).join(
            PokerGame, PokerGamePlayer.game_id == PokerGame.id
        ).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
            PokerGamePlayer.is_active == 1,
        ).all()
        ongoing_by_user = {}
        for uid, gid in active_rows:
            ongoing_by_user.setdefault(uid, []).append(gid)

        members = [
            {
                "user_id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "alias": aliases.get(user.id, ""),
                "role": ugr.role,
                "avatar_url": user.avatar_url,
                "ongoing_game_ids": ongoing_by_user.get(user.id, []),
            }
            for ugr, user in rows
        ]

        return {"success": True, "members": members}
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def start_game_service(group_id: int, organizer_id: int, name: str, preselected_user_ids: list):
    name, name_error = check_name(name, GAME_NAME_MAX)
    if name_error:
        return {
            "success": False,
            "message": "textTooLong" if name_error == "too_long" else "textInvalidChars",
        }

    db = SessionLocal()
    try:
        # 同一组同时只能有一个开局操作，避免同时开局绕过下面的检查
        _lock_group(db, group_id)

        # 最多同时 3 个进行中的局
        ongoing_games = db.query(PokerGame).filter(
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).all()

        if len(ongoing_games) >= 3:
            return {"success": False, "message": "tooManyOngoingGames"}

        if len(preselected_user_ids) > MAX_PLAYERS:
            return {"success": False, "message": "tooManyPlayers"}

        # 非局头用户不能同时在两个局里；把冲突的人一次全列出来
        ongoing_game_ids = [g.id for g in ongoing_games]
        conflict_ids = []
        for uid in preselected_user_ids:
            if uid == organizer_id or uid in conflict_ids:
                continue
            already_in = db.query(PokerGamePlayer).filter(
                PokerGamePlayer.game_id.in_(ongoing_game_ids),
                PokerGamePlayer.user_id == uid,
                PokerGamePlayer.is_active == 1,
            ).first()
            if already_in:
                conflict_ids.append(uid)
        if conflict_ids:
            aliases = _get_aliases(db, group_id)
            names = []
            for uid in conflict_ids:
                user = db.query(User).filter(User.id == uid).first()
                nickname = (user.nickname or user.username) if user else str(uid)
                names.append(_display_name(nickname, aliases.get(uid, "")))
            return {
                "success": False,
                "message": "playerAlreadyInAnotherGame",
                "player_ids": conflict_ids,
                "player_names": names,
            }

        game = PokerGame(
            group_id=group_id,
            organizer_id=organizer_id,
            name=name or None,
            status="ongoing",
            started_at=now_columbus_naive(),
        )
        db.add(game)
        db.flush()

        started_players = []
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
                joined_at=now_columbus_naive(),
            )
            db.add(player)
            started_players.append(player.nickname)

        record_game_event(
            db, game.id, "game_started",
            actor_user_id=organizer_id,
            details={"name": game.name or "", "players": started_players},
        )
        db.commit()
        return {"success": True, "game_id": game.id}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def add_player_to_game_service(game_id: int, group_id: int, user_id: int, organizer_id: int):
    db = SessionLocal()
    try:
        # 要检查“不能同时在本组两个局里”，所以先锁组再锁局
        _lock_group(db, group_id)
        game = _lock_ongoing_game(db, game_id, group_id)

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

        if existing_player and existing_player.is_active == 1:
            return {"success": False, "message": "playerAlreadyInGame"}

        # 新加入和加回（之前被移出或中途退出）都要检查下面两条

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
                    user = db.query(User).filter(User.id == user_id).first()
                    nickname = (user.nickname or user.username) if user else str(user_id)
                    alias = _get_aliases(db, group_id).get(user_id, "")
                    return {
                        "success": False,
                        "message": "playerAlreadyInAnotherGame",
                        "player_ids": [user_id],
                        "player_names": [_display_name(nickname, alias)],
                    }

        active_count = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.is_active == 1,
        ).count()

        if active_count >= MAX_PLAYERS:
            return {"success": False, "message": "gameFull"}

        if existing_player and existing_player.manager_only:
            # 只管理的局头上桌：之前只记过保险 / Anti，这是第一次坐下
            existing_player.is_active = 1
            existing_player.manager_only = 0
            record_game_event(db, game_id, "player_added", actor_user_id=organizer_id, target_user_id=user_id)
            db.commit()
            return {"success": True, "rejoined": False}

        if existing_player:
            existing_player.is_active = 1
            # 记下他这次回来之前是"暂离"还是"结算离场"，报告里区分显示
            last_leave = db.query(GameEvent).filter(
                GameEvent.game_id == game_id,
                GameEvent.target_user_id == user_id,
                GameEvent.event_type.in_(("player_removed", "player_exited")),
            ).order_by(GameEvent.id.desc()).first()
            if last_leave is not None and last_leave.event_type == "player_exited":
                rejoin_details = {"after": "exit", "cash_out": last_leave.amount}
            else:
                rejoin_details = {"after": "away"}
            record_game_event(
                db, game_id, "player_rejoined",
                actor_user_id=organizer_id, target_user_id=user_id, details=rejoin_details,
            )
            db.commit()
            return {"success": True, "rejoined": True}

        user = db.query(User).filter(User.id == user_id).first()
        player = PokerGamePlayer(
            game_id=game_id,
            user_id=user_id,
            nickname=user.nickname or user.username,
            is_active=1,
            joined_at=now_columbus_naive(),
        )
        db.add(player)
        record_game_event(db, game_id, "player_added", actor_user_id=organizer_id, target_user_id=user_id)
        db.commit()
        return {"success": True, "rejoined": False}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def remove_player_from_game_service(game_id: int, group_id: int, user_id: int, actor_id: int = None):
    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)

        if not game:
            return {"success": False, "message": "gameNotFound"}

        # 只能对仍在桌上的玩家执行；已经暂离或离场的再点一次（如重复提交）直接拒绝
        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
            PokerGamePlayer.is_active == 1,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        player.is_active = 0
        record_game_event(db, game_id, "player_removed", actor_user_id=actor_id, target_user_id=user_id)
        # 被移出后，他还没审批的买入申请一并拒绝
        _reject_pending_requests(db, game_id, user_id)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def exit_player_from_game_service(game_id: int, group_id: int, user_id: int, cash_out: int, actor_id: int = None):
    """玩家退出：记录 cash_out 并移出"""
    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)

        if not game:
            return {"success": False, "message": "gameNotFound"}

        # 只能对仍在桌上的玩家执行；已经暂离或离场的再点一次（如重复提交）直接拒绝
        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
            PokerGamePlayer.is_active == 1,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        amount_error = check_amount(cash_out, allow_zero=True)
        if amount_error:
            return {"success": False, "message": amount_error}

        # 离场拿走的筹码累计起来（可能结算离场、回来、再离场），结束牌局时自动计入总卖出
        player.left_cash_out = (player.left_cash_out or 0) + cash_out
        player.cash_out = player.left_cash_out
        player.net = player.cash_out - (player.total_buy_in or 0)
        player.is_active = 0
        record_game_event(
            db, game_id, "player_exited",
            actor_user_id=actor_id, target_user_id=user_id, amount=cash_out,
            details={
                "buy_in": player.total_buy_in or 0,
                "left_total": player.left_cash_out,
                "net": player.net,
            },
        )
        # 已经结算离场，还没审批的买入申请一并拒绝
        _reject_pending_requests(db, game_id, user_id)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def approve_chip_request_service(request_id: int, game_id: int, group_id: int, resolver_id: int):
    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)

        if not game:
            return {"success": False, "message": "gameNotFound"}

        req = db.query(ChipRequest).filter(
            ChipRequest.id == request_id,
            ChipRequest.game_id == game_id,
            ChipRequest.status == "pending",
        ).with_for_update().first()

        if not req:
            return {"success": False, "message": "requestNotFound"}

        # 只能批准仍在牌局中的玩家的申请
        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == req.user_id,
            PokerGamePlayer.is_active == 1,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        req.status = "approved"
        req.resolved_at = now_columbus_naive()
        req.resolved_by = resolver_id
        _add_to_buy_in(db, player.id, req.amount)
        record_game_event(
            db, game_id, "buyin_approved",
            actor_user_id=resolver_id, target_user_id=req.user_id, amount=req.amount, buy_type=req.type,
        )

        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def reject_chip_request_service(request_id: int, game_id: int, group_id: int, resolver_id: int):
    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)

        if not game:
            return {"success": False, "message": "gameNotFound"}

        req = db.query(ChipRequest).filter(
            ChipRequest.id == request_id,
            ChipRequest.game_id == game_id,
            ChipRequest.status == "pending",
        ).with_for_update().first()

        if not req:
            return {"success": False, "message": "requestNotFound"}

        req.status = "rejected"
        req.resolved_at = now_columbus_naive()
        req.resolved_by = resolver_id
        record_game_event(
            db, game_id, "buyin_rejected",
            actor_user_id=resolver_id, target_user_id=req.user_id, amount=req.amount, buy_type=req.type,
        )

        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def organizer_buyin_service(game_id: int, group_id: int, user_id: int, amount: int, buy_type: str = "normal"):
    """局头给自己买入，直接记为已批准。user_id 必须是局头本人（由路由从会话取得）。"""
    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)

        if not game:
            return {"success": False, "message": "gameNotFound"}

        amount_error = check_amount(amount)
        if amount_error:
            return {"success": False, "message": amount_error}

        if buy_type not in ("normal", "insurance", "anti"):
            return {"success": False, "message": "invalidBuyType"}

        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == user_id,
        ).with_for_update().first()

        user = db.query(User).filter(User.id == user_id).first()

        # 局头不上桌（只管理）时只能买保险 / Anti，普通买入要先上桌
        seated = player is not None and player.is_active == 1
        if not seated and buy_type == "normal":
            return {"success": False, "message": "organizerNotSeatedNormalBuyin"}

        if player is None:
            # 只管理的局头第一次买保险 / Anti：建一条不占桌上名额的记录，结束时一起结算
            player = PokerGamePlayer(
                game_id=game_id,
                user_id=user_id,
                nickname=(user.nickname or user.username) if user else "",
                is_active=0,
                manager_only=1,
                joined_at=now_columbus_naive(),
            )
            db.add(player)
            db.flush()

        _add_to_buy_in(db, player.id, amount)

        req = ChipRequest(
            game_id=game_id,
            user_id=user_id,
            nickname=user.nickname or user.username if user else "",
            type=buy_type,
            amount=amount,
            status="approved",
            requested_at=now_columbus_naive(),
            resolved_at=now_columbus_naive(),
            resolved_by=user_id,
        )
        db.add(req)
        record_game_event(
            db, game_id, "organizer_buyin",
            actor_user_id=user_id, target_user_id=user_id, amount=amount, buy_type=buy_type,
        )
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def organizer_proxy_buyin_service(game_id: int, group_id: int, organizer_id: int, target_user_id: int, amount: int):
    """局头代替玩家买入（需要玩家已授权 allow_organizer_chip_op）"""
    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)

        if not game:
            return {"success": False, "message": "gameNotFound"}

        amount_error = check_amount(amount)
        if amount_error:
            return {"success": False, "message": amount_error}

        # 检查目标玩家是否授权了局头代买
        auth = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == target_user_id,
            UserGroupRole.group_id == group_id,
            UserGroupRole.role == "user",
        ).first()

        if not auth or not auth.allow_organizer_chip_op:
            return {"success": False, "message": "proxyBuyinNotAuthorized"}

        # 确认玩家在局中
        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == target_user_id,
            PokerGamePlayer.is_active == 1,
        ).first()

        if not player:
            return {"success": False, "message": "playerNotInGame"}

        target_user = db.query(User).filter(User.id == target_user_id).first()

        _add_to_buy_in(db, player.id, amount)

        req = ChipRequest(
            game_id=game_id,
            user_id=target_user_id,
            nickname=target_user.nickname or target_user.username if target_user else "",
            type="normal",
            amount=amount,
            status="approved",
            requested_at=now_columbus_naive(),
            resolved_at=now_columbus_naive(),
            resolved_by=organizer_id,
        )
        db.add(req)
        record_game_event(
            db, game_id, "proxy_buyin",
            actor_user_id=organizer_id, target_user_id=target_user_id, amount=amount, buy_type="normal",
        )
        db.commit()

        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def list_player_buyins_service(game_id: int, group_id: int, user_id: int):
    """进行中牌局里某位玩家的每一笔买入（已批准的和已撤销的），给局头核对、撤销用。"""
    db = SessionLocal()
    try:
        game = db.query(PokerGame).filter(
            PokerGame.id == game_id,
            PokerGame.group_id == group_id,
            PokerGame.status == "ongoing",
        ).first()
        if not game:
            return {"success": False, "message": "gameNotFound"}

        rows = db.query(ChipRequest).filter(
            ChipRequest.game_id == game_id,
            ChipRequest.user_id == user_id,
            ChipRequest.status.in_(("approved", "reversed")),
        ).order_by(ChipRequest.resolved_at.asc(), ChipRequest.id.asc()).all()

        return {
            "success": True,
            "buyins": [
                {
                    "id": r.id,
                    "amount": r.amount,
                    "type": r.type or "normal",
                    "status": r.status,
                    "time": r.resolved_at.strftime("%H:%M:%S") if r.resolved_at else "",
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()


def reverse_buyin_service(request_id: int, game_id: int, group_id: int, organizer_id: int):
    """
    局头撤销一笔已记入的买入（批准的申请、局头买入、代买都可以）：
    从玩家总买入里减掉，原记录标为 reversed（不删除），并记一条 buyin_reversed 审计事件。
    只能在牌局进行中撤销；撤销不能再恢复，撤错了重新买入即可。
    """
    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)
        if not game:
            return {"success": False, "message": "gameNotFound"}

        req = db.query(ChipRequest).filter(
            ChipRequest.id == request_id,
            ChipRequest.game_id == game_id,
            ChipRequest.status == "approved",
        ).with_for_update().first()
        if not req:
            return {"success": False, "message": "buyinNotFound"}

        player = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
            PokerGamePlayer.user_id == req.user_id,
        ).with_for_update().first()
        if not player or (player.total_buy_in or 0) < req.amount:
            # 正常情况下不会发生：总买入就是这些买入加起来的
            return {"success": False, "message": "buyinNotFound"}

        req.status = "reversed"
        _add_to_buy_in(db, player.id, -req.amount)
        record_game_event(
            db, game_id, "buyin_reversed",
            actor_user_id=organizer_id, target_user_id=req.user_id, amount=req.amount, buy_type=req.type,
            details={"request_id": req.id},
        )
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
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
    note: str = "",
):
    note, note_error = check_text(note, GAME_NOTE_MAX)
    if note_error:
        return {
            "success": False,
            "message": "textTooLong" if note_error == "too_long" else "textInvalidChars",
        }

    db = SessionLocal()
    try:
        game = _lock_ongoing_game(db, game_id, group_id)

        if not game:
            return {"success": False, "message": "gameNotFound"}

        players = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id == game_id,
        ).all()

        # 服务器自己核对：名单必须与本局玩家完全一致，每个金额都合法，
        # 不信任前端传来的数据
        cash_out_map = {}
        for item in player_cash_outs or []:
            if not isinstance(item, dict):
                return {"success": False, "message": "settlementPlayersMismatch"}
            uid = item.get("user_id")
            co = item.get("cash_out")
            if isinstance(uid, bool) or not isinstance(uid, int) or uid in cash_out_map:
                return {"success": False, "message": "settlementPlayersMismatch"}
            amount_error = check_amount(co, allow_zero=True)
            if amount_error:
                return {"success": False, "message": amount_error}
            cash_out_map[uid] = co

        if set(cash_out_map) != {p.user_id for p in players}:
            return {"success": False, "message": "settlementPlayersMismatch"}

        # 局头填的是每人结束时剩余的筹码；中途结算离场拿走的部分由系统加上
        final_chips = dict(cash_out_map)
        for player in players:
            player.cash_out = (player.left_cash_out or 0) + final_chips[player.user_id]
            player.net = player.cash_out - player.total_buy_in

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

        # 牌局结束时，还没审批的买入申请全部拒绝，不再挂着"待审批"
        _reject_pending_requests(db, game_id)

        game.status = "finished"
        game.ended_at = now_columbus_naive()
        game.total_buy_in = total_buy_in
        game.total_cash_out = total_cash_out
        game.is_balanced = is_balanced
        game.player_count = len([p for p in players if p.total_buy_in > 0 or (p.cash_out or 0) > 0])
        if note:
            game.note = note

        record_game_event(
            db, game_id, "game_finished",
            actor_user_id=organizer_id,
            details={
                "total_buy_in": total_buy_in,
                "total_cash_out": total_cash_out,
                "balanced": bool(is_balanced),
                "forced": bool(force and not is_balanced),
                "players": [
                    {
                        "user_id": p.user_id,
                        "name": p.nickname,
                        "buy_in": p.total_buy_in,
                        "left_cash_out": p.left_cash_out or 0,
                        "final_chips": final_chips[p.user_id],
                        "cash_out": p.cash_out,
                        "net": p.net,
                    }
                    for p in players
                ],
            },
        )
        db.commit()

        players_refreshed = db.query(PokerGamePlayer, User).join(
            User, PokerGamePlayer.user_id == User.id
        ).filter(PokerGamePlayer.game_id == game_id).all()

        aliases = _get_aliases(db, group_id)
        players_data = []
        for p, u in players_refreshed:
            pd = _format_player(p, u)
            pd["alias"] = aliases.get(u.id, "")
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
        return {"success": False, "message": safe_error(e)}
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
        "left_cash_out": player.left_cash_out or 0,
        "net": player.net,
        "is_active": player.is_active,
        "manager_only": player.manager_only or 0,
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
