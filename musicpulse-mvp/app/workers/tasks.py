from app.core.config import get_settings
from app.core.database import SessionLocal, create_tables
from app.services.ingestion import IngestionService
from app.workers.celery_app import celery

settings = get_settings()


def _run(method_name: str, *args):
    create_tables()
    db = SessionLocal()
    try:
        service = IngestionService(db)
        return getattr(service, method_name)(*args)
    finally:
        db.close()


@celery.task(name="musicpulse.ingest_popular", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def ingest_popular():
    return _run("ingest_popular", settings.default_region, settings.popular_fetch_size)


@celery.task(name="musicpulse.ingest_recent", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def ingest_recent():
    return _run(
        "ingest_recent",
        settings.default_region,
        settings.recent_fetch_hours,
        settings.popular_fetch_size,
    )


@celery.task(name="musicpulse.refresh_statistics", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def refresh_statistics():
    return _run("refresh_statistics")
