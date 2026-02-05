#!/bin/sh
set -e

echo "Running migrations..."
uv run alembic upgrade head

echo "Checking if data is loaded..."
DATA_CHECK=$(uv run python -c "
import asyncio
from sqlalchemy import select, func
from app.db import create_engine, create_session_factory
from app.models import Video

async def check_data():
    engine = create_engine()
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        count = await session.scalar(select(func.count(Video.id)))
        return count or 0
    await engine.dispose()

print(asyncio.run(check_data()))
")

if [ "$DATA_CHECK" = "0" ]; then
    echo "No data found, loading from JSON..."
    uv run python scripts/load_data.py
    echo "Data loaded successfully"
else
    echo "Data already exists ($DATA_CHECK videos)"
fi

echo "Starting bot..."
exec uv run python app/main.py