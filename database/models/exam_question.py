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
class ExamQuestion(Base):
    __tablename__ = 'exam_questions'

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    type = Column(String, default='')
    valid = Column(Boolean, default=True)  # Add this field with default value

    question_content_text_map = Column(JSONB, default=dict)
    question_numbers = Column(String, nullable=False)  # Add this field

    default_question_info_id = Column(Integer, ForeignKey('default_question_infos.id'))
    default_question_info = relationship('DefaultQuestionInfo', back_populates='exam_question')

    answer_option_info_list = relationship(
        'AnswerOptionInfo',
        back_populates='exam_question',
        cascade='all, delete-orphan'
    )
