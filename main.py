from alembic.context import run_migrations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re

from controller.auth.auth_controller import auth
from controller.admin.admin_controller import admin
from controller.question_bank.question_bank_controller import question_bank
from controller.questions.questions_controller import question
from controller.test.test_controller import test
from database.database import create_db_and_tables, is_latest_migration_applied, \
    check_model_changes, run_alembic_migration, generate_revision

app = FastAPI()

localhost_regex = re.compile(r"^http://(localhost|127\.0\.0\.1):\d+$")


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    t1 = is_latest_migration_applied()
    t2 = check_model_changes()
    if not t1 or t2:
        # generate_revision()  # Optionally generate a revision if needed
        # run_alembic_migration()  # Run migrations at startup
        run_alembic_migration()


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily set to allow all origins (will handle dynamically)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.middleware("http")
async def dynamic_cors_middleware(request, call_next):
    origin = request.headers.get("origin")
    if origin and localhost_regex.match(origin):
        response = await call_next(request)
        response.headers.Access_Control_Allow_Origin = origin
        response.headers.Access_Control_Allow_Methods = 'POST, GET, OPTIONS, PUT, DELETE'
        response.headers.Access_Control_Allow_Headers = 'Authorization, Content-Type'
        return response
    return await call_next(request)


@app.get("/ping")
async def ping():
    return "pong"


app.include_router(question)
app.include_router(auth)
app.include_router(test)
app.include_router(admin)

app.include_router(question_bank)


@app.get("/ping")
async def ping():
    return "pong"