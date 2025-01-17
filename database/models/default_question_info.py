import base64
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BINARY, VARBINARY, LargeBinary, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field

from database.database import Base
from pydantic import BaseModel


class DefaultQuestionInfo(Base):
    __tablename__ = 'default_question_infos'

    id = Column(Integer, primary_key=True, index=True)
    exam = Column(String, default='')
    exam_year = Column(Integer, default=0)
    exam_month = Column(Integer, default=0)
    grade = Column(String, default='')
    file_path = Column(String, default='')
    selected_file_bytes = Column(LargeBinary, nullable=True)

    exam_question = relationship('ExamQuestion', back_populates='default_question_info', uselist=False)

    def to_json(self):
        return {
            "id": self.id,
            "exam": self.exam,
            "exam_year": self.exam_year,
            "exam_month": self.exam_month,
            "grade": self.grade,
            "file_path": self.file_path,
            "selected_file_bytes": str(self.selected_file_bytes) if self.selected_file_bytes else None,
        }
