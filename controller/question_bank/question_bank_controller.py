import json
from io import BytesIO
from typing import Optional
from uuid import uuid4
from PIL import Image
from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database.database import get_db
from database.pydantic_models.pydantic_models import ExamQuestionCreate, QuestionRequest
from service.question_bank.question_bank_service import save_exam_question

question_bank = APIRouter(
    prefix="/question-bank",
    tags=["question-bank"],
)


@question_bank.post("/add-all/file")
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

    # Validate and parse the data using the Pydantic model
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

    res = await save_exam_question(exam_question_data, replace, db)

    return JSONResponse(
        status_code=res['status_code'],
        content=res.get('detail', {})
    )


@question_bank.post("/add-all")
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

    exam_question_data = question_request.question_model

    res = await save_exam_question(exam_question_data, replace, db)

    return JSONResponse(
        status_code=res['status_code'],
        content={}
    )
