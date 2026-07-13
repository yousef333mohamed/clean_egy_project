"""Metric registry formulas and null semantics."""

from decimal import Decimal

from app.analytics.metric_registry import METRIC_REGISTRY, attendance_rate_pct, fuel_efficiency_km_per_l, null_safe_average, truck_utilization_pct


def test_initial_registry_is_complete():
    assert len(METRIC_REGISTRY) == 43
    assert all(metric.expression_builder for metric in METRIC_REGISTRY.values())


def test_null_safe_average_reports_denominators():
    assert null_safe_average([10, None, 20]) == (Decimal("15"), 2, 1)
    assert null_safe_average([None]) == (None, 0, 1)


def test_utilization_is_uncapped_and_invalid_capacity_excluded():
    assert truck_utilization_pct(1200, 1000) == Decimal("120.0")
    assert truck_utilization_pct(1, 0) is None


def test_fuel_efficiency_requires_positive_fuel():
    assert fuel_efficiency_km_per_l(100, 20) == Decimal("5")
    assert fuel_efficiency_km_per_l(100, 0) is None


def test_attendance_rate_distinguishes_empty_data():
    assert attendance_rate_pct(3, 4) == Decimal("75.00")
    assert attendance_rate_pct(0, 0) is None
