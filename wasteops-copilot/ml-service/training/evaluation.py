"""Candidate-versus-baseline evaluation with subgroup visibility."""

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score


def classifier_metrics(target, probability, threshold: float) -> dict[str, float]:
    target = np.asarray(target)
    probability = np.asarray(probability)
    predicted = probability >= threshold
    return {
        "roc_auc": float(roc_auc_score(target, probability)) if len(np.unique(target)) > 1 else 0.0,
        "pr_auc": float(average_precision_score(target, probability)),
        "precision": float(precision_score(target, predicted, zero_division=0)),
        "recall": float(recall_score(target, predicted, zero_division=0)),
        "f1": float(f1_score(target, predicted, zero_division=0)),
        "brier_score": float(brier_score_loss(target, probability)),
        "false_negative_rate": float(((target == 1) & (~predicted)).sum() / max(1, (target == 1).sum())),
    }


def subgroup_metrics(
    frame: pd.DataFrame, target_column: str, probability_column: str, groups: list[str], threshold: float
) -> dict[str, dict[str, dict[str, float]]]:
    result = {}
    for group in groups:
        if group not in frame:
            continue
        result[group] = {
            str(value): classifier_metrics(part[target_column], part[probability_column], threshold) for value, part in frame.groupby(group) if len(part) >= 10
        }
    return result


def passes_baseline(candidate: dict[str, float], baseline: dict[str, float]) -> bool:
    return (
        candidate.get("pr_auc", 0) > baseline.get("pr_auc", 0)
        and candidate.get("recall", 0) >= baseline.get("recall", 0)
        and candidate.get("brier_score", 1) <= baseline.get("brier_score", 1)
    )
