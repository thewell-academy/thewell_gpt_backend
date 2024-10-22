from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from sqlalchemy import text
from sqlmodel import Session

from database.database import engine
from database.models.user import User
from fastapi.responses import JSONResponse


def get_students_list():
    with Session(engine) as session:
        query = f"""
            select id, name from users
            where is_admin is not true
            and is_active is true;
            """

        result = session.execute(text(
            query
        )).all()

    return JSONResponse([{
        "id": r[0],
        "name": r[1],
    } for r in result])


def add_admin(admin_id, name, password):
    now = datetime.now()
    with Session(engine) as session:

        session.add_all([
            User(
                id=admin_id,
                name=name,
                device_id="NA",
                password=password,
                logged_in=False,
                is_admin=True,
                is_active=True,
                created_at=now
            )
            ])
        session.commit()
    return


def add_users(user_list: list):
    now = datetime.now()
    with Session(engine) as session:

        session.add_all([
            User(
                id=user['id'],
                name=user['name'],
                device_id="NA",
                password=user['password'],
                logged_in=False,
                is_admin=False,
                is_active=True,
                created_at=now
            )
            for user in user_list])
        session.commit()
    return


def get_password(user_id):
    with Session(engine) as session:
        query = f"""
            select password from users where id = '{user_id}';
        """

        result = session.execute(text(
            query
        )).first()


    return result[0]
