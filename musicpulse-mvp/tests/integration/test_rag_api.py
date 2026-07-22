"""End-to-end RAG tests use SQLite and the local embedding fallback."""

from datetime import datetime, timezone
from app.models.music import Artist, PlatformVideo
from app.services.knowledge import KnowledgeService
from app.services.normalization import normalize_text


def seed_knowledge(db):
    artist = Artist(name="RAG Artist", normalized_name="rag artist", youtube_channel_id="rag-channel")
    db.add(artist)
    db.flush()
    video = PlatformVideo(
        artist_id=artist.id,
        platform="youtube",
        external_id="rag-video",
        title="Rising Nairobi Sound",
        normalized_title=normalize_text("Rising Nairobi Sound"),
        description="An energetic Kenyan urban music release with rapid audience growth.",
        published_at=datetime.now(timezone.utc),
        url="https://youtube.com/watch?v=rag-video",
        latest_view_count=5000,
        latest_like_count=700,
        latest_comment_count=80,
    )
    db.add(video)
    db.commit()
    KnowledgeService(db).sync_videos()


def test_knowledge_sync_and_grounded_assistant_fallback(client, db):
    seed_knowledge(db)
    documents = client.get("/api/v1/knowledge/documents")
    assert documents.status_code == 200
    assert len(documents.json()) == 1

    answer = client.post(
        "/api/v1/assistant/ask",
        json={"question": "How is Rising Nairobi Sound performing?"},
    )
    assert answer.status_code == 200
    payload = answer.json()
    assert payload["conversation_id"] > 0
    assert payload["provider"] == "deterministic-rag"
    assert payload["fallback_used"] is True
    assert payload["sources"][0]["title"].startswith("Rising Nairobi Sound")


def test_conversation_follow_up_is_persisted(client, db):
    seed_knowledge(db)
    first = client.post(
        "/api/v1/assistant/ask", json={"question": "Show the latest songs"}
    ).json()
    second = client.post(
        "/api/v1/assistant/ask",
        json={"question": "How is Rising Nairobi Sound performing?", "conversation_id": first["conversation_id"]},
    )
    assert second.status_code == 200
    conversation = client.get(f"/api/v1/assistant/conversations/{first['conversation_id']}")
    assert conversation.status_code == 200
    assert len(conversation.json()["messages"]) == 4
