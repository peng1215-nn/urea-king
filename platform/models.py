from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
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
