"""Knowledge-base indexing and semantic retrieval for the RAG pipeline."""

from __future__ import annotations

import json
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDocument
from app.models.music import PlatformVideo
from app.services.embeddings import EmbeddingService


class KnowledgeService:
    def __init__(self, db: Session, embeddings: EmbeddingService | None = None):
        self.db = db
        self.embeddings = embeddings or EmbeddingService()

    def sync_videos(self) -> dict:
        """Convert every stored music video into a searchable RAG document."""
        videos = self.db.scalars(select(PlatformVideo)).all()
        inserted = 0
        updated = 0
        for video in videos:
            created = self.index_video(video)
            inserted += int(created)
            updated += int(not created)
        self.db.commit()
        return {"processed": len(videos), "inserted": inserted, "updated": updated}

    def index_video(self, video: PlatformVideo) -> bool:
        """Upsert one video document and regenerate its embedding."""
        source_id = f"{video.platform}:{video.external_id}"
        document = self.db.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.source_type == "video",
                KnowledgeDocument.source_id == source_id,
            )
        )
        created = document is None
        if document is None:
            document = KnowledgeDocument(source_type="video", source_id=source_id)
            self.db.add(document)

        content = self._video_content(video)
        embedding = self.embeddings.embed(content)
        document.title = f"{video.title} — {video.artist.name}"
        document.content = content
        document.source_url = video.url
        document.metadata_json = json.dumps(
            {
                "video_id": video.id,
                "artist": video.artist.name,
                "platform": video.platform,
                "published_at": video.published_at.isoformat(),
                "views": video.latest_view_count,
                "likes": video.latest_like_count,
                "comments": video.latest_comment_count,
                "region_code": video.region_code,
            }
        )
        document.embedding_json = json.dumps(embedding)
        document.embedding_provider = self.embeddings.provider_name
        self.db.flush()
        return created

    def add_manual_document(
        self,
        title: str,
        content: str,
        source_url: str | None = None,
    ) -> KnowledgeDocument:
        """Add user-curated market notes, reports, or other textual evidence."""
        source_id = f"manual:{abs(hash((title, content)))}"
        existing = self.db.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.source_type == "manual",
                KnowledgeDocument.source_id == source_id,
            )
        )
        document = existing or KnowledgeDocument(
            source_type="manual",
            source_id=source_id,
        )
        if existing is None:
            self.db.add(document)
        document.title = title
        document.content = content
        document.source_url = source_url
        document.metadata_json = "{}"
        document.embedding_json = json.dumps(
            self.embeddings.embed(f"{title}\n{content}")
        )
        document.embedding_provider = self.embeddings.provider_name
        self.db.commit()
        self.db.refresh(document)
        return document

    def search(self, query: str, limit: int | None = None) -> list[dict]:
        """Return documents ranked by cosine similarity to the user's question."""
        query_vector = self.embeddings.embed(query)
        documents = self.db.scalars(select(KnowledgeDocument)).all()
        ranked: list[dict] = []
        for document in documents:
            try:
                vector = json.loads(document.embedding_json)
                score = self.embeddings.cosine_similarity(query_vector, vector)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            ranked.append(
                {
                    "document_id": document.id,
                    "title": document.title,
                    "content": document.content,
                    "source_type": document.source_type,
                    "source_url": document.source_url,
                    "score": round(score, 4),
                    "metadata": json.loads(document.metadata_json or "{}"),
                }
            )
        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[: (limit or self.embeddings.settings.rag_top_k)]

    def list_documents(self, limit: int = 100) -> list[KnowledgeDocument]:
        return self.db.scalars(
            select(KnowledgeDocument)
            .order_by(desc(KnowledgeDocument.updated_at))
            .limit(limit)
        ).all()

    @staticmethod
    def _video_content(video: PlatformVideo) -> str:
        return (
            f"Song title: {video.title}.\n"
            f"Artist or YouTube channel: {video.artist.name}.\n"
            f"Description: {video.description or 'No description available.'}\n"
            f"Platform: {video.platform}. Region: {video.region_code or 'unknown'}.\n"
            f"Published at: {video.published_at.isoformat()}.\n"
            f"Latest metrics: {video.latest_view_count} views, "
            f"{video.latest_like_count} likes, and "
            f"{video.latest_comment_count} comments."
        )
