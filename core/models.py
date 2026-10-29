"""
平台级数据模型。

User 是平台统一账号，不属于任何单一模块。
各模块（poker 等）的 user_id 外键指向这里的 platform_users 表。
"""

from sqlalchemy import Column, DateTime, Integer, String
from database import Base
from core.time import now_columbus_naive


class User(Base):

    __tablename__ = "platform_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    email_verified = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=now_columbus_naive)
    deleted_at = Column(DateTime, nullable=True)
