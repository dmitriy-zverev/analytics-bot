"""Database connection and session management.

This module provides SQLAlchemy async database configuration,
base model class, and session factory utilities.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All ORM models should inherit from this class to ensure
    proper metadata collection for migrations.
    """

    pass


def create_engine() -> AsyncEngine:
    """Create and configure async SQLAlchemy engine.

    Uses connection pooling with pre-ping to verify connections
    before use, preventing stale connection issues.

    Returns:
        AsyncEngine: Configured async database engine
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,  # Verify connections before use
        echo=False,  # Set to True for SQL query logging
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create async session factory bound to the given engine.

    Sessions are configured to not expire on commit, which is
    important for async operations where objects may be accessed
    after the transaction completes.

    Args:
        engine: Async SQLAlchemy engine to bind sessions to

    Returns:
        async_sessionmaker: Factory for creating async sessions
    """
    return async_sessionmaker(
        engine,
        expire_on_commit=False,  # Keep objects usable after commit
        class_=AsyncSession,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency injection provider for database sessions.

    Yields an async session that is automatically closed when done.
    Intended for use with FastAPI-style dependency injection or
    as a context manager in async functions.

    Yields:
        AsyncSession: Database session for queries and transactions

    Example:
        async with get_session() as session:
            result = await session.execute(query)
    """
    engine = create_engine()
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        yield session
