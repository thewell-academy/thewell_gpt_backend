import json
import uuid
from typing import Dict

from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette import status

from database.database import engine, get_db_session
from database.models.question_bank import QuestionBank


async def save_questions(body, file=None, replace=False):

    question_id = body['questionId']
    question_type = body['questionType']

    subject = body['subject']
    exam = body['questionModel']['defaultQuestionInfo']['exam']
    exam_year = body['questionModel']['defaultQuestionInfo']['examYear']
    exam_month = body['questionModel']['defaultQuestionInfo']['examMonth']

    grade = body['questionModel']['defaultQuestionInfo']['grade']

    question_answer_json = body['questionModel']['answerOptionInfoList']
    question_numbers = ",".join(str(i['questionNumber']) for i in question_answer_json)

    question_script_dict = body['questionModel']['questionContentTextMap']

    exist = await same_question_exist(exam, exam_year, exam_month, question_numbers, subject)

    if exist and not replace:
        return {
            "status_code": status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
        }

    new_question = QuestionBank(
        id=str(uuid.uuid4()),
        exam=exam,
        exam_year=exam_year,
        exam_month=exam_month,
        grade=grade,
        subject=subject,
        question_type=question_type,
        question_script_dict=str(question_script_dict),
        file_data=file if isinstance(file, bytes) else None,
        question_numbers=question_numbers,
        question_answer_json=str(question_answer_json),
        valid=True
    )

    with get_db_session() as db:
        db.add(new_question)
        if replace and exist:
            with Session(engine) as session:
                query = f"""
                    UPDATE question_bank
                    SET valid = False
                    WHERE id = '{exist}';
                """
                session.execute(text(query))
        db.commit()
        return {
            "status_code": status.HTTP_200_OK,
        }


async def same_question_exist(exam, exam_year, exam_month, question_numbers, subject):
    with Session(engine) as session:
        query = f"""
                    SELECT * from question_bank
                    where exam = '{exam}' and exam_year = '{exam_year}' 
                    and exam_month = '{exam_month}' and question_numbers = '{question_numbers}'
                    and subject = '{subject}' and valid = TRUE
                    """

        result = session.execute(text(query)).first()

        if result is None:
            return None

        else:
            question_id = result[0]
            return question_id
