from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from database import Base


class PlatformUser(Base):
    """Platform user account — registration, login, identity only."""

    __tablename__ = "platform_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformGroup(Base):
    """Platform-level group for admin/developer accounts.
    Completely separate from poker groups.
    """

    __tablename__ = "platform_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_code = Column(String(50), unique=True, nullable=False, index=True)
    group_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformUserGroupRole(Base):
    """Membership of a platform user in a platform group with a role."""

    __tablename__ = "platform_user_group_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # references platform_users.id
    group_id = Column(Integer, nullable=False, index=True)  # references platform_groups.id
    role = Column(String(30), nullable=False, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformAuditLog(Base):
    """System-wide audit log — belongs to platform, records all site activity.
    Includes the operator's platform group and role for full context.
    """

    __tablename__ = "platform_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, nullable=True)
    operator_username = Column(String(50), nullable=True)
    operator_group_id = Column(Integer, nullable=True)    # platform or poker group id
    operator_group_code = Column(String(50), nullable=True)  # human-readable group identifier
    operator_role = Column(String(30), nullable=True)     # role in that group
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformAnnouncement(Base):
    """Announcements created by platform admins, visible across the site."""

    __tablename__ = "platform_announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, nullable=True)        # references platform_users.id
    author_username = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
