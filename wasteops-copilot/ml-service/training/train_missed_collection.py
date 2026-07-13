import pandas as pd
from app.models.missed_collection_model import MissedCollectionModel


def train(frame: pd.DataFrame, target: pd.Series, version: str = "candidate"):
    return MissedCollectionModel(version).fit(frame, target)
