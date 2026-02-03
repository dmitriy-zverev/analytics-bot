from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, index=True)
    video_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    views_count: Mapped[int] = mapped_column(BigInteger, default=0)
    likes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    reports_count: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    snapshots: Mapped[list["VideoSnapshot"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    views_count: Mapped[int] = mapped_column(BigInteger, default=0)
    likes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    reports_count: Mapped[int] = mapped_column(BigInteger, default=0)

    delta_views_count: Mapped[int] = mapped_column(BigInteger, default=0)
    delta_likes_count: Mapped[int] = mapped_column(BigInteger, default=0)
    delta_comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    delta_reports_count: Mapped[int] = mapped_column(BigInteger, default=0)

    video: Mapped[Video] = relationship(back_populates="snapshots")


Index("ix_video_snapshots_video_id_created_at", VideoSnapshot.video_id, VideoSnapshot.created_at)
