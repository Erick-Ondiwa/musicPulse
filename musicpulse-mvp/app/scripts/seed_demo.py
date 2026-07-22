from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal, create_tables
from app.models.music import Artist, MetricSnapshot, PlatformVideo
from app.services.normalization import normalize_text
from app.services.knowledge import KnowledgeService


DEMO = [
    ("Sauti Sol", "Midnight Train", "demo001", 1200000, 25000, 2100, 32000),
    ("Bien", "Lifestyle", "demo002", 940000, 22000, 1800, 51000),
    ("Nikita Kering", "On Yah", "demo003", 710000, 18000, 1200, 44000),
    ("Bensoul", "Nairobi", "demo004", 650000, 14000, 900, 18000),
    ("Wakadinali", "Geri Inengi", "demo005", 2200000, 41000, 3900, 73000),
    ("Nyashinski", "Perfect Design", "demo006", 1800000, 36000, 2700, 64000),
    ("Femi One", "Properly", "demo007", 830000, 19000, 1500, 29000),
    ("Khaligraph Jones", "Invisible Currency", "demo008", 2700000, 55000, 5100, 82000),
    ("Savara", "Balance", "demo009", 580000, 12000, 730, 26000),
    ("Njerae", "Aki Sioni", "demo010", 430000, 11000, 650, 37000),
]


def main():
    create_tables()
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        for index, (artist_name, title, youtube_id, views, likes, comments, growth) in enumerate(DEMO):
            artist = Artist(
                name=artist_name,
                normalized_name=normalize_text(artist_name),
                youtube_channel_id=f"channel-{youtube_id}",
            )
            db.add(artist)
            db.flush()

            video = PlatformVideo(
                artist_id=artist.id,
                platform="youtube",
                external_id=youtube_id,
                title=title,
                normalized_title=normalize_text(title),
                description="Demo record",
                published_at=now - timedelta(hours=index * 8 + 1),
                thumbnail_url=None,
                url=f"https://www.youtube.com/watch?v={youtube_id}",
                duration_seconds=210,
                region_code="KE",
                category_id="10",
                latest_view_count=views,
                latest_like_count=likes,
                latest_comment_count=comments,
                last_synced_at=now,
            )
            db.add(video)
            db.flush()

            db.add(
                MetricSnapshot(
                    video_id=video.id,
                    recorded_at=now - timedelta(hours=6),
                    view_count=views - growth,
                    like_count=max(likes - growth // 40, 0),
                    comment_count=max(comments - growth // 400, 0),
                )
            )
            db.add(
                MetricSnapshot(
                    video_id=video.id,
                    recorded_at=now,
                    view_count=views,
                    like_count=likes,
                    comment_count=comments,
                )
            )

        db.commit()
        KnowledgeService(db).sync_videos()
        print(f"Inserted {len(DEMO)} demo songs with two metric snapshots each.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
