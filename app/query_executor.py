"""SQL query execution with safety checks.

Executes validated SQL queries and ensures results are numeric.
Handles PostgreSQL-specific return types like Decimal.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.config import get_settings


class SqlExecutionError(RuntimeError):
    """Raised when SQL execution fails or returns unexpected results."""

    pass


@dataclass(frozen=True)
class QueryResult:
    """Wrapper for query results to ensure type safety."""

    value: int


class QueryExecutor:
    """Execute SQL queries against PostgreSQL with safety checks."""

    def __init__(self) -> None:
        """Initialize with async engine and session factory."""
        settings = get_settings()
        self._engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def close(self) -> None:
        """Close database connections."""
        await self._engine.dispose()

    async def fetch_scalar(self, sql: str) -> QueryResult:
        """Execute SQL and return single numeric value.

        Args:
            sql: Validated SQL query to execute

        Returns:
            QueryResult: Wrapper containing numeric value

        Raises:
            SqlExecutionError: If execution fails or result is non-numeric
        """
        import structlog

        logger = structlog.get_logger()
        settings = get_settings()

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    text(sql).execution_options(timeout=settings.db_timeout)
                )
                value = result.scalar_one_or_none()

                # Debug logging to diagnose non-numeric results
                logger.debug(
                    "sql_executed",
                    sql=sql[:100],
                    result_type=type(value).__name__,
                    result_value=str(value)[:100] if value is not None else None,
                )

                if value is None:
                    return QueryResult(value=0)
                if isinstance(value, bool):
                    raise SqlExecutionError(
                        f"SQL returned boolean ({value}), expected numeric. Query: {sql[:100]}"
                    )
                # Handle int, float, and PostgreSQL Decimal types
                if isinstance(value, (int, float, Decimal)):
                    return QueryResult(value=int(value))
                raise SqlExecutionError(
                    f"SQL returned non-numeric result: {type(value).__name__} = {str(value)[:50]}. "
                    f"Query: {sql[:100]}"
                )
        except Exception as exc:
            if isinstance(exc, SqlExecutionError):
                raise
            raise SqlExecutionError(f"SQL execution failed: {exc}") from exc
