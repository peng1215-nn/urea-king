"""
普通用户退出组、登录页注销账号、管理员强制解散组。

原则：只删除仅属于本人的信息；与其他用户有关的牌局记录保留。
局头注销时，他的组（已经没有其他成员）连同组内全部记录一起删除。系统日志保留。
"""

from datetime import datetime

DEFAULT_PASSWORD = "Passw0rd123"


# ───────────────────────── 辅助 ─────────────────────────

def _db():
    from database import SessionLocal

    return SessionLocal()


def _add_player(game_id, user_id, nickname, net=0, is_active=0):
    from poker.models import PokerGamePlayer

    db = _db()
    try:
        db.add(PokerGamePlayer(
            game_id=game_id,
            user_id=user_id,
            nickname=nickname,
            total_buy_in=100,
            cash_out=100 + net,
            net=net,
            is_active=is_active,
        ))
        db.commit()
    finally:
        db.close()


def _ongoing_game(group_id, organizer_id, player_id=None):
    from poker.models import PokerGame

    db = _db()
    try:
        game = PokerGame(
            group_id=group_id,
            organizer_id=organizer_id,
            status="ongoing",
            name="进行中",
            started_at=datetime(2026, 1, 1, 20, 0, 0),
        )
        db.add(game)
        db.commit()
        game_id = game.id
    finally:
        db.close()

    if player_id:
        _add_player(game_id, player_id, "p", is_active=1)
    return game_id


def _alias(group_id, user_id, alias):
    from poker.models import GroupMemberAlias

    db = _db()
    try:
        db.add(GroupMemberAlias(group_id=group_id, user_id=user_id, alias=alias))
        db.commit()
    finally:
        db.close()


def _used_invite(code, group_code, username):
    from poker.models import InvitationCode

    db = _db()
    try:
        db.add(InvitationCode(code=code, group_code=group_code, role="user", is_used=1, used_by_username=username))
        db.commit()
    finally:
        db.close()


def _count(model, **filters):
    db = _db()
    try:
        query = db.query(model)
        for name, value in filters.items():
            query = query.filter(getattr(model, name) == value)
        return query.count()
    finally:
        db.close()


def _user(user_id):
    from poker.models import User

    db = _db()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def _audit_actions():
    from poker.models import AuditLog

    db = _db()
    try:
        return [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]
    finally:
        db.close()


def _delete(client, username, password=DEFAULT_PASSWORD, confirm_text="注销"):
    return client.post(
        "/account/delete",
        data={"username": username, "password": password, "confirm_text": confirm_text},
    )


def _group_with_organizer(factory, code="G1", organizer="orgaaaa1"):
    group_id = factory.group(code, name=f"{code}组")
    org_id = factory.user(organizer)
    factory.role(org_id, group_id, "organizer")
    return group_id, org_id


# ───────────────────────── 退出组 ─────────────────────────

def test_user_can_leave_group_and_history_is_kept(client, factory, login_as):
    from poker.models import GroupMemberAlias, InvitationCode, PokerGamePlayer, UserGroupRole

    group_id, org_id = _group_with_organizer(factory)
    user_id = factory.user("alice001")
    factory.role(user_id, group_id, "user")
    _alias(group_id, user_id, "小A")
    _used_invite("INV-ALICE", "G1", "alice001")
    game_id = factory.finished_game(group_id, org_id, "周五局")
    _add_player(game_id, user_id, "alice001", 30)

    login_as("alice001", group_id)
    response = client.post("/user/leave-group")
    assert response.json()["success"] is True
    assert response.json()["message"] == "leaveGroupSuccess"
    assert response.json()["remaining_groups"] == 0

    assert _count(UserGroupRole, user_id=user_id, group_id=group_id) == 0
    assert _count(GroupMemberAlias, user_id=user_id) == 0
    # 邀请码名额被释放
    assert _count(InvitationCode, code="INV-ALICE") == 0
    # 牌局记录保留
    assert _count(PokerGamePlayer, user_id=user_id) == 1
    # 会话被清除
    assert client.get("/current-user").json()["success"] is False
    assert "LEAVE_GROUP" in _audit_actions()


def test_leaving_one_group_keeps_other_memberships(client, factory, login_as):
    from poker.models import UserGroupRole

    g1, _ = _group_with_organizer(factory, "G1", "orgaaaa1")
    g2, _ = _group_with_organizer(factory, "G2", "orgbbbb1")
    user_id = factory.user("alice001")
    factory.role(user_id, g1, "user")
    factory.role(user_id, g2, "user")

    login_as("alice001", g1)
    assert client.post("/user/leave-group").json()["remaining_groups"] == 1
    assert _count(UserGroupRole, user_id=user_id, group_id=g2) == 1


