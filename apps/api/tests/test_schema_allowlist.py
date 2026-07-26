import pytest

from insightbridge.sql_validator import SqlValidationError, validate_sql


def test_rejects_unqualified_public_table():
    with pytest.raises(SqlValidationError) as exc:
        validate_sql("SELECT * FROM customers", allowed_schemas={"analytics"})
    assert exc.value.code == "schema_denied"
