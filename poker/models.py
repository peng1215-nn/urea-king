"""Poker module models — all tables prefixed with poker_
Note: audit logs and announcements are platform-level concerns and live in core/models.py.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from database import Base


class PokerGroup(Base):
    """A poker group (game circle). Replaces the old 'groups' table."""

    __tablename__ = "poker_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_code = Column(String(50), unique=True, nullable=False, index=True)
    group_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PokerUserGroupRole(Base):
    """Membership of a platform user in a poker group with a role."""

    __tablename__ = "poker_user_group_roles"

    id = Column(Integer, primary_key=True, index=True)
    # References platform_users.id — no FK constraint across logical modules
    user_id = Column(Integer, nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("poker_groups.id"), nullable=False)
    role = Column(String(30), nullable=False, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class PokerInvitationCode(Base):
    """Invite codes for joining a poker group.
    Format: POKER-G{group_id:03d}-{RANDOM4}
    """

    __tablename__ = "poker_invitation_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    assigned_to = Column(String(100), nullable=True)
    group_id = Column(Integer, ForeignKey("poker_groups.id"), nullable=False)
    role = Column(String(30), nullable=False, default="user")
    is_used = Column(Integer, nullable=False, default=0)
    used_by_user_id = Column(Integer, nullable=True)
    used_by_username = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)


class PokerGame(Base):

    __tablename__ = "poker_games"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("poker_groups.id"), nullable=False, index=True)
    organizer_id = Column(Integer, nullable=False)  # references platform_users.id
    status = Column(String(20), nullable=False, default="ongoing")
    name = Column(String(100), nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_buy_in = Column(Integer, nullable=True)
    total_cash_out = Column(Integer, nullable=True)
    is_balanced = Column(Integer, nullable=True)
    player_count = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)


class PokerGamePlayer(Base):

    __tablename__ = "poker_game_players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("poker_games.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)  # references platform_users.id
    nickname = Column(String(50), nullable=True)
    total_buy_in = Column(Integer, nullable=False, default=0)
    cash_out = Column(Integer, nullable=True)
    net = Column(Integer, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PokerChipRequest(Base):

    __tablename__ = "poker_chip_requests"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("poker_games.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)  # references platform_users.id
    nickname = Column(String(50), nullable=True)
    type = Column(String(20), nullable=False, default="normal")
    amount = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)  # references platform_users.id
