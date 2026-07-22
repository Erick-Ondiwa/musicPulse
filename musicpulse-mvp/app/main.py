"""FastAPI application entry point, lifecycle, CORS, routes, and health checks."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import create_tables
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create tables and preload the local embedding model."""

    create_tables()

    if settings.bge_enabled:
        try:
            # Loading PyTorch and BGE is blocking work, so execute it in a
            # worker thread rather than blocking FastAPI's event loop.
            await asyncio.to_thread(EmbeddingService(settings).warm_up)
        except Exception:
            # Do not prevent the API from starting. EmbeddingService will use
            # its deterministic fallback if BGE cannot load.
            logger.exception(
                "BGE startup warm-up failed. "
                "The application will use fallback embeddings."
            )

    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description=(
        "RAG-powered music intelligence using YouTube analytics "
        "and grounded LLM answers."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "2.0.0",
        "llm_configured": settings.llm_available,
        "embedding_model": settings.bge_embedding_model,
        "embedding_enabled": settings.bge_enabled,
    }