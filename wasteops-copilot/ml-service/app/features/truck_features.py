from datetime import datetime
import numpy as np
import pandas as pd
from app.features.feature_validation import enforce_point_in_time


def build_truck_features(trips: pd.DataFrame, as_of: datetime) -> pd.DataFrame:
    prior = enforce_point_in_time(trips, "trip_end_timestamp", as_of).copy()
    fuel = pd.to_numeric(prior["fuel_consumed_l"], errors="coerce")
    distance = pd.to_numeric(prior["distance_km"], errors="coerce")
    prior["fuel_efficiency_km_per_l"] = np.where(fuel > 0, distance / fuel, np.nan)
    return prior
