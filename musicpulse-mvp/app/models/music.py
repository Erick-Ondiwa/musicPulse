from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    youtube_channel_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    videos: Mapped[list["PlatformVideo"]] = relationship(back_populates="artist")


class PlatformVideo(Base):
    __tablename__ = "platform_videos"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_platform_external_video"),
        Index("ix_video_published_at", "published_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="youtube")
    external_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    normalized_title: Mapped[str] = mapped_column(String(500), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    url: Mapped[str] = mapped_column(String(1000))
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    category_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    latest_view_count: Mapped[int] = mapped_column(BigInteger, default=0)
    latest_like_count: Mapped[int] = mapped_column(BigInteger, default=0)
    latest_comment_count: Mapped[int] = mapped_column(BigInteger, default=0)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    artist: Mapped[Artist] = relationship(back_populates="videos")
    snapshots: Mapped[list["MetricSnapshot"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="MetricSnapshot.recorded_at",
    )


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        Index("ix_snapshot_video_recorded", "video_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("platform_videos.id", ondelete="CASCADE"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    view_count: Mapped[int] = mapped_column(BigInteger, default=0)
    like_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comment_count: Mapped[int] = mapped_column(BigInteger, default=0)
    trend_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    video: Mapped[PlatformVideo] = relationship(back_populates="snapshots")
