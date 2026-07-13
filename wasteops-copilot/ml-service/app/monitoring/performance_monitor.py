"""Outcome-backed metrics; refuses to manufacture accuracy without labels."""

import numpy as np
from sklearn.metrics import brier_score_loss, f1_score, mean_absolute_error, mean_squared_error, precision_score, recall_score


def classification_metrics(y_true, probability, threshold: float) -> dict[str, float]:
    if y_true is None or len(y_true) == 0:
        raise ValueError("Confirmed outcomes are required")
    predicted = np.asarray(probability) >= threshold
    return {
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, probability)),
    }


def regression_metrics(y_true, prediction) -> dict[str, float]:
    if y_true is None or len(y_true) == 0:
        raise ValueError("Confirmed outcomes are required")
    return {"mae": float(mean_absolute_error(y_true, prediction)), "rmse": float(mean_squared_error(y_true, prediction) ** 0.5)}
