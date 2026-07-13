"""Low-cardinality Prometheus application metrics."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter("wasteops_http_requests_total", "HTTP requests", ["method", "route", "status"])
HTTP_LATENCY = Histogram("wasteops_http_request_duration_seconds", "HTTP request latency", ["method", "route"])
AUTH_FAILURES = Counter("wasteops_authentication_failures_total", "Authentication failures")
AUTHZ_DENIALS = Counter("wasteops_authorization_denials_total", "Authorization denials")
RATE_LIMITS = Counter("wasteops_rate_limit_events_total", "Rate-limit responses")
JOB_EVENTS = Counter("wasteops_background_job_events_total", "Background jobs", ["job_type", "status"])


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
