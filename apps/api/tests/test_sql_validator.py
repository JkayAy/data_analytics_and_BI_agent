import pytest

from insightbridge.sql_validator import SqlValidationError, ensure_limit, validate_sql


def test_rejects_delete():
    with pytest.raises(SqlValidationError) as exc:
        validate_sql("DELETE FROM analytics.customers", allowed_schemas={"analytics"})
    assert exc.value.code == "not_select"


def test_rejects_multi_statement():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT 1; SELECT 2", allowed_schemas={"analytics"})


def test_accepts_select():
    sql = validate_sql(
        "SELECT COUNT(*) FROM analytics.customers",
        allowed_schemas={"analytics"},
    )
    assert "SELECT" in sql.upper()


def test_injects_limit():
    out = ensure_limit("SELECT 1", 100)
    assert "LIMIT 100" in out.upper()


def test_preserves_existing_limit():
    out = ensure_limit("SELECT 1 LIMIT 5", 100)
    assert out.upper().count("LIMIT") == 1
