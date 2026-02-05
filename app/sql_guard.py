"""SQL validation and sanitization layer.

Provides multi-layer security for LLM-generated SQL queries:
1. Extraction: Parse SQL from markdown/text wrappers
2. Structure validation: Ensure SELECT-only, aggregate functions
3. Forbidden keyword detection: Block destructive operations

All validation failures raise SqlValidationError with descriptive messages.
"""

import re


class SqlValidationError(ValueError):
    """Raised when SQL fails validation checks.

    This exception indicates the generated SQL is unsafe or doesn't
    meet the requirements (e.g., not a SELECT, missing aggregate).
    """

    pass


# Validation patterns
_SELECT_ONLY_RE = re.compile(r"^\s*select\s", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke)\b",
    re.IGNORECASE,
)
_CODE_FENCE_RE = re.compile(r"```(?:sql)?(.*?)```", re.IGNORECASE | re.DOTALL)
_FIRST_SELECT_RE = re.compile(r"select\s+.*", re.IGNORECASE | re.DOTALL)
_AGGREGATE_RE = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.IGNORECASE)


def _extract_sql(raw: str) -> str:
    """Extract SQL query from markdown or text content.

    Handles common LLM output formats:
    - Markdown code fences (```sql ... ```)
    - Plain code blocks (``` ... ```)
    - Text with embedded SQL (extracts first SELECT)

    Args:
        raw: Raw text potentially containing SQL

    Returns:
        str: Extracted SQL query or cleaned text

    Example:
        >>> _extract_sql("```sql\nSELECT 1\n```")
        'SELECT 1'
    """
    # Try to extract from markdown code fence first
    match = _CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()

    # Fall back to finding first SELECT statement
    match = _FIRST_SELECT_RE.search(raw)
    if match:
        return match.group(0).strip()

    # Return cleaned raw text as last resort
    return raw.strip()


def validate_sql(sql: str) -> str:
    """Validate and sanitize SQL query from LLM.

    Performs multiple validation layers to ensure safety:
    1. Extracts SQL from markdown/text wrappers
    2. Verifies query starts with SELECT
    3. Checks for forbidden keywords (INSERT, UPDATE, etc.)
    4. Ensures aggregate function is present

    Args:
        sql: Raw SQL string from LLM

    Returns:
        str: Cleaned, validated SQL query (semicolon removed)

    Raises:
        SqlValidationError: If any validation check fails

    Example:
        >>> validate_sql("SELECT COUNT(*) FROM videos;")
        'SELECT COUNT(*) FROM videos'

        >>> validate_sql("DELETE FROM videos")  # Raises SqlValidationError
    """
    cleaned = _extract_sql(sql)

    # Layer 1: Must start with SELECT
    if not _SELECT_ONLY_RE.search(cleaned):
        raise SqlValidationError(f"SQL must start with SELECT. Query: {cleaned[:100]}...")

    # Layer 2: No destructive operations
    forbidden_match = _FORBIDDEN_RE.search(cleaned)
    if forbidden_match:
        raise SqlValidationError(f"SQL contains forbidden keyword: {forbidden_match.group(1)}")

    # Layer 3: Must aggregate (return single value)
    if not _AGGREGATE_RE.search(cleaned):
        raise SqlValidationError("SQL must use an aggregate function (COUNT, SUM, AVG, MIN, MAX)")

    # Clean trailing semicolon for consistency
    return cleaned.strip().rstrip(";")
