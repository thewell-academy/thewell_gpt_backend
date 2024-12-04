import asyncio
import base64
import datetime
import io
import json
import time
import uuid
from io import BytesIO
from typing import Dict, List

import requests
from PIL import Image
from fastapi import Request, UploadFile, File
from openai import OpenAI
from sqlalchemy import text
from sqlmodel import Session
from fastapi.responses import JSONResponse

from service.questions.util import get_question_with_image, init_system_config
from database.database import engine
from database.models import crud
from database.models.user_question import UserQuestion
from database.models.user import User
from secret.secret import api_key

user_threads: Dict[str, List[Dict[str, str]]] = {}


async def get_users(user_id, subject):
    with Session(engine) as session:
        result = session.execute(text("SELECT * FROM users"))
        rows = result.fetchall()

        users = [User(id=row.id, name=row.name) for row in rows]
        return users


async def answer_question(
        req: Request,
        file: UploadFile = File(...),
        subject: str = 'math',
        user_id: str = "unknown",
):

    contents: bytes = await file.read()
    image = Image.open(BytesIO(contents))

    i = image.size  # current size (height,width)
    i = i[0] // 4, i[1] // 4  # new size
    downsized_image = image.resize(i)

    img_byte_arr = io.BytesIO()
    downsized_image.save(img_byte_arr, format='PNG')
    downsized_image_bytes = img_byte_arr.getvalue()

    encoded_image = base64.b64encode(contents).decode('utf-8')  # Encode as base64 string
    encoded_image_downsized = base64.b64encode(downsized_image_bytes).decode('utf-8')

    create_at = datetime.datetime.now()

    try:

        base64_image = base64.b64encode(contents).decode('utf-8')

        client = OpenAI(api_key=api_key)

        question_prompt = get_question_with_image(base64_image, subject)

        response = json.loads(client.chat.completions.create(
            messages=[init_system_config(subject), question_prompt],
            model="gpt-4o",
            max_tokens=3000
        ).model_dump_json())

        return_value = response['choices'][0]['message']['content']

        if return_value.startswith("1"):
            return_value = return_value[3:]

            await crud.create(
                UserQuestion(
                    id=f"{user_id}_{str(uuid.uuid4())}",
                    user_id=user_id,
                    subject=subject,
                    answer=return_value,
                    image=encoded_image,
                    image_small=encoded_image_downsized,
                    created_at=create_at
                )
            )
            print(return_value)
            return return_value
        else:
            return "이미지가 또렷하지 않은 것 같아요. 다시 한 번 찍어서 업로드 해주세요!"

    except Exception as e:
        print(e)
        return "서버 오류. 사진을 다시 찍어주세요."


async def get_questions(user_id, subject, start, end):

    subject_list = ["수학", "과학"]

    with Session(engine) as session:

        query = f"""
            SELECT * FROM questions
            where user_id = '{user_id}'
            and created_at between '{start}' and '{end}'
            order by created_at desc
            """
        if subject == "수학":
            query += " and subject = 'math'"
        elif subject == "과학":
            query += " and subject = 'science'"

        result = session.execute(text(
            query
        )).all()

        data = [
            UserQuestion(
                id=row.id,
                user_id=row.user_id,
                subject=row.subject,
                answer=row.answer,
                image=row.image,
                image_small=row.image_small,
                created_at=row.created_at,

            ) for row in result
        ]

        res = [{
            "id": d.id,
            "subject": d.subject,
            "answer": d.answer,
            "image_preview": d.image_small,
            "created_at": d.created_at.isoformat(),
        } for d in data]

    return JSONResponse(
        content=res,
        media_type="application/json; charset=utf-8"
    )

