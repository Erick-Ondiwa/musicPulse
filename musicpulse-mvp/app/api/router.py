"""Central API router that assembles every feature-specific route module."""

from fastapi import APIRouter
from app.api.routes import artists, assistant, ingestion, knowledge, songs

api_router = APIRouter()
api_router.include_router(ingestion.router)
api_router.include_router(songs.router)
api_router.include_router(artists.router)
api_router.include_router(assistant.router)
api_router.include_router(knowledge.router)
