"""Shared ingestion constants."""

INGESTION_ORDER = (
    "smart_bins",
    "trucks",
    "workforce",
    "environmental_daily",
    "smart_bin_readings",
    "operational_daily",
    "truck_trip_logs",
    "workforce_attendance",
)

SUCCESSFUL_STATUSES = ("COMPLETED", "COMPLETED_WITH_ERRORS")
NULL_STRINGS = frozenset({"", "nan", "nat", "null", "none"})
