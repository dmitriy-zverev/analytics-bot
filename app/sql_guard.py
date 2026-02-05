import re


class SqlValidationError(ValueError):
    pass


_SELECT_ONLY_RE = re.compile(r"^\s*select\s", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create)\b", re.IGNORECASE)
_CODE_FENCE_RE = re.compile(r"```(?:sql)?(.*?)```", re.IGNORECASE | re.DOTALL)
_FIRST_SELECT_RE = re.compile(r"select\s+.*", re.IGNORECASE | re.DOTALL)
_AGGREGATE_RE = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.IGNORECASE)


def _extract_sql(raw: str) -> str:
    match = _CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    match = _FIRST_SELECT_RE.search(raw)
    if match:
        return match.group(0).strip()
    return raw.strip()


def validate_sql(sql: str) -> str:
    cleaned = _extract_sql(sql)
    if not _SELECT_ONLY_RE.search(cleaned):
        raise SqlValidationError("SQL must start with SELECT")
    if _FORBIDDEN_RE.search(cleaned):
        raise SqlValidationError("SQL contains forbidden keywords")
    if not _AGGREGATE_RE.search(cleaned):
        raise SqlValidationError("SQL must use an aggregate function")
    return cleaned.strip().rstrip(";")
