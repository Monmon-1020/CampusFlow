import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("campusflow", broker=REDIS_URL, backend=REDIS_URL, include=["src.tasks"])

# Celery configuration
app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "send-assignment-reminders": {
            "task": "src.tasks.send_assignment_reminders",
            "schedule": crontab(hour=7, minute=0),  # Every day at 07:00
        },
    },
)

if __name__ == "__main__":
    app.start()
