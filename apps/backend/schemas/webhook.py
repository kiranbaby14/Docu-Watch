from pydantic import BaseModel
from enum import Enum
from typing import Dict, List, Optional


class WebhookSchema(BaseModel):
    url: str
    headers: Optional[Dict[str, str]] = None


class ProcessingStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    BATCH_PROGRESS = "batch_progress"
    BATCH_COMPLETED = "batch_completed"


class ProcessingType(str, Enum):
    INDIVIDUAL = "individual"
    BATCH = "batch"
    TERMINATE = "terminate"


class ProcessingPhase(str, Enum):
    DOWNLOAD = "download"
    PDF_TO_JSON = "pdf_to_json"
    JSON_TO_GRAPH = "json_to_graph"


class EnvelopeStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


# Individual envelope processing models
class DocumentProgress(BaseModel):
    current_document: str
    completed: int
    total: int
    percentage: float


class IndividualStartedMessage(BaseModel):
    type: ProcessingType = ProcessingType.INDIVIDUAL
    status: ProcessingStatus = ProcessingStatus.STARTED
    envelope_id: str
    total_documents: int
    phase: ProcessingPhase


class IndividualProgressMessage(BaseModel):
    type: ProcessingType = ProcessingType.INDIVIDUAL
    status: ProcessingStatus = ProcessingStatus.IN_PROGRESS
    envelope_id: str
    progress: DocumentProgress
    phase: ProcessingPhase


class IndividualCompletedMessage(BaseModel):
    type: ProcessingType = ProcessingType.INDIVIDUAL
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    envelope_id: str
    files: List[str]
    phase: ProcessingPhase


class IndividualErrorMessage(BaseModel):
    type: ProcessingType = ProcessingType.INDIVIDUAL
    status: ProcessingStatus = ProcessingStatus.ERROR
    envelope_id: str
    error: str
    phase: ProcessingPhase


# Batch processing models
class EnvelopeStatusInfo(BaseModel):
    total_documents: int
    completed_documents: int
    status: EnvelopeStatus


class OverallProgress(BaseModel):
    completed_envelopes: int
    total_envelopes: int
    completed_documents: int
    total_documents: int
    percentage: float


class CurrentEnvelopeProgress(BaseModel):
    id: str
    current_document: str
    completed: int
    total: int


class BatchProgressMessage(BaseModel):
    type: ProcessingType = ProcessingType.BATCH
    status: ProcessingStatus = ProcessingStatus.BATCH_PROGRESS
    overall_progress: OverallProgress
    current_envelope: Optional[CurrentEnvelopeProgress] = None
    envelope_statuses: Dict[str, EnvelopeStatusInfo]
    phase: ProcessingPhase


class BatchCompletedMessage(BaseModel):
    type: ProcessingType = ProcessingType.BATCH
    status: ProcessingStatus = ProcessingStatus.BATCH_COMPLETED
    overall_progress: OverallProgress
    envelope_statuses: Dict[str, EnvelopeStatusInfo]
    phase: ProcessingPhase


class TerminateMessage(BaseModel):
    type: ProcessingType = ProcessingType.TERMINATE
    terminate: bool = False  # True when this is the final message
