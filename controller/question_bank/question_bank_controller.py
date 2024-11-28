import json
from io import BytesIO
from typing import Optional
from uuid import uuid4
from PIL import Image
from fastapi import APIRouter, Form
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse


from service.question_bank.question_bank_service import save_questions

question_bank = APIRouter(
    prefix="/question-bank",
    tags=["question-bank"],
)


@question_bank.post("/add-all/file")
async def create_upload_with_file(
    body: str = Form(...),  # JSON data as a form field
    file: UploadFile = File(...),  # File
    replace: bool = False
):
    # Parse the JSON string
    body_data = json.loads(body)

    # Process the file
    if file:
        contents: bytes = await file.read()
    else:
        contents: bytes = None

    res = await save_questions(body_data, contents, replace)

    return JSONResponse(
        status_code=res['status_code'],
        content={}
    )


@question_bank.post("/add-all")
async def create_upload_without_file(
    request: Request,
    replace: bool = False,
):
    request_body = await request.json()
    res = await save_questions(request_body, None, replace)

    return JSONResponse(
        status_code=res['status_code'],
        content={}
    )
