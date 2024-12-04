from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class DefaultQuestionInfoBase(BaseModel):
    exam: str = ''
    exam_year: int = 0
    exam_month: int = 0
    grade: str = ''
    file_path: str = ''
    selected_file_bytes: Optional[bytes] = None


class DefaultQuestionInfoCreate(BaseModel):
    exam: str = Field('', alias='exam')
    exam_year: int = Field(0, alias='examYear')
    exam_month: int = Field(0, alias='examMonth')
    grade: str = Field('', alias='grade')
    file_path: str = Field('', alias='filePath')
    selected_file_bytes: Optional[bytes] = None


class DefaultQuestionInfoRead(DefaultQuestionInfoBase):
    id: int

    class Config:
        orm_mode = True


class AnswerOptionInfoBase(BaseModel):
    question_number: int
    question_score: int
    question_text: str
    option1: str
    option2: str
    option3: str
    option4: str
    option5: str
    answer: int
    memo: str


class AnswerOptionInfoCreate(BaseModel):
    question_number: int = Field(..., alias='questionNumber')
    question_score: int = Field(..., alias='questionScore')
    question_text: str = Field(..., alias='questionText')
    options: List[str] = Field(..., alias='options')
    selected_answer: int = Field(..., alias='selectedAnswer')
    memo: str = Field('', alias='memo')


class AnswerOptionInfoRead(AnswerOptionInfoBase):
    id: int
    exam_question_id: int

    class Config:
        orm_mode = True


class ExamQuestionBase(BaseModel):
    subject: str
    default_question_info: DefaultQuestionInfoCreate
    question_content_text_map: Optional[Dict[str, Any]] = {}
    answer_option_info_list: List[AnswerOptionInfoCreate] = []
    type: str = ''


class ExamQuestionCreate(BaseModel):
    subject: str = Field(..., alias='subject')
    default_question_info: DefaultQuestionInfoCreate = Field(..., alias='defaultQuestionInfo')
    question_content_text_map: Dict[str, Any] = Field(default_factory=dict, alias='questionContentTextMap')
    answer_option_info_list: List[AnswerOptionInfoCreate] = Field(default_factory=list, alias='answerOptionInfoList')
    type: str = Field('', alias='type')


class QuestionRequest(BaseModel):
    question_id: int = Field(..., alias='questionId')
    subject: str = Field(..., alias='subject')
    question_model: ExamQuestionCreate = Field(..., alias='questionModel')
    question_type: str = Field(..., alias='questionType')


class ExamQuestionRead(ExamQuestionBase):
    id: int
    default_question_info: DefaultQuestionInfoRead
    answer_option_info_list: List[AnswerOptionInfoRead]

    class Config:
        orm_mode = True
