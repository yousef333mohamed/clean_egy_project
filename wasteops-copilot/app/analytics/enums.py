"""Stable analytics vocabulary shared by routing, tools, and APIs."""

from enum import StrEnum


class AnalyticsDomain(StrEnum):
    BINS = "BINS"
    OPERATIONS = "OPERATIONS"
    TRUCKS = "TRUCKS"
    WORKFORCE = "WORKFORCE"
    ENVIRONMENT = "ENVIRONMENT"
    OVERVIEW = "OVERVIEW"


class AnalyticsIntent(StrEnum):
    COUNT = "COUNT"
    SUMMARY = "SUMMARY"
    RANKING = "RANKING"
    TREND = "TREND"
    COMPARISON = "COMPARISON"
    ANOMALY_RULE = "ANOMALY_RULE"
    DETAIL_LOOKUP = "DETAIL_LOOKUP"
    AVAILABILITY = "AVAILABILITY"
    PERFORMANCE = "PERFORMANCE"


class AggregationType(StrEnum):
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MAXIMUM = "maximum"
    DISTRIBUTION = "distribution"
    RATIO = "ratio"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class EvidenceSourceType(StrEnum):
    DATABASE = "database"
    DOCUMENT = "document"


class AnalyticsRoute(StrEnum):
    STRUCTURED_DATA = "STRUCTURED_DATA"
    DOCUMENT_KNOWLEDGE = "DOCUMENT_KNOWLEDGE"
    HYBRID_ANALYSIS = "HYBRID_ANALYSIS"
    UNSUPPORTED = "UNSUPPORTED"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"
