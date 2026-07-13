"""Train an overflow candidate from an explicitly prepared feature dataset."""

import argparse
from pathlib import Path
import joblib
import pandas as pd
from app.models.overflow_model import OverflowModel
from training.splits import chronological_split
from training.evaluation import classifier_metrics


def train(path: Path, horizon: int, version: str = "candidate"):
    frame = pd.read_csv(path)
    split = chronological_split(frame, "prediction_timestamp")
    model = OverflowModel(version=version).fit(split.train, split.train["target"])
    probability = model.estimator.predict_proba(split.test)[:, 1]
    return model, classifier_metrics(split.test["target"], probability, model.decision_threshold)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--horizon", type=int, choices=[6, 12, 24], default=24)
    parser.add_argument("--output", type=Path, default=Path("artifacts/models/bin-overflow/candidate/model.joblib"))
    args = parser.parse_args()
    model, metrics = train(args.dataset, args.horizon)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)
    print(metrics)