def test_organizer_cannot_use_leave_group(client, factory, login_as):
    from poker.models import UserGroupRole

    group_id, org_id = _group_with_organizer(factory)
    login_as("orgaaaa1", group_id)

    assert client.post("/user/leave-group").json()["success"] is False
    assert _count(UserGroupRole, user_id=org_id) == 1


def test_cannot_leave_group_during_ongoing_game(client, factory, login_as):
    from poker.models import UserGroupRole

    group_id, org_id = _group_with_organizer(factory)
    user_id = factory.user("alice001")
    factory.role(user_id, group_id, "user")
    _ongoing_game(group_id, org_id, player_id=user_id)

    login_as("alice001", group_id)
    response = client.post("/user/leave-group").json()
    assert response["success"] is False
    assert response["message"] == "leaveGroupOngoingGame"
    assert _count(UserGroupRole, user_id=user_id) == 1


# ───────────────────────── 注销账号 ─────────────────────────

def test_delete_account_page_is_public(client):
    response = client.get("/delete-account", headers={"accept": "text/html"})
    assert response.status_code == 200
    assert "confirm-text" in response.text


def test_user_still_in_group_cannot_delete(client, factory):
    group_id, _ = _group_with_organizer(factory)
    user_id = factory.user("alice001")
    factory.role(user_id, group_id, "user")

    result = _delete(client, "alice001").json()
    assert result["success"] is False
    assert result["message"] == "accountDeleteStillInGroup"
    assert result["group_name"] == "G1组"
    assert _user(user_id).username == "alice001"


def test_user_can_delete_after_leaving_all_groups(client, factory, login_as):
    from poker.models import PokerGamePlayer

    group_id, org_id = _group_with_organizer(factory)
    user_id = factory.user("alice001", nickname="爱丽丝")
    factory.role(user_id, group_id, "user")
    game_id = factory.finished_game(group_id, org_id, "周五局")
    _add_player(game_id, user_id, "爱丽丝", 30)

    login_as("alice001", group_id)
    assert client.post("/user/leave-group").json()["success"] is True

    result = _delete(client, "alice001").json()
    assert result["success"] is True, result

    row = _user(user_id)
    assert row.username == f"deleted#{user_id}"
    assert row.nickname == "已注销用户"
    assert row.is_active == 0
    assert row.avatar_url is None

    # 与其他人有关的牌局记录保留
    assert _count(PokerGamePlayer, user_id=user_id) == 1

    # 原密码不能再登录；原用户名可以重新注册
    login = client.post("/login", data={"username": "alice001", "password": DEFAULT_PASSWORD}).json()
    assert login["success"] is False
    factory.user("alice001")

    actions = _audit_actions()
    assert "LEAVE_GROUP" in actions and "DELETE_ACCOUNT" in actions


def test_user_without_any_group_can_delete(client, factory):
    user_id = factory.user("loner001")
    assert _delete(client, "loner001", confirm_text="DELETE").json()["success"] is True
    assert _user(user_id).username == f"deleted#{user_id}"


def test_confirm_text_must_match(client, factory):
    user_id = factory.user("loner001")
    result = _delete(client, "loner001", confirm_text="好的").json()
    assert result == {"success": False, "message": "accountDeleteConfirmMismatch"}
    assert _user(user_id).username == "loner001"


def test_wrong_password_is_rejected_and_rate_limited(client, factory):
    user_id = factory.user("loner001")

    for _ in range(5):
        result = _delete(client, "loner001", password="wrong-pass").json()
        assert result["message"] == "loginInvalidCredentials"

    response = _delete(client, "loner001")
    assert response.status_code == 429
    assert _user(user_id).username == "loner001"


def test_unknown_username(client):
    assert _delete(client, "nobody01").json()["message"] == "loginInvalidCredentials"


def test_disabled_account_cannot_delete(client, factory):
    user_id = factory.user("loner001", is_active=0)
    assert _delete(client, "loner001").json()["message"] == "loginAccountDisabled"
    assert _user(user_id).username == "loner001"


def test_admin_cannot_delete(client, factory):
    admin_group = factory.group("0", name="管理员")
    admin_id = factory.user("admin001")
    factory.role(admin_id, admin_group, "admin")

    assert _delete(client, "admin001").json()["message"] == "accountDeleteAdminForbidden"
    assert _user(admin_id).username == "admin001"


