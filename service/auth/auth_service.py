from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.testing.pickleable import User

from database.database import engine


async def login(request: Request):
    d = await request.json()
    user_id = d['id']
    password = d['password']

    with Session(engine) as session:

        query = f"""
            SELECT * FROM users
            where id = '{user_id}'
            and password = '{password}'
            """

        result = session.execute(text(
            query
        )).all()

        data = [
            User(
                id=row.id,
                password=row.password

            ) for row in result
        ]

    if len(data) > 0:
        return "login"
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
