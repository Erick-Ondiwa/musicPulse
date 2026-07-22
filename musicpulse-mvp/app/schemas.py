"""Pydantic request and response contracts for the public API."""

from datetime import datetime
from pydantic import BaseModel, Field


class SongResult(BaseModel):
    video_id: int
    title: str
    artist: str
    youtube_id: str
    url: str
    thumbnail_url: str | None
    published_at: datetime
    views: int
    likes: int
    comments: int
    view_growth: int | None = None
    view_velocity_per_hour: float | None = None
    trend_score: float | None = None


class ArtistResult(BaseModel):
    artist_id: int
    artist: str
    video_count: int
    total_views: int


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    conversation_id: int | None = None


class RetrievedSource(BaseModel):
    document_id: int
    title: str
    content: str
    source_type: str
    source_url: str | None = None
    score: float
    metadata: dict = Field(default_factory=dict)


class AskResponse(BaseModel):
    question: str
    intent: str
    answer: str
    data: list[dict]
    metric_definition: str
    conversation_id: int
    sources: list[RetrievedSource]
    provider: str
    model_name: str | None = None
    fallback_used: bool
    generated_at: datetime


class ManualKnowledgeRequest(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    content: str = Field(min_length=10, max_length=100000)
    source_url: str | None = None
