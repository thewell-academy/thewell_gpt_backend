from sqlalchemy import Select
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from database.database import engine
from database.models.question import Question
from database.models.user import User


async def create(item):
    try:
        with Session(engine) as session:
            existing_user = session.query(item.__class__).filter(item.__class__.id == item.id).first()
            if existing_user is None:
                session.add(item)
                session.commit()
    except IntegrityError:
        session.rollback()
        print(f"Failed to add item due to integrity constraint. (id: {item.id})")


def get(item):
    try:
        with Session(engine) as session:
            session.exec(
                f"""
                    select * from {item.__class__.__name__}  
                """
            )
        return
    except Exception as e:
        print(e)
        return
