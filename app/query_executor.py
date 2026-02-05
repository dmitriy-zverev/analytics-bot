from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.config import get_settings


class SqlExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class QueryResult:
    value: int


class QueryExecutor:
    def __init__(self) -> None:
        settings = get_settings()
        self._engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def close(self) -> None:
        await self._engine.dispose()

    async def fetch_scalar(self, sql: str) -> QueryResult:
        settings = get_settings()
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    text(sql).execution_options(timeout=settings.db_timeout)
                )
                value = result.scalar_one_or_none()
                if value is None:
                    return QueryResult(value=0)
                if isinstance(value, bool):
                    raise SqlExecutionError("SQL returned boolean, expected numeric")
                if isinstance(value, (int, float)):
                    return QueryResult(value=int(value))
                raise SqlExecutionError("SQL returned non-numeric result")
        except Exception as exc:  # noqa: BLE001 - wrap with custom error
            raise SqlExecutionError(f"SQL execution failed: {exc}") from exc
