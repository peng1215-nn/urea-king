"""
平台级数据模型。

User 是平台统一账号，不属于任何单一模块。
各模块（poker 等）的 user_id 外键指向这里的 platform_users 表。
"""

from sqlalchemy import Column, DateTime, Index, Integer, String, UniqueConstraint, func
from database import Base
from core.time import now_columbus_naive


class User(Base):

    __tablename__ = "platform_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    # 已验证的邮箱：全站唯一。只有验证成功的账号才占用邮箱
    email = Column(String(255), unique=True, nullable=True, index=True)
    # 注册或更换后、还没验证的邮箱：不占用，可以同时出现在多个账号上，谁先验证归谁
    pending_email = Column(String(255), nullable=True, index=True)
    email_verified = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=now_columbus_naive)
    deleted_at = Column(DateTime, nullable=True)


# 昵称全站唯一（不区分大小写，已注销的账号不算），见 poker/services/common/nicknames.py
Index(
    "uq_platform_users_nickname_lower",
    func.lower(User.nickname),
    unique=True,
    postgresql_where=User.deleted_at.is_(None),
    sqlite_where=User.deleted_at.is_(None),
)


class UserModule(Base):
    """记录用户在哪些平台模块有账号。

    一个用户首次在某模块完成注册验证或首次登录时插入一行。
    同一 (user_id, module) 组合唯一，不会重复记录。
    module 取值：'poker' | 'mahjong' | ...（各模块自己的标识符）
    """

    __tablename__ = "platform_user_modules"
    __table_args__ = (
        UniqueConstraint("user_id", "module", name="uq_user_modules_user_module"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    module = Column(String(50), nullable=False)
    joined_at = Column(DateTime, nullable=False, default=now_columbus_naive)
    is_active = Column(Integer, nullable=False, default=1)
