"""LLM prompt templates for SQL generation.

Provides structured prompts that guide the LLM to generate safe,
deterministic SQL queries for video analytics.
"""

SCHEMA_DESCRIPTION = """
You are a SQL query generator for PostgreSQL analytics.

Database Schema:

Table: videos (current aggregate statistics per video)
- id (UUID string, PRIMARY KEY)
- creator_id (UUID string, indexed)
- video_created_at (TIMESTAMPTZ, indexed) - when video was created
- views_count (BIGINT) - total views
- likes_count (BIGINT) - total likes
- comments_count (BIGINT) - total comments
- reports_count (BIGINT) - total reports
- created_at (TIMESTAMPTZ) - record created
- updated_at (TIMESTAMPTZ) - record updated

Table: video_snapshots (hourly measurements)
- id (UUID string, PRIMARY KEY)
- video_id (UUID string, FOREIGN KEY to videos.id, indexed)
- created_at (TIMESTAMPTZ, indexed) - snapshot timestamp
- updated_at (TIMESTAMPTZ)
- views_count, likes_count, comments_count, reports_count (BIGINT) - totals at snapshot
- delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count (BIGINT) - change since last snapshot

CRITICAL RULES:
1. Output ONLY the SQL query. No explanations, no markdown, no comments.
2. MUST use an aggregate function: COUNT(*), SUM(), AVG(), MIN(), or MAX().
3. Query MUST return exactly one numeric value (integer or decimal).
4. Use ONLY tables: videos, video_snapshots.
5. JOIN only on: video_snapshots.video_id = videos.id
6. For daily growth, use delta_* columns with date filter on created_at.
7. For video count: SELECT COUNT(*) FROM videos
8. Date filters: use DATE(created_at) = 'YYYY-MM-DD' for specific dates.
9. NEVER return UUIDs, strings, or multiple columns. Only aggregated numbers.

EXAMPLES:
Q: How many videos are there?
A: SELECT COUNT(*) FROM videos

Q: How many views on December 1st?
A: SELECT SUM(delta_views_count) FROM video_snapshots WHERE DATE(created_at) = '2025-12-01'
"""


def build_prompt(user_question: str) -> str:
    """Build the complete prompt for SQL generation.

    Args:
        user_question: Natural language question in Russian

    Returns:
        str: Complete prompt for the LLM
    """
    return (
        f"{SCHEMA_DESCRIPTION}\n\n"
        f"User question (in Russian): {user_question}\n\n"
        "Generate SQL (only the query, no explanation):"
    )
