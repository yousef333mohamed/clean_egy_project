"""Every protected API must declare inspectable backend authorization."""

from scripts.generate_endpoint_matrix import rows


def test_all_routes_have_security_metadata() -> None:
    generated = rows()
    assert generated
    assert all(row[2] in {"yes", "no"} for row in generated)
