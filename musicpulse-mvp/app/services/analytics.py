from datetime import datetime, timedelta, timezone
import math
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.music import Artist, MetricSnapshot, PlatformVideo


def _song_dict(video: PlatformVideo, **extra) -> dict:
    return {
        "video_id": video.id,
        "title": video.title,
        "artist": video.artist.name,
        "youtube_id": video.external_id,
        "url": video.url,
        "thumbnail_url": video.thumbnail_url,
        "published_at": video.published_at,
        "views": video.latest_view_count,
        "likes": video.latest_like_count,
        "comments": video.latest_comment_count,
        **extra,
    }


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def latest(self, limit: int = 10, hours: int | None = None) -> list[dict]:
        query = select(PlatformVideo).order_by(desc(PlatformVideo.published_at)).limit(limit)
        if hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = (
                select(PlatformVideo)
                .where(PlatformVideo.published_at >= cutoff)
                .order_by(desc(PlatformVideo.published_at))
                .limit(limit)
            )
        return [_song_dict(video) for video in self.db.scalars(query).all()]

    def most_viewed(self, limit: int = 10, published_within_hours: int | None = None) -> list[dict]:
        query = select(PlatformVideo)
        if published_within_hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=published_within_hours)
            query = query.where(PlatformVideo.published_at >= cutoff)
        query = query.order_by(desc(PlatformVideo.latest_view_count)).limit(limit)
        return [_song_dict(video) for video in self.db.scalars(query).all()]

    def top_artists(self, limit: int = 10) -> list[dict]:
        rows = self.db.execute(
            select(
                Artist.id,
                Artist.name,
                func.count(PlatformVideo.id),
                func.coalesce(func.sum(PlatformVideo.latest_view_count), 0),
            )
            .join(PlatformVideo, PlatformVideo.artist_id == Artist.id)
            .group_by(Artist.id, Artist.name)
            .order_by(desc(func.sum(PlatformVideo.latest_view_count)))
            .limit(limit)
        ).all()
        return [
            {
                "artist_id": artist_id,
                "artist": name,
                "video_count": video_count,
                "total_views": int(total_views),
            }
            for artist_id, name, video_count, total_views in rows
        ]

    def trending(self, limit: int = 10, lookback_hours: int = 24) -> list[dict]:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=lookback_hours)
        videos = self.db.scalars(select(PlatformVideo)).all()
        ranked: list[dict] = []

        for video in videos:
            newest = self.db.scalar(
                select(MetricSnapshot)
                .where(MetricSnapshot.video_id == video.id)
                .order_by(MetricSnapshot.recorded_at.desc())
                .limit(1)
            )
            oldest = self.db.scalar(
                select(MetricSnapshot)
                .where(
                    MetricSnapshot.video_id == video.id,
                    MetricSnapshot.recorded_at >= cutoff,
                )
                .order_by(MetricSnapshot.recorded_at.asc())
                .limit(1)
            )
            if newest is None or oldest is None or newest.id == oldest.id:
                continue

            elapsed_hours = max(
                (newest.recorded_at - oldest.recorded_at).total_seconds() / 3600,
                1 / 60,
            )
            view_growth = max(newest.view_count - oldest.view_count, 0)
            like_growth = max(newest.like_count - oldest.like_count, 0)
            comment_growth = max(newest.comment_count - oldest.comment_count, 0)
            view_velocity = view_growth / elapsed_hours
            engagement_velocity = (like_growth + 2 * comment_growth) / elapsed_hours
            published_at = video.published_at
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            age_hours = max((now - published_at).total_seconds() / 3600, 0)
            freshness = 1 / (1 + age_hours / 24)

            score = (
                math.log1p(view_velocity) * 0.65
                + math.log1p(engagement_velocity) * 0.20
                + freshness * 0.15
            )

            newest.trend_score = score
            ranked.append(
                _song_dict(
                    video,
                    view_growth=view_growth,
                    view_velocity_per_hour=round(view_velocity, 2),
                    trend_score=round(score, 4),
                )
            )

        self.db.commit()
        ranked.sort(key=lambda row: row["trend_score"], reverse=True)
        return ranked[:limit]

    def search_song(self, phrase: str, limit: int = 5) -> list[dict]:
        pattern = f"%{phrase.strip()}%"
        videos = self.db.scalars(
            select(PlatformVideo)
            .where(PlatformVideo.title.ilike(pattern))
            .order_by(desc(PlatformVideo.latest_view_count))
            .limit(limit)
        ).all()
        return [_song_dict(video) for video in videos]
