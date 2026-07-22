from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.connectors.youtube import YouTubeAPIError
from app.core.config import get_settings
from app.core.database import get_db
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/popular")
def ingest_popular(
    region_code: str = Query(default="KE", min_length=2, max_length=2),
    max_results: int = Query(default=25, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        return IngestionService(db).ingest_popular(region_code.upper(), max_results)
    except YouTubeAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/recent")
def ingest_recent(
    region_code: str = Query(default="KE", min_length=2, max_length=2),
    hours: int = Query(default=24, ge=1, le=168),
    max_results: int = Query(default=25, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        return IngestionService(db).ingest_recent(region_code.upper(), hours, max_results)
    except YouTubeAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/refresh-statistics")
def refresh_statistics(db: Session = Depends(get_db)):
    try:
        return IngestionService(db).refresh_statistics()
    except YouTubeAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
