from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "musicpulse",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "ingest-popular-music-every-30-minutes": {
            "task": "musicpulse.ingest_popular",
            "schedule": crontab(minute="*/30"),
        },
        "discover-recent-music-every-15-minutes": {
            "task": "musicpulse.ingest_recent",
            "schedule": crontab(minute="*/15"),
        },
        "refresh-video-statistics-every-10-minutes": {
            "task": "musicpulse.refresh_statistics",
            "schedule": crontab(minute="*/10"),
        },
    },
)
