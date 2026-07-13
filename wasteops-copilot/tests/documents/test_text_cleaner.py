"""Conservative cleaning and language detection tests."""

from app.ingestion.text_cleaner import clean_text, detect_language


def test_cleaning_preserves_structure_identifiers_and_arabic() -> None:
    source = "#  Safety\r\n\r\n\r\n-  Check  BIN-01\x00\r\n- افحص TRK-02"
    cleaned = clean_text(source)
    assert "# Safety" in cleaned
    assert "- Check BIN-01" in cleaned
    assert "افحص TRK-02" in cleaned
    assert "\n\n\n" not in cleaned


def test_transparent_language_detection() -> None:
    assert detect_language("Safety inspection procedure") == "en"
    assert detect_language("إجراء فحص السلامة") == "ar"
    assert detect_language("Safety إجراء السلامة") == "mixed"
    assert detect_language("1234") == "unknown"
