import json
import uuid
from typing import Dict

from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette import status

from database.database import engine, get_db
from database.models.answer_option_info import AnswerOptionInfo
from database.models.default_question_info import DefaultQuestionInfo
from database.models.exam_question import ExamQuestion
from database.pydantic_models.pydantic_models import ExamQuestionCreate


async def save_exam_question(exam_question_data: ExamQuestionCreate, replace: bool, db: Session):
    # Extract data from exam_question_data
    subject = exam_question_data.subject
    grade = exam_question_data.default_question_info.grade
    exam = exam_question_data.default_question_info.exam
    exam_year = exam_question_data.default_question_info.exam_year
    exam_month = exam_question_data.default_question_info.exam_month

    question_numbers_list = [str(i.question_number) for i in exam_question_data.answer_option_info_list]
    question_numbers = ",".join(question_numbers_list) if question_numbers_list else ""

    # Check if the same question exists
    exist = same_question_exists(exam, exam_year, exam_month, question_numbers, subject, grade, db)

    if exist and replace:
        existing_question = db.query(ExamQuestion).filter(ExamQuestion.id == exist).first()
        if existing_question:
            existing_question.valid = False
            db.commit()
            db.refresh(existing_question)
        else:
            # Handle case where the existing question is not found
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Existing question not found."
            }

    if exist and not replace:
        return {
            "status_code": status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
        }

    # Create DefaultQuestionInfo instance
    db_default_info = DefaultQuestionInfo(
        exam=exam_question_data.default_question_info.exam,
        exam_year=exam_question_data.default_question_info.exam_year,
        exam_month=exam_question_data.default_question_info.exam_month,
        grade=exam_question_data.default_question_info.grade,
        file_path=exam_question_data.default_question_info.file_path,
        selected_file_bytes=exam_question_data.default_question_info.selected_file_bytes
    )

    # Create ExamQuestion instance
    db_exam_question = ExamQuestion(
        subject=exam_question_data.subject,
        type=exam_question_data.type,
        question_content_text_map=exam_question_data.question_content_text_map,
        question_numbers=question_numbers,  # Now defined in the model
        default_question_info=db_default_info  # Correct usage
    )

    # Create AnswerOptionInfo instances
    for answer_option_data in exam_question_data.answer_option_info_list:
        db_answer_option = AnswerOptionInfo(
            question_number=answer_option_data.question_number,
            question_score=answer_option_data.question_score,
            question_text=answer_option_data.question_text,
            option1=answer_option_data.options[0],
            option2=answer_option_data.options[1],
            option3=answer_option_data.options[2],
            option4=answer_option_data.options[3],
            option5=answer_option_data.options[4],
            answer=answer_option_data.selected_answer,
            memo=answer_option_data.memo
        )
        db_exam_question.answer_option_info_list.append(db_answer_option)

    # Add and commit to the database
    db.add(db_exam_question)
    db.commit()
    db.refresh(db_exam_question)
    return {
        "status_code": status.HTTP_200_OK,
    }


def same_question_exists(exam, exam_year, exam_month, question_numbers, subject, grade, db: Session):
    # Ensure data types
    if not isinstance(exam_year, int):
        exam_year = int(exam_year)
    if not isinstance(exam_month, int):
        exam_month = int(exam_month)
    if not isinstance(question_numbers, str):
        question_numbers = str(question_numbers)

    existing_question = db.query(ExamQuestion).join(DefaultQuestionInfo).filter(
        ExamQuestion.subject == subject,
        ExamQuestion.valid == True,
        ExamQuestion.question_numbers == question_numbers,
        DefaultQuestionInfo.exam == exam,
        DefaultQuestionInfo.exam_year == exam_year,
        DefaultQuestionInfo.exam_month == exam_month,
        DefaultQuestionInfo.grade == grade,
    ).first()

    if existing_question:
        return existing_question.id
    else:
        return None
