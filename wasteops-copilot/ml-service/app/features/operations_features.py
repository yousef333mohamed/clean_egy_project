from datetime import datetime
import pandas as pd
from app.features.feature_validation import enforce_point_in_time


def build_operations_features(rows: pd.DataFrame, as_of: datetime) -> pd.DataFrame:
    return enforce_point_in_time(rows, "available_at", as_of)
