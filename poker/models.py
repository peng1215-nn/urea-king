from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from database import Base
from utils.time import now_columbus_naive


class User(Base):

    __tablename__ = "poker_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    invitation_code = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=now_columbus_naive)
    is_active = Column(Integer, nullable=False, default=1)


class Group(Base):

    __tablename__ = "poker_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_code = Column(String(50), unique=True, nullable=False, index=True)
    group_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    invite_code_limit = Column(Integer, nullable=False, default=27)
    created_at = Column(DateTime, default=now_columbus_naive)


class UserGroupRole(Base):

    __tablename__ = "poker_user_group_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group_roles_user_group"),
        # 查组内成员（按组查）；按用户查可以用上面的唯一约束
        Index("ix_user_group_roles_group_id", "group_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("poker_users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("poker_groups.id"), nullable=False)
    role = Column(String(30), nullable=False, default="user")
    allow_organizer_chip_op = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=now_columbus_naive)


class InvitationCode(Base):

    __tablename__ = "poker_invitation_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    assigned_to = Column(String(100), nullable=True)
    group_code = Column(String(50), nullable=False)
    role = Column(String(30), nullable=False, default="user")
    is_used = Column(Integer, nullable=False, default=0)
    used_by_username = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=now_columbus_naive)
    used_at = Column(DateTime, nullable=True)


class AuditLog(Base):

    __tablename__ = "poker_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, nullable=True)
    operator_username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=now_columbus_naive)


class Announcement(Base):

    __tablename__ = "poker_announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now_columbus_naive)
    updated_at = Column(
        DateTime,
        default=now_columbus_naive,
        onupdate=now_columbus_naive,
    )


class PokerGame(Base):

    __tablename__ = "poker_games"
    __table_args__ = (
        CheckConstraint("status IN ('ongoing', 'finished')", name="ck_games_status"),
        # 牌局日志、统计：按组 + 状态筛选，按结束时间排序
        Index("ix_games_group_status_ended", "group_id", "status", "ended_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("poker_groups.id"), nullable=False, index=True)
    organizer_id = Column(Integer, ForeignKey("poker_users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="ongoing")
    name = Column(String(100), nullable=True)
    started_at = Column(DateTime, nullable=False, default=now_columbus_naive)
    ended_at = Column(DateTime, nullable=True)
    total_buy_in = Column(Integer, nullable=True)
    total_cash_out = Column(Integer, nullable=True)
    is_balanced = Column(Integer, nullable=True)
    player_count = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)


class PokerGamePlayer(Base):

    __tablename__ = "poker_game_players"
    __table_args__ = (
        UniqueConstraint("game_id", "user_id", name="uq_game_players_game_user"),
        CheckConstraint("total_buy_in >= 0", name="ck_game_players_buy_in_nonneg"),
        CheckConstraint("cash_out IS NULL OR cash_out >= 0", name="ck_game_players_cash_out_nonneg"),
        # 个人走势、是否在进行中的牌局里：按用户查
        Index("ix_game_players_user_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("poker_games.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("poker_users.id"), nullable=False)
    nickname = Column(String(50), nullable=True)
    total_buy_in = Column(Integer, nullable=False, default=0)
    cash_out = Column(Integer, nullable=True)
    net = Column(Integer, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    joined_at = Column(DateTime, nullable=False, default=now_columbus_naive)


class GroupMemberAlias(Base):

    __tablename__ = "poker_group_member_aliases"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_member_aliases_group_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("poker_groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("poker_users.id"), nullable=False, index=True)
    alias = Column(String(50), nullable=False)
    updated_at = Column(DateTime, default=now_columbus_naive, onupdate=now_columbus_naive)


class ChipRequest(Base):

    __tablename__ = "poker_chip_requests"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_chip_requests_amount_pos"),
    )

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("poker_games.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("poker_users.id"), nullable=False)
    nickname = Column(String(50), nullable=True)
    type = Column(String(20), nullable=False, default="normal")
    amount = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    requested_at = Column(DateTime, nullable=False, default=now_columbus_naive)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("poker_users.id"), nullable=True)