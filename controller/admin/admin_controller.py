from fastapi import APIRouter
from fastapi import FastAPI, File, UploadFile, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import engine
from service.admin.admin_service import *
from service.auth.auth_service import login

admin = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@admin.get("/get/users")
async def get_students():
    return get_students_list()


@admin.post("/add/admin")
async def add_admins(admin_id, name, password):
    # data = await request.json()
    return add_admin(admin_id, name, password)


@admin.get("/{user_id}/password")
async def get_user_password(user_id):
    return get_password(user_id)


@admin.post("/add/users")
async def add_user(req: Request):
    d = await req.json()

    return add_users(d)