def test_organizer_with_members_cannot_delete(client, factory):
    group_id, org_id = _group_with_organizer(factory)
    member_id = factory.user("alice001")
    factory.role(member_id, group_id, "user")

    result = _delete(client, "orgaaaa1").json()
    assert result["message"] == "accountDeleteGroupHasMembers"
    assert result["group_name"] == "G1组"
    assert _user(org_id).username == "orgaaaa1"


def test_organizer_with_ongoing_game_cannot_delete(client, factory):
    group_id, org_id = _group_with_organizer(factory)
    _ongoing_game(group_id, org_id)

    assert _delete(client, "orgaaaa1").json()["message"] == "accountDeleteOngoingGame"


def test_organizer_also_member_elsewhere_must_leave_first(client, factory):
    _group_with_organizer(factory, "G1", "orgaaaa1")
    g2, _ = _group_with_organizer(factory, "G2", "orgbbbb1")
    org_id = _user_id("orgaaaa1")
    factory.role(org_id, g2, "user")

    result = _delete(client, "orgaaaa1").json()
    assert result["message"] == "accountDeleteStillInGroup"
    assert result["group_name"] == "G2组"


def _user_id(username):
    from poker.models import User

    db = _db()
    try:
        return db.query(User.id).filter(User.username == username).scalar()
    finally:
        db.close()


def test_organizer_alone_deletes_account_and_group(client, factory):
    from poker.models import (
        ChipRequest,
        Group,
        GroupMemberAlias,
        InvitationCode,
        PokerGame,
        PokerGamePlayer,
        UserGroupRole,
    )

    group_id, org_id = _group_with_organizer(factory)
    former_id = factory.user("former01")
    game_id = factory.finished_game(group_id, org_id, "老牌局")
    _add_player(game_id, org_id, "局头", -10)
    _add_player(game_id, former_id, "former01", 10)
    _alias(group_id, former_id, "老成员")
    factory.invite("INV-UNUSED", "G1")

    # 另一个组的数据不受影响
    other_group, other_org = _group_with_organizer(factory, "G2", "orgbbbb1")
    other_game = factory.finished_game(other_group, other_org, "别的组")
    _add_player(other_game, other_org, "别人", 0)

    result = _delete(client, "orgaaaa1").json()
    assert result["success"] is True, result
    assert result["deleted_groups"] == 1

    assert _count(Group, id=group_id) == 0
    assert _count(PokerGame, group_id=group_id) == 0
    assert _count(PokerGamePlayer, game_id=game_id) == 0
    assert _count(GroupMemberAlias, group_id=group_id) == 0
    assert _count(InvitationCode, group_code="G1") == 0
    assert _count(UserGroupRole, user_id=org_id) == 0
    assert _count(ChipRequest) == 0
    assert _user(org_id).username == f"deleted#{org_id}"

    assert _count(Group, id=other_group) == 1
    assert _count(PokerGamePlayer, game_id=other_game) == 1

    actions = _audit_actions()
    assert actions.count("DELETE_GROUP") == 1
    assert "DELETE_ACCOUNT" in actions


def test_delete_clears_existing_session_of_same_account(client, factory, login_as):
    group_id, _ = _group_with_organizer(factory)
    login_as("orgaaaa1", group_id)

    assert _delete(client, "orgaaaa1").json()["success"] is True
    assert client.get("/current-user").json()["success"] is False


# ───────────────────────── 管理员强制解散组 ─────────────────────────

def test_admin_force_delete_group_with_aliases(client, factory, login_as):
    """回归：之前强制解散不会删除备注名，存在备注名时会因外键失败。"""
    from poker.models import Group, GroupMemberAlias

    admin_group = factory.group("0", name="管理员")
    admin_id = factory.user("admin001")
    factory.role(admin_id, admin_group, "admin")

    group_id, _ = _group_with_organizer(factory)
    member_id = factory.user("alice001")
    factory.role(member_id, group_id, "user")
    _alias(group_id, member_id, "小A")

    login_as("admin001", admin_group)
    result = client.post(
        "/admin/groups/force-delete",
        data={"group_id": group_id, "group_code": "G1"},
    ).json()

    assert result["success"] is True, result
    assert result["counts"]["aliases"] == 1
    assert _count(Group, id=group_id) == 0
    assert _count(GroupMemberAlias) == 0
