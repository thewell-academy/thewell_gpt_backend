import base64
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BINARY, VARBINARY, LargeBinary, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field

from database.database import Base
from pydantic import BaseModel


@dataclass
class SubjectDetail(Base):
    __tablename__ = 'subject_details'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    subject: str = Column(String, nullable=False)  # The overall subject (e.g., "수학")
    name: str = Column(String, nullable=False)  # The current node's name (e.g., "다항식")
    parent_id: int = Column(Integer, ForeignKey('subject_details.id'), nullable=True)  # Parent ID
    path: str = Column(Text, nullable=False)  # Full hierarchical path
    value: JSONB = Column(JSONB, nullable=True)  # Dictionary to store child values or leaf node data

    # Relationships
    children = relationship("SubjectDetail", backref="parent", remote_side=[id])
