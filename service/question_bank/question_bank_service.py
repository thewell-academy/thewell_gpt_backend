import json
import uuid
from typing import Dict, List

from docx import Document
from docx.shared import Inches
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette import status
from database.models.answer_option_info import AnswerOptionInfo
from database.models.default_question_info import DefaultQuestionInfo
from database.models.exam_question import ExamQuestion
from database.models.subject_detail import SubjectDetail
from database.pydantic_models.pydantic_models import ExamQuestionCreate, QuestionRequest
from sqlalchemy.orm.attributes import flag_modified
import uuid

from service.question_bank.question_bank_util import TableFlowManager, get_big_text, get_big_text


async def save_exam_question(question_request: QuestionRequest, replace: bool, db: Session):

    exam_question_data = question_request.question_model

    try:
        subject = exam_question_data.subject
        grade = exam_question_data.default_question_info.grade
        exam = exam_question_data.default_question_info.exam
        exam_year = exam_question_data.default_question_info.exam_year
        exam_month = exam_question_data.default_question_info.exam_month

        question_numbers_list = [str(i.question_number) for i in exam_question_data.answer_option_info_list]
        question_numbers = ",".join(question_numbers_list) if question_numbers_list else ""

        exist = same_question_exists(exam, exam_year, exam_month, question_numbers, subject, grade, db)

        if exist and replace:
            existing_question = db.query(ExamQuestion).filter(ExamQuestion.id == exist).first()
            if existing_question:
                existing_question.valid = False
                db.commit()
                db.refresh(existing_question)
            else:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Existing question not found."
                }

        if exist and not replace:
            return {
                "status_code": status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
            }

        db_default_info = DefaultQuestionInfo(
            exam=exam_question_data.default_question_info.exam,
            exam_year=exam_question_data.default_question_info.exam_year,
            exam_month=exam_question_data.default_question_info.exam_month,
            grade=exam_question_data.default_question_info.grade,
            file_path=exam_question_data.default_question_info.file_path,
            selected_file_bytes=exam_question_data.default_question_info.selected_file_bytes
        )

        db_exam_question = ExamQuestion(
            subject=exam_question_data.subject,
            type=question_request.question_type,
            question_content_text_map=exam_question_data.question_content_text_map,
            question_numbers=question_numbers,  # Now defined in the model
            default_question_info=db_default_info  # Correct usage
        )

        for answer_option_data in exam_question_data.answer_option_info_list:
            db_answer_option = AnswerOptionInfo(
                question_number=answer_option_data.question_number,
                question_score=answer_option_data.question_score,
                abc_option_list=answer_option_data.abc_option_list,
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

        db.add(db_exam_question)
        db.commit()
        db.refresh(db_exam_question)
        return {
            "status_code": status.HTTP_200_OK,
        }
    except Exception as e:
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }


def same_question_exists(exam, exam_year, exam_month, question_numbers, subject, grade, db: Session):
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


async def save_subject_details(subject: str, details: dict, db: Session, parent_id: int = None, path: str = ""):
    for key, value in details.items():
        current_path = f"{path} > {key}" if path else key

        if isinstance(value, list):
            value = {}

        existing_node = db.query(SubjectDetail).filter_by(subject=subject, name=key, parent_id=parent_id).first()

        if existing_node:
            if isinstance(value, dict):
                await save_subject_details(subject, value, db, existing_node.id, current_path)
            else:
                existing_node.value = value
                db.commit()
        else:
            new_node = SubjectDetail(
                subject=subject,
                name=key,
                parent_id=parent_id,
                path=current_path,
                value=None if isinstance(value, dict) else value,
            )
            db.add(new_node)
            db.commit()
            db.refresh(new_node)

            if isinstance(value, dict):
                await save_subject_details(subject, value, db, new_node.id, current_path)


async def get_subject_details_data(subject: str, db: Session):
    nodes = db.query(SubjectDetail).filter_by(subject=subject).all()

    node_map = {node.id: node for node in nodes}

    hierarchy = {}

    for node in nodes:
        current_entry = {}

        if node.parent_id:
            parent = node_map[node.parent_id]
            parent_entry = hierarchy
            for part in parent.path.split(" > "):
                parent_entry = parent_entry.setdefault(part, {})
            parent_entry[node.name] = current_entry
        else:
            hierarchy[node.name] = current_entry

    return hierarchy


async def delete_question(question_id, db: Session):
    db.execute(text(f"DELETE FROM answer_option_infos WHERE exam_question_id = '{question_id}';"))
    db.commit()
    db.execute(text(f"DELETE FROM exam_questions WHERE id = '{question_id}';"))
    db.commit()
    db.execute(text(f"DELETE FROM default_question_infos WHERE id = '{question_id}';"))
    db.commit()


async def export_question_service(
        subject: str,
        exam: str,
        selections: List[str],
        years: List[int],
        months: List[int],
        grades: List[str],
        db: Session
):
    if exam == "수능":
        existing_question_query_result = db.query(ExamQuestion).join(DefaultQuestionInfo).filter(
            ExamQuestion.valid == True,
            ExamQuestion.subject == subject,
            DefaultQuestionInfo.exam == exam,
            ExamQuestion.type.in_(selections),
            DefaultQuestionInfo.exam_year.in_(years),
        ).all()
    else:
        existing_question_query_result = db.query(ExamQuestion).join(DefaultQuestionInfo).filter(
            ExamQuestion.valid == True,
            ExamQuestion.subject == subject,
            DefaultQuestionInfo.exam == exam,
            ExamQuestion.type.in_(selections),
            DefaultQuestionInfo.exam_year.in_(years),
            DefaultQuestionInfo.exam_month.in_(months),
            DefaultQuestionInfo.grade.in_(grades),
        ).all()

    existing_question_list: List[ExamQuestion] = [
        question() if isinstance(question, type) else question
        for question in existing_question_query_result
    ]

    # if not existing_question_list:
    #     # If no questions exist, avoid creating an empty document
    #     print("No questions available for the given filters.")
    #     return []

    # Create Document and configure section margins
    doc = Document()

    section = doc.sections[0]
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)

    manager = TableFlowManager(
        doc,
        max_lines_per_cell=25,
        max_chars_per_line=70,
    )

    print(f"exam question len: {len(existing_question_list)}")
    for exam_question_class in existing_question_list:
        big_text = get_big_text(exam_question_class)

        manager.add_question(
            big_text=big_text,
            subquestions=[
                (
                    i.question_text,
                    [i.option1, i.option2, i.option3, i.option4, i.option5]
                )
                for i in exam_question_class.answer_option_info_list
            ]
        )

    output_file = f"{str(uuid.uuid4())}.docx"
    doc.save(output_file)
    print(f"Document saved as {output_file}")

    return [i.question_content_text_map for i in existing_question_list]

