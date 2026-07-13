import pandas as pd
from app.models.workforce_forecast_model import WorkforceForecastModel


def train(frame: pd.DataFrame, target: pd.Series, version: str = "candidate"):
    return WorkforceForecastModel(version).fit(frame, target)
