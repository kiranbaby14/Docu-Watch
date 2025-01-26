# batch_progress.py
from typing import Dict, Optional
from ..notification.webhook import WebhookService
from schemas.webhook import (
    BatchProgressMessage,
    BatchCompletedMessage,
    OverallProgress,
    EnvelopeStatusInfo,
    CurrentEnvelopeProgress,
    EnvelopeStatus,
    ProcessingPhase,
)


class BatchProgressTracker:
    def __init__(
        self,
        total_envelopes: int,
        webhook_service: Optional[WebhookService] = None,
        phase: ProcessingPhase = ProcessingPhase.DOWNLOAD,
    ):
        self.total_envelopes = total_envelopes
        self.completed_envelopes = 0
        self.total_documents = 0
        self.completed_documents = 0
        self.envelope_statuses: Dict[str, EnvelopeStatusInfo] = {}
        self.webhook_service = webhook_service
        self.phase = phase

    def _get_overall_progress(self) -> OverallProgress:
        """Calculate overall batch progress"""
        return OverallProgress(
            completed_envelopes=self.completed_envelopes,
            total_envelopes=self.total_envelopes,
            completed_documents=self.completed_documents,
            total_documents=self.total_documents,
            percentage=(
                round((self.completed_documents / self.total_documents * 100), 2)
                if self.total_documents > 0
                else 0
            ),
        )

    async def register_envelope(self, envelope_id: str, total_documents: int):
        """Register a new envelope in the batch"""
        self.envelope_statuses[envelope_id] = EnvelopeStatusInfo(
            total_documents=total_documents,
            completed_documents=0,
            status=EnvelopeStatus.PENDING,
        )
        self.total_documents += total_documents

        if self.webhook_service:
            message = BatchProgressMessage(
                overall_progress=self._get_overall_progress(),
                envelope_statuses=self.envelope_statuses,
                phase=self.phase,
            )
            await self.webhook_service.send_notification(message.model_dump())

    async def update_envelope_progress(self, envelope_id: str, document_name: str):
        """Update progress for a specific envelope"""
        if envelope_id in self.envelope_statuses:
            status = self.envelope_statuses[envelope_id]
            status.completed_documents += 1
            self.completed_documents += 1

            if self.webhook_service:
                current_envelope = CurrentEnvelopeProgress(
                    id=envelope_id,
                    current_document=document_name,
                    completed=status.completed_documents,
                    total=status.total_documents,
                )

                message = BatchProgressMessage(
                    overall_progress=self._get_overall_progress(),
                    current_envelope=current_envelope,
                    envelope_statuses=self.envelope_statuses,
                    phase=self.phase,
                )
                await self.webhook_service.send_notification(message.model_dump())

    async def complete_envelope(self, envelope_id: str):
        """Mark an envelope as completed"""
        if envelope_id in self.envelope_statuses:
            self.envelope_statuses[envelope_id].status = EnvelopeStatus.COMPLETED
            self.completed_envelopes += 1

            if (
                self.completed_envelopes == self.total_envelopes
                and self.webhook_service
            ):
                message = BatchCompletedMessage(
                    overall_progress=self._get_overall_progress(),
                    envelope_statuses=self.envelope_statuses,
                    phase=self.phase,
                )
                await self.webhook_service.send_notification(message.model_dump())
