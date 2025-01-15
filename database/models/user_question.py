import base64
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BINARY, VARBINARY, LargeBinary, DateTime, Text
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field

from database.database import Base


@dataclass
class UserQuestion(Base):
    __tablename__ = 'user_questions'
    id: str = Column(String, default=None, primary_key=True)
    user_id: str = Column(String, default=None, nullable=True)
    subject: str = Column(String, default=None, nullable=True)
    answer: str = Column(Text, default=None, nullable=True)
    image: str = Column(Text, default=None, nullable=True)
    image_small: str = Column(Text, default=None, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
