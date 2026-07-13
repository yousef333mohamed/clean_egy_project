"""Small deterministic trace metric helpers."""

from collections.abc import Iterable


def latency_summary(values_ms: Iterable[float]) -> dict[str, float]:
    values = sorted(float(value) for value in values_ms)
    if not values:
        return {"count": 0, "mean_ms": 0, "p95_ms": 0, "max_ms": 0}
    p95_index = min(len(values) - 1, max(0, int(len(values) * 0.95) - 1))
    return {"count": len(values), "mean_ms": sum(values) / len(values), "p95_ms": values[p95_index], "max_ms": values[-1]}
