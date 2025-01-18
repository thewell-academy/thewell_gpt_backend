import json
from io import BytesIO
from typing import Optional, List
from fastapi.encoders import jsonable_encoder
from uuid import uuid4
from PIL import Image
from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from database.database import get_db
from database.pydantic_models.pydantic_models import ExamQuestionCreate, QuestionRequest
from service.question_bank.question_bank_service import save_exam_question, save_subject_details, \
    get_subject_details_data, delete_question, export_question_service

question_bank = APIRouter(
    prefix="/question-bank",
    tags=["question-bank"],
)


@question_bank.post("/add/file")
async def create_upload_with_file(
        body: str = Form(...),  # JSON data as a form field
        file: UploadFile = File(...),  # File
        replace: bool = Form(False),
        db: Session = Depends(get_db)
):
    # Parse the JSON string
    try:
        body_data = json.loads(body)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in 'body': {str(e)}")

    try:
        question_request = QuestionRequest(**body_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    exam_question_data = question_request.question_model

    # Read the file contents
    contents: Optional[bytes] = await file.read() if file else None

    # Assign the file contents to selected_file_bytes
    if contents:
        exam_question_data.default_question_info.selected_file_bytes = contents

    res = await save_exam_question(question_request, replace, db)

    return JSONResponse(
        status_code=res['status_code'],
        content=res.get('detail', {})
    )


@question_bank.post("/add")
async def create_upload_without_file(
        request: Request,
        replace: bool = False,
        db: Session = Depends(get_db)
):
    request_body = await request.json()

    try:
        question_request = QuestionRequest(**request_body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    print(question_request)

    res = await save_exam_question(question_request, replace, db)

    return JSONResponse(
        status_code=res['status_code'],
        content={}
    )


@question_bank.post("/subject-details/{subject}")
async def add_subject_details(
        request: Request,
        subject: str,
        db: Session = Depends(get_db)
):
    data = await request.json()

    await save_subject_details(subject, data, db)


@question_bank.get("/subject-details/{subject}")
async def get_subject_details(
        subject: str,
        db: Session = Depends(get_db)
):
    return JSONResponse(
        jsonable_encoder(
            await get_subject_details_data(subject, db)),
        media_type="application/json; charset=utf-8"
    )


@question_bank.delete("/{question_id}")
async def delete_question_by_id(
        question_id: str,
        db: Session = Depends(get_db)
):
    return await delete_question(question_id, db)


@question_bank.get("/export")
async def export_question(
        subject: str,
        exam: str,
        selections: str,
        years: str,
        months: str,
        grades: str,
        db: Session = Depends(get_db)
):

    selections = selections.split(',')
    years = [int(i) for i in years.split(',')] if len(years) > 0 else []
    months = [int(i) for i in months.split(',')] if len(months) > 0 else []
    grades = grades.split(',')

    file_path = await export_question_service(
            subject, exam, selections, years, months, grades, db
        )

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="output.docx",
    )
