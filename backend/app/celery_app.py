from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "workbridge_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.milestones"],
)
celery_app.conf.update(
    timezone="UTC",
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "recover-overdue-milestone-reviews": {
            "task": "app.tasks.milestones.process_overdue_reviews",
            "schedule": 300.0,
        },
        "recover-milestone-review-reminders": {
            "task": "app.tasks.milestones.process_review_reminders",
            "schedule": 300.0,
        }
    },
)
