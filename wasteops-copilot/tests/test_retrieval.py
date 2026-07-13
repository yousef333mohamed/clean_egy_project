import pytest
from app.core.security import validate_read_only_sql
from app.utils.exceptions import UnsafeQueryError


def test_select_gets_limit() -> None:
    assert validate_read_only_sql("SELECT * FROM trucks", 25).endswith("LIMIT 25")


def test_existing_large_limit_is_still_capped() -> None:
    result = validate_read_only_sql("SELECT * FROM trucks LIMIT 10000", 25)
    assert result.endswith("LIMIT 25")


@pytest.mark.parametrize(
    "query", ["DELETE FROM trucks", "SELECT * FROM trucks; DROP TABLE trucks", "WITH x AS (DELETE FROM trucks RETURNING *) SELECT * FROM x"]
)
def test_unsafe_sql_is_rejected(query: str) -> None:
    with pytest.raises(UnsafeQueryError):
        validate_read_only_sql(query)
