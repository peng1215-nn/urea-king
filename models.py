from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from database import Base
from sqlalchemy import Text


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    nickname = Column(
        String(50),
        nullable=True,
    )

    role = Column(
        String(30),
        nullable=False,
        default="user",
    )

    group_id = Column(
        String(30),
        nullable=True,
    )

    avatar_url = Column(
        String(255),
        nullable=True,
    )

    invitation_code = Column(
        String(100),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class InvitationCode(Base):

    __tablename__ = "invitation_codes"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    code = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    assigned_to = Column(
        String(100),
        nullable=True,
    )

    role = Column(
        String(30),
        nullable=False,
        default="user",
    )

    group_id = Column(
        String(30),
        nullable=True,
    )

    is_used = Column(
        Integer,
        nullable=False,
        default=0,
    )

    used_by_username = Column(
        String(50),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    used_at = Column(
        DateTime,
        nullable=True,
    )


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    operator_id = Column(
        Integer,
        nullable=True,
    )

    operator_username = Column(
        String(50),
        nullable=True,
    )

    action = Column(
        String(100),
        nullable=False,
    )

    target_type = Column(
        String(50),
        nullable=False,
    )

    target_id = Column(
        Integer,
        nullable=True,
    )

    old_value = Column(
        Text,
        nullable=True,
    )

    new_value = Column(
        Text,
        nullable=True,
    )

    ip_address = Column(
        String(100),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )