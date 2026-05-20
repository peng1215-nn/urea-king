from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = (Column(
        Integer,
        primary_key=True,
        index=True
    ))

    username = Column(
        String(50),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(30),
        nullable=False,
        default="user"
    )

    invitation_code = Column(
        String(100)
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )