import pandas as pd
from app.models.truck_anomaly_model import TruckAnomalyModel


def train(frame: pd.DataFrame, version: str = "candidate"):
    return TruckAnomalyModel(version).fit(frame)
