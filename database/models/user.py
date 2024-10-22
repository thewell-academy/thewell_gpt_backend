from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field

from database.database import Base


@dataclass
class User(Base):
    __tablename__ = 'users'
    id: str = Column(String, primary_key=True)
    name: str = Column(String, default="unknown", nullable=True)
    device_id: str = Column(String, nullable=True)
    password: str = Column(String, default="1234", nullable=True)
    logged_in: bool = Column(Boolean, default=False, nullable=False)
    is_admin: bool = Column(Boolean, default=False, nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
