from fastapi import APIRouter
from fastapi import FastAPI, File, UploadFile, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import engine
from service.auth.auth_service import login
from service.questions.questions_service import get_questions, answer_question

question = APIRouter(
    prefix="/ask",
    tags=["ask"],
)


@question.post("/{subject}/{user_id}")
async def create_upload_file(
        req: Request,
        file: UploadFile = File(...),
        subject: str = 'math',
        user_id: str = "unknown",
):
    return await answer_question(req, file, subject, user_id)


@question.get("/history/{subject}/{device_id}")
async def get_questions_list(
        subject: str = 'math',
        device_id: str = "unknown",
        start: str = None,
        end: str = None,
):
    return await get_questions(device_id, subject, start, end)
