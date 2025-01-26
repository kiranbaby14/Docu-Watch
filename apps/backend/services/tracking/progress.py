# progress.py
from typing import List, Optional
from ..notification.webhook import WebhookService
from schemas.webhook import (
    IndividualStartedMessage,
    IndividualProgressMessage,
    IndividualCompletedMessage,
    IndividualErrorMessage,
    DocumentProgress,
    ProcessingStatus,
    ProcessingPhase,
    EnvelopeStatus,
)


class ProgressTracker:
    def __init__(
        self,
        webhook_service: Optional[WebhookService] = None,
        phase: ProcessingPhase = ProcessingPhase.DOWNLOAD,
    ):
        self.webhook_service = webhook_service
        self.envelopes = {}
        self.phase = phase

    async def start_envelope(self, envelope_id: str, total_documents: int):
        """Initialize tracking for an envelope"""
        self.envelopes[envelope_id] = {
            "total_documents": total_documents,
            "completed_documents": 0,
            "status": EnvelopeStatus.PENDING,
        }

        if self.webhook_service:
            message = IndividualStartedMessage(
                envelope_id=envelope_id,
                total_documents=total_documents,
                phase=self.phase,
            )
            await self.webhook_service.send_notification(message.model_dump())

    async def update_document_progress(self, envelope_id: str, document_name: str):
        """Update progress for a document"""
        if envelope_id in self.envelopes:
            self.envelopes[envelope_id]["completed_documents"] += 1
            completed = self.envelopes[envelope_id]["completed_documents"]
            total = self.envelopes[envelope_id]["total_documents"]

            if self.webhook_service:
                progress = DocumentProgress(
                    current_document=document_name,
                    completed=completed,
                    total=total,
                    percentage=round((completed / total) * 100, 2),
                )

                message = IndividualProgressMessage(
                    envelope_id=envelope_id, progress=progress, phase=self.phase
                )
                await self.webhook_service.send_notification(message.model_dump())

    async def complete_envelope(self, envelope_id: str, files: List[str]):
        """Mark envelope as completed"""
        if envelope_id in self.envelopes:
            self.envelopes[envelope_id]["status"] = EnvelopeStatus.COMPLETED

            if self.webhook_service:
                message = IndividualCompletedMessage(
                    envelope_id=envelope_id, files=files, phase=self.phase
                )
                await self.webhook_service.send_notification(message.model_dump())

    async def mark_envelope_failed(self, envelope_id: str, error: str):
        """Mark envelope as failed"""
        if envelope_id in self.envelopes:
            self.envelopes[envelope_id]["status"] = EnvelopeStatus.FAILED

            if self.webhook_service:
                message = IndividualErrorMessage(
                    envelope_id=envelope_id, error=error, phase=self.phase
                )
                await self.webhook_service.send_notification(message.model_dump())
