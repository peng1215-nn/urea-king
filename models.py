from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class ContactMessage(Base):

    __tablename__ = "landing_contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
