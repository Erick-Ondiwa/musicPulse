from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/songs", tags=["songs"])


@router.get("/latest")
def latest(
    limit: int = Query(default=10, ge=1, le=50),
    hours: int | None = Query(default=None, ge=1, le=720),
    db: Session = Depends(get_db),
):
    return AnalyticsService(db).latest(limit=limit, hours=hours)


@router.get("/most-viewed")
def most_viewed(
    limit: int = Query(default=10, ge=1, le=50),
    published_within_hours: int | None = Query(default=None, ge=1, le=720),
    db: Session = Depends(get_db),
):
    return AnalyticsService(db).most_viewed(limit, published_within_hours)


@router.get("/trending")
def trending(
    limit: int = Query(default=10, ge=1, le=50),
    lookback_hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    return AnalyticsService(db).trending(limit, lookback_hours)
