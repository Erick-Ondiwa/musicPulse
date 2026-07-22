from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get("/top")
def top_artists(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return AnalyticsService(db).top_artists(limit)
