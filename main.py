import os
import re
from urllib.request import Request

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controller.admin.admin_controller import admin
from controller.auth.auth_controller import auth
from controller.question_bank.question_bank_controller import question_bank
from controller.questions.questions_controller import question
from controller.test.test_controller import test
from database.database import create_db_and_tables, is_latest_migration_applied, \
    check_model_changes, run_alembic_migration

app = FastAPI()

localhost_regex = re.compile(r"^http://(localhost|127\.0\.0\.1):\d+$")

scheduler = BackgroundScheduler()


def my_cron_job():
    word_file_list = [i for i in os.listdir() if i.endswith(".docx")]
    for word_file in word_file_list:
        os.remove(word_file)


scheduler.add_job(
    my_cron_job,
    CronTrigger(minute="*")
)

# Start the scheduler
scheduler.start()


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    t1 = is_latest_migration_applied()
    t2 = check_model_changes()
    if not t1 or t2:
        # generate_revision()  # Optionally generate a revision if needed
        # run_alembic_migration()  # Run migrations at startup
        run_alembic_migration()


localhost_regex = re.compile(r"^(http://localhost:\d+|https://thewell-academy.github.io)$")

# Global CORS middleware for default behavior
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (temporary, overridden by dynamic middleware)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Dynamic CORS middleware
@app.middleware("http")
async def dynamic_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    response = await call_next(request)

    # Check if the origin is allowed by the regex
    if origin and localhost_regex.match(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.get("/ping")
async def ping():
    return "pong"


app.include_router(question)
app.include_router(auth)
app.include_router(test)
app.include_router(admin)

app.include_router(question_bank)


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()


@app.get("/ping")
async def ping():
    return "pong"
