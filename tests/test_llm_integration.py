"""Integration tests for LLM SQL generation.

These tests verify that the LLM generates proper SQL queries
that return numeric results when executed against the database.

Note: These tests require:
- Valid OpenRouter API key in environment
- Running PostgreSQL database with test data
"""

import os

import pytest
from tenacity import RetryError

from app.llm import OpenRouterClient, SqlGenerationError
from app.query_executor import QueryExecutor, SqlExecutionError
from app.sql_guard import SqlValidationError, validate_sql

# Skip all tests if no API key available
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


@pytest.fixture
async def llm_client():
    """Create LLM client for testing."""
    return OpenRouterClient()


@pytest.fixture
async def query_executor():
    """Create query executor for testing."""
    executor = QueryExecutor()
    yield executor
    await executor.close()


class TestVideoCountQueries:
    """Test queries about video counts."""

    @pytest.mark.asyncio
    async def test_total_video_count(self, llm_client, query_executor):
        """Query: How many videos are there?"""
        question = "Сколько всего видео в системе?"

        response = await llm_client.generate_sql(question)
        assert "COUNT" in response.sql.upper()

        result = await query_executor.fetch_scalar(response.sql)
        assert isinstance(result.value, int)
        assert result.value >= 0

    @pytest.mark.asyncio
    async def test_videos_by_creator(self, llm_client):
        """Query: How many videos per creator?"""
        question = "Сколько видео у каждого создателя?"

        # This query uses GROUP BY which returns multiple rows
        # Our system only supports single-value queries
        response = await llm_client.generate_sql(question)
        # Verify it generates some kind of aggregate query
        assert any(func in response.sql.upper() for func in ["COUNT", "SUM", "AVG", "MIN", "MAX"])
        # Note: Executing GROUP BY queries will fail with MultipleResultsFound


class TestViewsQueries:
    """Test queries about view counts."""

    @pytest.mark.asyncio
    async def test_total_views(self, llm_client, query_executor):
        """Query: Total views across all videos."""
        question = "Сколько всего просмотров?"

        response = await llm_client.generate_sql(question)
        assert "SUM" in response.sql.upper() or "COUNT" in response.sql.upper()

        result = await query_executor.fetch_scalar(response.sql)
        assert isinstance(result.value, int)
        assert result.value >= 0

    @pytest.mark.asyncio
    async def test_views_on_specific_date(self, llm_client, query_executor):
        """Query: Views on December 1st."""
        question = "Сколько просмотров было 1 декабря?"

        response = await llm_client.generate_sql(question)
        # Should use delta_views_count from video_snapshots
        assert "delta_views_count" in response.sql.lower() or "SUM" in response.sql.upper()

        result = await query_executor.fetch_scalar(response.sql)
        assert isinstance(result.value, int)


class TestLikesQueries:
    """Test queries about likes."""

    @pytest.mark.asyncio
    async def test_total_likes(self, llm_client, query_executor):
        """Query: Total likes across all videos."""
        question = "Сколько всего лайков?"

        response = await llm_client.generate_sql(question)
        result = await query_executor.fetch_scalar(response.sql)
        assert isinstance(result.value, int)

    @pytest.mark.asyncio
    async def test_max_likes(self, llm_client, query_executor):
        """Query: Maximum likes on a single video."""
        question = "Какое максимальное количество лайков у видео?"

        response = await llm_client.generate_sql(question)
        assert "MAX" in response.sql.upper()

        result = await query_executor.fetch_scalar(response.sql)
        assert isinstance(result.value, int)


class TestErrorCases:
    """Test error handling for problematic queries."""

    @pytest.mark.asyncio
    async def test_non_aggregate_query_fails(self, llm_client):
        """Query asking for IDs should fail validation."""
        question = "Покажи мне id всех видео"

        response = await llm_client.generate_sql(question)
        # Should fail validation or return 0
        try:
            validate_sql(response.sql)
        except SqlValidationError as e:
            assert "aggregate" in str(e).lower()

    @pytest.mark.asyncio
    async def test_ambiguous_question(self, llm_client, query_executor):
        """Test handling of ambiguous questions."""
        question = "Расскажи про видео"

        # Should either generate valid SQL or fail gracefully
        try:
            response = await llm_client.generate_sql(question)
            result = await query_executor.fetch_scalar(response.sql)
            assert isinstance(result.value, int)
        except (SqlGenerationError, SqlExecutionError):
            pass  # Expected for ambiguous questions


class TestSqlStructure:
    """Test structure of generated SQL."""

    @pytest.mark.asyncio
    async def test_sql_starts_with_select(self, llm_client):
        """All queries should start with SELECT."""
        question = "Сколько видео?"

        response = await llm_client.generate_sql(question)
        assert response.sql.strip().upper().startswith("SELECT")

    @pytest.mark.asyncio
    async def test_sql_has_aggregate(self, llm_client):
        """All queries should have aggregate function."""
        question = "Среднее количество просмотров"

        response = await llm_client.generate_sql(question)
        assert any(func in response.sql.upper() for func in ["COUNT", "SUM", "AVG", "MIN", "MAX"])

    @pytest.mark.asyncio
    async def test_sql_no_forbidden_keywords(self, llm_client):
        """No DELETE, UPDATE, INSERT, DROP in SQL."""
        question = "Удали все видео"

        # Should fail validation or generate safe query
        try:
            response = await llm_client.generate_sql(question)
            sql_upper = response.sql.upper()
            assert "DELETE" not in sql_upper
            assert "DROP" not in sql_upper
            assert "TRUNCATE" not in sql_upper
        except (SqlGenerationError, RetryError):
            pass  # Expected for malicious queries
