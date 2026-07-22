"""Knowledge-base administration endpoints used by the RAG pipeline."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import ManualKnowledgeRequest
from app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/sync-videos")
def sync_videos(db: Session = Depends(get_db)):
    return KnowledgeService(db).sync_videos()


@router.post("/documents")
def add_document(payload: ManualKnowledgeRequest, db: Session = Depends(get_db)):
    document = KnowledgeService(db).add_manual_document(
        payload.title, payload.content, payload.source_url
    )
    return {"id": document.id, "title": document.title, "source_type": document.source_type}


@router.get("/documents")
def list_documents(
    limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)
):
    documents = KnowledgeService(db).list_documents(limit)
    return [
        {
            "id": item.id,
            "title": item.title,
            "source_type": item.source_type,
            "source_url": item.source_url,
            "embedding_provider": item.embedding_provider,
            "updated_at": item.updated_at,
        }
        for item in documents
    ]
