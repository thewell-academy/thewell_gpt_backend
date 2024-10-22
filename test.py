# 필요한 라이브러리 import하기
import subprocess
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session
from sqlalchemy import text

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

with Session(engine) as session:
    session.execute(text("select 1;"))