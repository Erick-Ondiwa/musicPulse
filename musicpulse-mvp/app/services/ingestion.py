from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.youtube import YouTubeClient
from app.models.music import Artist, MetricSnapshot, PlatformVideo
from app.services.normalization import normalize_text
from app.services.knowledge import KnowledgeService


class IngestionService:
    def __init__(self, db: Session, youtube: YouTubeClient | None = None):
        self.db = db
        self.youtube = youtube or YouTubeClient()

    def ingest_popular(self, region_code: str, max_results: int) -> dict:
        videos = self.youtube.most_popular_music(region_code, max_results)
        return self._upsert_many(videos)

    def ingest_recent(self, region_code: str, hours: int, max_results: int) -> dict:
        videos = self.youtube.recent_music(region_code, hours, max_results)
        return self._upsert_many(videos)

    def refresh_statistics(self) -> dict:
        ids = self.db.scalars(
            select(PlatformVideo.external_id).where(PlatformVideo.platform == "youtube")
        ).all()
        if not ids:
            return {"requested": 0, "updated": 0, "snapshots_created": 0}
        videos = self.youtube.video_details(list(ids))
        result = self._upsert_many(videos, create_snapshot=True)
        result["requested"] = len(ids)
        return result

    def _upsert_many(self, videos: list[dict], create_snapshot: bool = True) -> dict:
        inserted = 0
        updated = 0
        snapshots = 0
        now = datetime.now(timezone.utc)

        for payload in videos:
            artist = self._get_or_create_artist(payload["channel_title"], payload.get("channel_id"))
            video = self.db.scalar(
                select(PlatformVideo).where(
                    PlatformVideo.platform == "youtube",
                    PlatformVideo.external_id == payload["external_id"],
                )
            )
            if video is None:
                video = PlatformVideo(
                    artist_id=artist.id,
                    platform="youtube",
                    external_id=payload["external_id"],
                    title=payload["title"],
                    normalized_title=normalize_text(payload["title"]),
                    description=payload["description"],
                    published_at=payload["published_at"],
                    thumbnail_url=payload.get("thumbnail_url"),
                    url=payload["url"],
                    duration_seconds=payload.get("duration_seconds"),
                    region_code=payload.get("region_code"),
                    category_id=payload.get("category_id"),
                    latest_view_count=payload["view_count"],
                    latest_like_count=payload["like_count"],
                    latest_comment_count=payload["comment_count"],
                    last_synced_at=now,
                )
                self.db.add(video)
                self.db.flush()
                inserted += 1
            else:
                video.artist_id = artist.id
                video.title = payload["title"]
                video.normalized_title = normalize_text(payload["title"])
                video.description = payload["description"]
                video.published_at = payload["published_at"]
                video.thumbnail_url = payload.get("thumbnail_url")
                video.duration_seconds = payload.get("duration_seconds")
                video.region_code = payload.get("region_code") or video.region_code
                video.category_id = payload.get("category_id") or video.category_id
                video.latest_view_count = payload["view_count"]
                video.latest_like_count = payload["like_count"]
                video.latest_comment_count = payload["comment_count"]
                video.last_synced_at = now
                updated += 1

            if create_snapshot and self._snapshot_changed(video, payload):
                self.db.add(
                    MetricSnapshot(
                        video_id=video.id,
                        recorded_at=now,
                        view_count=payload["view_count"],
                        like_count=payload["like_count"],
                        comment_count=payload["comment_count"],
                    )
                )
                snapshots += 1

        self.db.commit()

        # Keep the RAG knowledge base synchronized with the newest metadata.
        KnowledgeService(self.db).sync_videos()

        return {
            "received": len(videos),
            "inserted": inserted,
            "updated": updated,
            "snapshots_created": snapshots,
        }

    def _get_or_create_artist(self, name: str, channel_id: str | None) -> Artist:
        normalized = normalize_text(name) or "unknown artist"
        artist = None
        if channel_id:
            artist = self.db.scalar(select(Artist).where(Artist.youtube_channel_id == channel_id))
        if artist is None:
            artist = self.db.scalar(select(Artist).where(Artist.normalized_name == normalized))
        if artist is None:
            artist = Artist(name=name, normalized_name=normalized, youtube_channel_id=channel_id)
            self.db.add(artist)
            self.db.flush()
        elif channel_id and not artist.youtube_channel_id:
            artist.youtube_channel_id = channel_id
        return artist

    def _snapshot_changed(self, video: PlatformVideo, payload: dict) -> bool:
        last = self.db.scalar(
            select(MetricSnapshot)
            .where(MetricSnapshot.video_id == video.id)
            .order_by(MetricSnapshot.recorded_at.desc())
            .limit(1)
        )
        if last is None:
            return True
        return (
            last.view_count != payload["view_count"]
            or last.like_count != payload["like_count"]
            or last.comment_count != payload["comment_count"]
        )
