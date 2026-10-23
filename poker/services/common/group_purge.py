"""
删除一个组及组内全部记录。管理员强制解散组、局头注销账号共用。
"""

from poker.models import (
    ChipRequest,
    GroupMemberAlias,
    InvitationCode,
    PokerGame,
    PokerGamePlayer,
    UserGroupRole,
)


def purge_group(db, group):
    """
    删除一个组及组内全部记录（不提交事务，由调用方提交）。
    管理员强制解散组与局头注销共用。返回各类记录的删除数量。
    """
    game_ids = [row[0] for row in db.query(PokerGame.id).filter(PokerGame.group_id == group.id).all()]
    counts = {"games": len(game_ids), "chip_requests": 0, "players": 0}

    if game_ids:
        counts["chip_requests"] = db.query(ChipRequest).filter(
            ChipRequest.game_id.in_(game_ids)
        ).delete(synchronize_session=False)
        counts["players"] = db.query(PokerGamePlayer).filter(
            PokerGamePlayer.game_id.in_(game_ids)
        ).delete(synchronize_session=False)
        db.query(PokerGame).filter(PokerGame.id.in_(game_ids)).delete(synchronize_session=False)

    counts["aliases"] = db.query(GroupMemberAlias).filter(
        GroupMemberAlias.group_id == group.id
    ).delete(synchronize_session=False)
    counts["members"] = db.query(UserGroupRole).filter(
        UserGroupRole.group_id == group.id
    ).delete(synchronize_session=False)
    counts["invites"] = db.query(InvitationCode).filter(
        InvitationCode.group_code == group.group_code
    ).delete(synchronize_session=False)

    db.delete(group)
    return counts
