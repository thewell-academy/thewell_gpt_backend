import json
from typing import Dict, List

import openai
import requests
from fastapi import APIRouter, HTTPException
from fastapi import FastAPI, File, UploadFile, Request
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import engine
from secret.secret import api_key
from service.auth.auth_service import login
from service.questions.questions_service import get_questions, answer_question

user_threads: Dict[str, List[Dict[str, str]]] = {}

test = APIRouter(
    prefix="/test",
    tags=["test"],
)


@test.post("/ask")
async def get_ask(request: Request):
    d = await request.json()
    question = d.get("question")
    user_id = "my_user_id"
    system_message = {
        "role": "system",
        "content": "You are a general AI assistant that helps users with their questions."
    }

    if user_id not in user_threads:
        # Start with the system message to define the assistant's behavior
        user_threads[user_id] = [system_message]

        # Append the new question to the conversation history
    user_threads[user_id].append({"role": "user", "content": question})

    try:

        client = OpenAI(
            # This is the default and can be omitted
            api_key=api_key,
        )

        response = json.loads(client.chat.completions.create(
            messages=user_threads[user_id],
            model="gpt-3.5-turbo",
        ).model_dump_json())

        # Get the assistant's reply
        assistant_reply = response['choices'][0]['message']['content']

        # Append the assistant's reply to the conversation history
        user_threads[user_id].append({"role": "assistant", "content": assistant_reply})

        print(user_threads)

        return {"response": assistant_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

