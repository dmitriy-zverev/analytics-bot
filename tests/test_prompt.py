"""Tests for LLM prompt templates.

Validates that prompts contain required schema information
and enforce proper SQL generation rules.
"""

from app.prompt import SCHEMA_DESCRIPTION, build_prompt


def test_schema_contains_tables():
    """Ensure schema describes both tables."""
    assert "videos" in SCHEMA_DESCRIPTION
    assert "video_snapshots" in SCHEMA_DESCRIPTION


def test_schema_contains_key_fields():
    """Ensure schema lists important fields."""
    assert "id" in SCHEMA_DESCRIPTION
    assert "creator_id" in SCHEMA_DESCRIPTION
    assert "views_count" in SCHEMA_DESCRIPTION
    assert "delta_views_count" in SCHEMA_DESCRIPTION


def test_schema_contains_rules():
    """Ensure schema has generation rules."""
    assert "SELECT" in SCHEMA_DESCRIPTION
    assert "COUNT" in SCHEMA_DESCRIPTION
    assert "SUM" in SCHEMA_DESCRIPTION
    assert "aggregate" in SCHEMA_DESCRIPTION.lower()


def test_build_prompt_includes_question():
    """Ensure user question is included in prompt."""
    question = "How many videos?"
    prompt = build_prompt(question)
    assert question in prompt


def test_build_prompt_includes_schema():
    """Ensure schema is included in prompt."""
    question = "Test question"
    prompt = build_prompt(question)
    assert "videos" in prompt
    assert "video_snapshots" in prompt


def test_prompt_requires_aggregate():
    """Ensure prompt requires aggregate functions."""
    assert "COUNT(*)" in SCHEMA_DESCRIPTION
    assert "SUM(" in SCHEMA_DESCRIPTION
    assert "AVG(" in SCHEMA_DESCRIPTION
    assert "MIN(" in SCHEMA_DESCRIPTION
    assert "MAX(" in SCHEMA_DESCRIPTION


def test_prompt_forbids_non_select():
    """Ensure prompt restricts to SELECT only."""
    schema_lower = SCHEMA_DESCRIPTION.lower()
    assert "select" in schema_lower
    # Should not encourage destructive operations
    assert "insert" not in schema_lower
    assert "delete" not in schema_lower
    assert "drop" not in schema_lower


def test_prompt_has_examples():
    """Ensure prompt includes examples."""
    assert "Q:" in SCHEMA_DESCRIPTION
    assert "A:" in SCHEMA_DESCRIPTION
    assert "SELECT COUNT(*) FROM videos" in SCHEMA_DESCRIPTION
