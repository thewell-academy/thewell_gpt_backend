import base64
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BINARY, VARBINARY, LargeBinary, DateTime, Text
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field

from database.database import Base


@dataclass
class QuestionBank(Base):
    __tablename__ = 'question_bank'
    id: str = Column(String, default=None, primary_key=True)

    exam: str = Column(String, nullable=False)
    exam_year: int = Column(Integer, nullable=False)
    exam_month: int = Column(Integer, nullable=False)

    grade: str = Column(String, nullable=False, default="", server_default="")

    subject: str = Column(String, nullable=False)

    question_type: str = Column(String, nullable=False)
    question_script_dict: str = Column(String, nullable=False)  # json dict

    file_data: bytes = Column(LargeBinary, nullable=True)  # Store file as binary data

    question_numbers: str = Column(String, nullable=False)  # json dict

    question_answer_json: str = Column(String, nullable=False)  # list

    valid: bool = Column(Boolean, nullable=True, default=True)

