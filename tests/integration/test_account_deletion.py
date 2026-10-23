"""用户自助注销：只删除仅属于本人的信息，与其他人有关的牌局记录全部保留。"""

DEFAULT_PASSWORD = "Passw0rd123"


def _delete(client, password=DEFAULT_PASSWORD, confirm_text="注销"):
    return client.post("/account/delete", data={"password": password, "confirm_text": confirm_text})


def _add_player(game_id, user_id, nickname, net):
    from database import SessionLocal
    from poker.models import PokerGamePlayer

    db = SessionLocal()
    try:
        db.add(PokerGamePlayer(
            game_id=game_id,
            user_id=user_id,
            nickname=nickname,
            total_buy_in=100,
            cash_out=100 + net,
            net=net,
            is_active=0,
        ))
        db.commit()
    finally:
        db.close()


def _start_ongoing_game(group_id, organizer_id, player_id=None):
    from datetime import datetime

    from database import SessionLocal
    from poker.models import PokerGame, PokerGamePlayer

    db = SessionLocal()
    try:
        game = PokerGame(group_id=group_id, organizer_id=organizer_id, status="ongoing", started_at=datetime(2026, 1, 1))
        db.add(game)
        db.flush()
        if player_id:
            db.add(PokerGamePlayer(game_id=game.id, user_id=player_id, nickname="p", total_buy_in=0, is_active=1))
        db.commit()
        return game.id
    finally:
        db.close()


def _user_row(user_id):
    from database import SessionLocal
    from poker.models import User

    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def test_user_can_delete_account_and_history_is_kept(client, factory, login_as):
    group_id = factory.group("G1")
    org_id = factory.user("orgaaaa1")
    factory.role(org_id, group_id, "organizer")
    user_id = factory.user("alice001", nickname="爱丽丝")
    factory.role(user_id, group_id, "user")

    game_id = factory.finished_game(group_id, org_id, "周五局")
    _add_player(game_id, user_id, "爱丽丝", 30)
    _add_player(game_id, org_id, "局头", -30)

    login_as("alice001", group_id)
    response = _delete(client)
    assert response.json() == {"success": True}

    # 会话已清除，不能再访问
    assert client.get("/current-user").json()["success"] is False

    # 账号被匿名化，不能登录
    row = _user_row(user_id)
    assert row.username == f"deleted#{user_id}"
    assert row.nickname == "已注销用户"
    assert row.is_active == 0
    assert client.post("/login", data={"username": "alice001", "password": DEFAULT_PASSWORD}).json()["success"] is False

    # 局头那边的牌局记录完整保留，仍显示当时的昵称，账目仍然平衡
    login_as("orgaaaa1", group_id)
    games = client.get("/organizer/game-log/list").json()["games"]
    assert len(games) == 1
    players = {p["nickname"]: p["net"] for p in games[0]["players"]}
    assert players["爱丽丝"] == 30
    assert sum(players.values()) == 0


def test_username_can_be_registered_again_after_deletion(client, factory, login_as):
    group_id = factory.group("G1")
    user_id = factory.user("bobbbb01")
    factory.role(user_id, group_id, "user")
    factory.invite("NEWCODE1", "G1")

    login_as("bobbbb01", group_id)
    assert _delete(client).json()["success"] is True

    response = client.post("/register", data={
        "username": "bobbbb01",
        "nickname": "新的 Bob",
        "password": "AnotherPass1",
        "confirm_password": "AnotherPass1",
        "invite_code": "NEWCODE1",
    })
    assert response.json()["success"] is True, response.json()


def test_wrong_password_or_confirm_text_is_rejected(client, factory, login_as):
    group_id = factory.group("G1")
    user_id = factory.user("carl0001")
    factory.role(user_id, group_id, "user")
    login_as("carl0001", group_id)

    assert _delete(client, password="wrong-password").json()["message"] == "currentPasswordIncorrect"
    assert _delete(client, confirm_text="确定").json()["message"] == "accountDeleteConfirmMismatch"
    assert _delete(client, confirm_text="delete").json()["success"] is True  # 英文界面输入 DELETE，不区分大小写


def test_cannot_delete_while_in_ongoing_game(client, factory, login_as):
    group_id = factory.group("G1")
    org_id = factory.user("orgbbbb1")
    factory.role(org_id, group_id, "organizer")
    user_id = factory.user("dana0001")
    factory.role(user_id, group_id, "user")
    _start_ongoing_game(group_id, org_id, player_id=user_id)

    login_as("dana0001", group_id)
    assert _delete(client).json()["message"] == "accountDeleteOngoingGame"
    assert _user_row(user_id).is_active == 1


def test_organizer_with_members_cannot_delete(client, factory, login_as):
    group_id = factory.group("G1", name="周五牌友")
    org_id = factory.user("orgcccc1")
    factory.role(org_id, group_id, "organizer")
    member_id = factory.user("eve00001")
    factory.role(member_id, group_id, "user")

    login_as("orgcccc1", group_id)
    result = _delete(client).json()
    assert result["message"] == "accountDeleteGroupHasMembers"
    assert result["group_name"] == "周五牌友"


def test_organizer_with_ongoing_game_cannot_delete(client, factory, login_as):
    group_id = factory.group("G1")
    org_id = factory.user("orgdddd1")
    factory.role(org_id, group_id, "organizer")
    _start_ongoing_game(group_id, org_id)

    login_as("orgdddd1", group_id)
    assert _delete(client).json()["message"] == "accountDeleteOngoingGame"


def test_organizer_alone_in_group_can_delete_and_games_are_kept(client, factory, login_as):
    group_id = factory.group("G1")
    org_id = factory.user("orgeeee1")
    factory.role(org_id, group_id, "organizer")
    factory.finished_game(group_id, org_id, "以前的局")

    login_as("orgeeee1", group_id)
    assert _delete(client).json()["success"] is True

    from database import SessionLocal
    from poker.models import PokerGame

    db = SessionLocal()
    try:
        assert db.query(PokerGame).filter(PokerGame.organizer_id == org_id).count() == 1
    finally:
        db.close()


def test_admin_cannot_delete_account(client, factory, login_as):
    group_id = factory.group("ADMIN")
    admin_id = factory.user("admin003")
    factory.role(admin_id, group_id, "admin")

    login_as("admin003", group_id)
    assert _delete(client).json()["message"] == "permissionDenied"


def test_deletion_is_recorded_in_audit_log(client, factory, login_as):
    from database import SessionLocal
    from poker.models import AuditLog

    group_id = factory.group("G1")
    user_id = factory.user("fred0001")
    factory.role(user_id, group_id, "user")
    login_as("fred0001", group_id)
    assert _delete(client).json()["success"] is True

    db = SessionLocal()
    try:
        log = db.query(AuditLog).filter(AuditLog.action == "DELETE_ACCOUNT").one()
        assert log.target_id == user_id
        assert log.old_value == "fred0001"
    finally:
        db.close()
