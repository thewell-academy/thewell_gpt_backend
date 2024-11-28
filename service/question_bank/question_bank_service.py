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
    subject = body['subject']
    question_type = body['questionType']

    subject = body['subject']
    exam = body['questionModel']['defaultQuestionInfo']['exam']
    exam_year = body['questionModel']['defaultQuestionInfo']['examYear']
    exam_month = body['questionModel']['defaultQuestionInfo']['examMonth']
    question_number = body['questionModel']['defaultQuestionInfo']['questionNumber']
    question_score = body['questionModel']['defaultQuestionInfo']['questionScore']
    question_text = body['questionModel']['defaultQuestionInfo']['questionText']

    question_script_dict = body['questionModel']['questionContentTextMap']

    answer_option_list = body['questionModel']['answerOptionInfo']['options']
    answer = body['questionModel']['answerOptionInfo']['selectedAnswer']
    memo = body['questionModel']['answerOptionInfo']['memo']

    exist = await same_question_exist(exam, exam_year, exam_month, question_number, subject)

    if exist and not replace:
        return {
            "status_code": status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
        }

    new_question = QuestionBank(
        id=str(uuid.uuid4()),
        exam=exam,
        exam_year=exam_year,
        exam_month=exam_month,
        subject=subject,
        question_number=question_number,
        question_score=question_score,
        question_type=question_type,
        question_text=question_text,
        question_script_dict=str(question_script_dict),
        answer_option_list=str(answer_option_list),
        answer=answer,
        memo=memo,
        file_data=file if isinstance(file, bytes) else None,
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


async def same_question_exist(exam, exam_year, exam_month, question_number, subject):
    with Session(engine) as session:
        query = f"""
                    SELECT * from question_bank
                    where exam = '{exam}' and exam_year = '{exam_year}' 
                    and exam_month = '{exam_month}' and question_number = '{question_number}'
                    and subject = '{subject}' and valid = TRUE
                    """

        result = session.execute(text(query)).first()

        if result is None:
            return None

        else:
            question_id = result[0]
            return question_id
