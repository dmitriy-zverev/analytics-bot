"""SQLAlchemy ORM models for video analytics.

Defines the database schema for storing video statistics and
time-series snapshot data for analytics queries.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Video(Base):
    """Represents a video with aggregate statistics.

    This table stores the latest known statistics for each video.
    For historical data and daily deltas, see VideoSnapshot.
    """

    __tablename__ = "videos"

    # Primary identifiers
    id: Mapped[str] = mapped_column(
        String(36),  # UUID format
        primary_key=True,
    )
    creator_id: Mapped[str] = mapped_column(
        String(36),
        index=True,
    )

    # Temporal fields
    video_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Engagement metrics (latest known values)
    views_count: Mapped[int] = mapped_column(BigInteger, default=0)
    likes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    reports_count: Mapped[int] = mapped_column(BigInteger, default=0)

    # Relationships
    snapshots: Mapped[list["VideoSnapshot"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )


class VideoSnapshot(Base):
    """Time-series snapshot of video metrics at a specific point in time.

    This table stores periodic measurements of video statistics,
    enabling analysis of growth trends and daily deltas.

    The delta_* fields represent the change since the previous snapshot,
    making it easy to calculate daily growth without joining multiple rows.
    """

    __tablename__ = "video_snapshots"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    # Foreign key relationship
    video_id: Mapped[str] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        index=True,
    )

    # Snapshot timestamp (indexed for time-range queries)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Absolute metrics at snapshot time
    views_count: Mapped[int] = mapped_column(BigInteger, default=0)
    likes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    reports_count: Mapped[int] = mapped_column(BigInteger, default=0)

    # Delta metrics (change since previous snapshot)
    # These enable efficient daily growth calculations
    delta_views_count: Mapped[int] = mapped_column(BigInteger, default=0)
    delta_likes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    delta_comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    delta_reports_count: Mapped[int] = mapped_column(BigInteger, default=0)

    # Relationships
    video: Mapped[Video] = relationship(back_populates="snapshots")


# Composite index for efficient video + time range queries
# Essential for "growth on specific day" type queries
Index(
    "ix_video_snapshots_video_id_created_at",
    VideoSnapshot.video_id,
    VideoSnapshot.created_at,
)
