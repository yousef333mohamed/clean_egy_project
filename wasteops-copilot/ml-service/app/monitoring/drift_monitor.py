"""Multiple drift signals; none is treated as proof of failure."""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import ks_2samp


@dataclass(frozen=True)
class DriftSignal:
    feature: str
    psi: float | None
    ks_statistic: float | None
    missing_rate_difference: float
    drift_detected: bool


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy()
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy()
    if len(ref) < bins or len(cur) < bins:
        return 0.0
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    r = np.histogram(ref, bins=edges)[0] / len(ref)
    c = np.histogram(cur, bins=edges)[0] / len(cur)
    r = np.clip(r, 1e-6, None)
    c = np.clip(c, 1e-6, None)
    return float(np.sum((c - r) * np.log(c / r)))


def compare(reference: pd.DataFrame, current: pd.DataFrame) -> list[DriftSignal]:
    signals = []
    for feature in sorted(set(reference.columns) & set(current.columns)):
        missing = abs(float(reference[feature].isna().mean() - current[feature].isna().mean()))
        if pd.api.types.is_numeric_dtype(reference[feature]):
            ref = reference[feature].dropna()
            cur = current[feature].dropna()
            psi = population_stability_index(ref, cur)
            ks = float(ks_2samp(ref, cur).statistic) if len(ref) and len(cur) else None
            detected = psi >= 0.2 or (ks is not None and ks >= 0.2) or missing >= 0.1
            signals.append(DriftSignal(feature, psi, ks, missing, detected))
        else:
            categories = sorted(set(reference[feature].dropna().astype(str)) | set(current[feature].dropna().astype(str)))
            ref = np.array([(reference[feature].astype(str) == c).mean() for c in categories])
            cur = np.array([(current[feature].astype(str) == c).mean() for c in categories])
            js = float(jensenshannon(np.clip(ref, 1e-8, None), np.clip(cur, 1e-8, None))) if categories else 0.0
            signals.append(DriftSignal(feature, None, js, missing, js >= 0.2 or missing >= 0.1))
    return signals
