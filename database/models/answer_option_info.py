import base64
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BINARY, VARBINARY, LargeBinary, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from sqlmodel import SQLModel, Field

from database.database import Base
from pydantic import BaseModel


class AnswerOptionInfo(Base):
    __tablename__ = 'answer_option_infos'

    id = Column(Integer, primary_key=True, index=True)
    exam_question_id = Column(Integer, ForeignKey('exam_questions.id'), nullable=False)

    question_number = Column(Integer, nullable=False)
    question_score = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    option1 = Column(Text, nullable=False)
    option2 = Column(Text, nullable=False)
    option3 = Column(Text, nullable=False)
    option4 = Column(Text, nullable=False)
    option5 = Column(Text, nullable=False)
    answer = Column(Integer, nullable=False)
    memo = Column(Text, nullable=False)

    # Relationship back to ExamQuestion
    exam_question = relationship('ExamQuestion', back_populates='answer_option_info_list')