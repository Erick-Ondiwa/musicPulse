"""Import every SQLAlchemy model so table discovery works at application startup."""

from app.models.music import Artist, PlatformVideo, MetricSnapshot
from app.models.knowledge import KnowledgeDocument, Conversation, ChatMessage, AssistantRun

__all__ = [
    "Artist", "PlatformVideo", "MetricSnapshot", "KnowledgeDocument",
    "Conversation", "ChatMessage", "AssistantRun",
]
