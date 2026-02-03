import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Video, VideoSnapshot

DATA_PATH = Path("data/videos.json")
BATCH_SIZE = 1000


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        raise ValueError("Expected datetime string, got empty value")
    # Accept ISO-8601 and "YYYY-MM-DD HH:MM:SS" formats
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _video_payload(video: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": video["id"],
        "creator_id": video["creator_id"],
        "video_created_at": _parse_datetime(video["video_created_at"]),
        "views_count": video.get("views_count", 0),
        "likes_count": video.get("likes_count", 0),
        "comments_count": video.get("comments_count", 0),
        "reports_count": video.get("reports_count", 0),
        "created_at": _parse_datetime(video["created_at"]),
        "updated_at": _parse_datetime(video["updated_at"]),
    }


def _snapshot_payload(video_id: int, snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": snapshot["id"],
        "video_id": video_id,
        "created_at": _parse_datetime(snapshot["created_at"]),
        "updated_at": _parse_datetime(snapshot["updated_at"]),
        "views_count": snapshot.get("views_count", 0),
        "likes_count": snapshot.get("likes_count", 0),
        "comments_count": snapshot.get("comments_count", 0),
        "reports_count": snapshot.get("reports_count", 0),
        "delta_views_count": snapshot.get("delta_views_count", 0),
        "delta_likes_count": snapshot.get("delta_likes_count", 0),
        "delta_comments_count": snapshot.get("delta_comments_count", 0),
        "delta_reports_count": snapshot.get("delta_reports_count", 0),
    }


async def _insert_batches(session_factory: async_sessionmaker) -> None:
    payload = json.loads(DATA_PATH.read_text())
    videos: list[dict[str, Any]] = payload.get("videos", [])

    video_rows = [_video_payload(video) for video in videos]
    snapshot_rows: list[dict[str, Any]] = []
    for video in videos:
        video_id = video["id"]
        for snapshot in video.get("snapshots", []):
            snapshot_rows.append(_snapshot_payload(video_id, snapshot))

    async with session_factory() as session:
        for batch in _chunked(video_rows, BATCH_SIZE):
            await session.execute(insert(Video), batch)
        for batch in _chunked(snapshot_rows, BATCH_SIZE):
            await session.execute(insert(VideoSnapshot), batch)
        await session.commit()


async def main() -> None:
    settings = get_settings()
    engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        await _insert_batches(session_factory)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
