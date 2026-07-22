from datetime import datetime, timedelta, timezone

from app.models.music import Artist, MetricSnapshot, PlatformVideo
from app.services.normalization import normalize_text


def seed(db):
    now = datetime.now(timezone.utc)
    artist = Artist(name="Test Artist", normalized_name="test artist", youtube_channel_id="channel1")
    db.add(artist)
    db.flush()
    video = PlatformVideo(
        artist_id=artist.id,
        external_id="abc123",
        title="Test Song",
        normalized_title=normalize_text("Test Song"),
        published_at=now - timedelta(minutes=30),
        url="https://www.youtube.com/watch?v=abc123",
        latest_view_count=2000,
        latest_like_count=200,
        latest_comment_count=20,
        last_synced_at=now,
    )
    db.add(video)
    db.flush()
    db.add(MetricSnapshot(video_id=video.id, recorded_at=now - timedelta(hours=2), view_count=1000, like_count=100, comment_count=10))
    db.add(MetricSnapshot(video_id=video.id, recorded_at=now, view_count=2000, like_count=200, comment_count=20))
    db.commit()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_latest_and_assistant(client, db):
    seed(db)

    latest = client.get("/api/v1/songs/latest?limit=10")
    assert latest.status_code == 200
    assert latest.json()[0]["title"] == "Test Song"

    answer = client.post(
        "/api/v1/assistant/ask",
        json={"question": "Which songs were released in the last hour?"},
    )
    assert answer.status_code == 200
    payload = answer.json()
    assert payload["intent"] == "released_last_hour"
    assert payload["data"][0]["title"] == "Test Song"


def test_trending(client, db):
    seed(db)
    response = client.get("/api/v1/songs/trending?lookback_hours=24")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["view_growth"] == 1000
    assert payload[0]["trend_score"] > 0
