from app.ingestion.csv_loader import MODEL_MAP
from app.utils.validators import normalize_column_name


def test_all_expected_datasets_have_models() -> None:
    assert len(MODEL_MAP) == 8


def test_column_normalization() -> None:
    assert normalize_column_name(" Fill Level (%) ") == "fill_level"
