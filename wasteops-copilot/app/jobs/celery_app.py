"""Celery worker configuration using Redis without sensitive payloads."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("wasteops", broker=settings.redis_url, backend=settings.redis_url, include=["app.jobs.tasks"])
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=86_400,
    task_acks_late=True,
    beat_schedule={"daily-retention-cleanup": {"task": "wasteops.retention_cleanup", "schedule": 86_400.0}},
)
