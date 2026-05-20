from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=False, index=True)

    password_hash = Column(String(255), nullable=False)

    nickname = Column(String(50), nullable=False)

    role = Column(String(30), nullable=False, default="user")

    invitation_code = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class InvitationCode(Base):
    __tablename__ = "invitation_codes"

    id = Column(Integer, primary_key=True, index=True)

    code = Column(String(100), unique=True, nullable=False, index=True)

    assigned_to = Column(String(100), nullable=True)

    role = Column(String(30), nullable=False, default="user")

    group_id = Column(Integer, nullable=True)

    is_used = Column(Integer, nullable=False, default=0)

    used_by_username = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    used_at = Column(DateTime, nullable=True)