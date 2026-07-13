"""Database model registry used by application code and Alembic."""

from app.models.base import Base
from app.models.document_chunk import DocumentChunk
from app.models.environmental_daily import EnvironmentalDaily
from app.models.evaluation_result import EvaluationResult
from app.models.evaluation_run import EvaluationRun, EvaluationRunStatus
from app.models.ingestion_error import IngestionError
from app.models.ingestion_run import IngestionRun, IngestionStatus
from app.models.knowledge_document import DocumentStatus, KnowledgeDocument
from app.models.operational_daily import OperationalDaily
from app.models.interaction_trace import InteractionTrace
from app.models.prompt_version import PromptStatus, PromptVersion
from app.models.smart_bin import SmartBin
from app.models.smart_bin_reading import SmartBinReading
from app.models.truck import Truck
from app.models.truck_trip_log import TruckTripLog
from app.models.worker import Worker
from app.models.workforce_attendance import WorkforceAttendance
from app.models.user_feedback import FeedbackType, UserFeedback
from app.audit.models import AuditEvent

__all__ = [
    "Base",
    "DocumentChunk",
    "EnvironmentalDaily",
    "EvaluationResult",
    "EvaluationRun",
    "EvaluationRunStatus",
    "IngestionError",
    "IngestionRun",
    "IngestionStatus",
    "DocumentStatus",
    "KnowledgeDocument",
    "OperationalDaily",
    "InteractionTrace",
    "PromptStatus",
    "PromptVersion",
    "SmartBin",
    "SmartBinReading",
    "Truck",
    "TruckTripLog",
    "Worker",
    "WorkforceAttendance",
    "FeedbackType",
    "UserFeedback",
    "AuditEvent",
]
