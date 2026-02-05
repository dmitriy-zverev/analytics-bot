import pytest

from app.sql_guard import SqlValidationError, validate_sql


def test_valid_select_with_count():
    sql = "SELECT COUNT(*) FROM videos"
    result = validate_sql(sql)
    assert result == "SELECT COUNT(*) FROM videos"


def test_valid_select_with_sum():
    sql = "SELECT SUM(views_count) FROM videos"
    result = validate_sql(sql)
    assert result == "SELECT SUM(views_count) FROM videos"


def test_markdown_code_fence():
    sql = "```sql\nSELECT COUNT(*) FROM videos\n```"
    result = validate_sql(sql)
    assert result == "SELECT COUNT(*) FROM videos"


def test_markdown_without_sql_tag():
    sql = "```\nSELECT AVG(likes_count) FROM videos\n```"
    result = validate_sql(sql)
    assert result == "SELECT AVG(likes_count) FROM videos"


def test_sql_with_explanation():
    sql = "Here is the query:\nSELECT MAX(views_count) FROM videos"
    result = validate_sql(sql)
    assert result == "SELECT MAX(views_count) FROM videos"


def test_trailing_semicolon_removed():
    sql = "SELECT COUNT(*) FROM videos;"
    result = validate_sql(sql)
    assert result == "SELECT COUNT(*) FROM videos"


def test_reject_insert():
    sql = "INSERT INTO videos VALUES (1, 2, 3)"
    with pytest.raises(SqlValidationError, match="must start with SELECT"):
        validate_sql(sql)


def test_reject_update():
    sql = "UPDATE videos SET views_count = 0"
    with pytest.raises(SqlValidationError, match="must start with SELECT"):
        validate_sql(sql)


def test_reject_delete():
    sql = "DELETE FROM videos"
    with pytest.raises(SqlValidationError, match="must start with SELECT"):
        validate_sql(sql)


def test_reject_drop():
    sql = "DROP TABLE videos"
    with pytest.raises(SqlValidationError, match="must start with SELECT"):
        validate_sql(sql)


def test_reject_non_select():
    sql = "SHOW TABLES"
    with pytest.raises(SqlValidationError, match="must start with SELECT"):
        validate_sql(sql)


def test_reject_no_aggregate():
    sql = "SELECT id FROM videos"
    with pytest.raises(SqlValidationError, match="must use an aggregate function"):
        validate_sql(sql)


def test_case_insensitive_aggregate():
    sql = "select count(*) from videos"
    result = validate_sql(sql)
    assert "count(*)" in result.lower()


def test_min_aggregate():
    sql = "SELECT MIN(created_at) FROM videos"
    result = validate_sql(sql)
    assert result == "SELECT MIN(created_at) FROM videos"
