"""Low-cardinality Prometheus application metrics."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter("wasteops_http_requests_total", "HTTP requests", ["method", "route", "status"])
HTTP_LATENCY = Histogram("wasteops_http_request_duration_seconds", "HTTP request latency", ["method", "route"])
AUTH_FAILURES = Counter("wasteops_authentication_failures_total", "Authentication failures")
AUTHZ_DENIALS = Counter("wasteops_authorization_denials_total", "Authorization denials")
RATE_LIMITS = Counter("wasteops_rate_limit_events_total", "Rate-limit responses")
JOB_EVENTS = Counter("wasteops_background_job_events_total", "Background jobs", ["job_type", "status"])
ML_PREDICTION_REQUESTS = Counter("wasteops_ml_prediction_requests_total", "ML provider requests", ["model"])
ML_PREDICTION_FAILURES = Counter("wasteops_ml_prediction_failures_total", "ML provider failures", ["model", "reason"])
ML_PREDICTION_LATENCY = Histogram("wasteops_ml_prediction_duration_seconds", "ML provider request duration", ["model"])
ML_MODEL_VERSION_USAGE = Counter("wasteops_ml_model_version_usage_total", "Approved model version usage", ["model", "version"])
ML_MODEL_UNAVAILABLE = Counter("wasteops_ml_model_unavailable_total", "ML model unavailable responses", ["model"])
ML_PREDICTION_WARNINGS = Counter("wasteops_ml_prediction_warnings_total", "Prediction warning categories", ["model", "category"])


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
