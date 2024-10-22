from fastapi import APIRouter
from fastapi import FastAPI, File, UploadFile, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import engine
from service.auth.auth_service import login

auth = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth.get("/{device_id}")
async def root(device_id: str):
    return "OK"


@auth.post("/login")
async def user_login(request: Request):
    return await login(request)
