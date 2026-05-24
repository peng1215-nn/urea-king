from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from database import Base


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

    is_active = Column(
        Integer,
        nullable=False,
        default=1,
    )


class Group(Base):

    __tablename__ = "groups"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    group_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    group_name = Column(
        String(100),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class UserGroupRole(Base):

    __tablename__ = "user_group_roles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    group_id = Column(
        Integer,
        ForeignKey("groups.id"),
        nullable=False,
    )

    role = Column(
        String(30),
        nullable=False,
        default="user",
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

    group_code = Column(
        String(50),
        nullable=False,
    )

    role = Column(
        String(30),
        nullable=False,
        default="user",
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