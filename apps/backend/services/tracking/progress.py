from typing import List, Optional
from ..notification.webhook import WebhookService


class ProgressTracker:
    def __init__(self, webhook_service: Optional[WebhookService] = None):
        self.webhook_service = webhook_service
        self.envelopes = {}

    async def start_envelope(self, envelope_id: str, total_documents: int):
        """Initialize tracking for an envelope"""
        self.envelopes[envelope_id] = {
            "total_documents": total_documents,
            "completed_documents": 0,
            "status": "in_progress",
        }

        if self.webhook_service:
            await self.webhook_service.send_notification(
                {
                    "status": "started",
                    "envelope_id": envelope_id,
                    "total_documents": total_documents,
                }
            )

    async def update_document_progress(self, envelope_id: str, document_name: str):
        """Update progress for a document"""
        if envelope_id in self.envelopes:
            self.envelopes[envelope_id]["completed_documents"] += 1

            if self.webhook_service:
                await self.webhook_service.send_notification(
                    {
                        "status": "in_progress",
                        "envelope_id": envelope_id,
                        "progress": {
                            "current_document": document_name,
                            "completed": self.envelopes[envelope_id][
                                "completed_documents"
                            ],
                            "total": self.envelopes[envelope_id]["total_documents"],
                            "percentage": round(
                                (
                                    self.envelopes[envelope_id]["completed_documents"]
                                    / self.envelopes[envelope_id]["total_documents"]
                                )
                                * 100,
                                2,
                            ),
                        },
                    }
                )

    async def complete_envelope(self, envelope_id: str, files: List[str]):
        """Mark envelope as completed"""
        if envelope_id in self.envelopes:
            self.envelopes[envelope_id]["status"] = "completed"

            if self.webhook_service:
                await self.webhook_service.send_notification(
                    {"status": "completed", "envelope_id": envelope_id, "files": files}
                )

    async def mark_envelope_failed(self, envelope_id: str, error: str):
        """Mark envelope as failed"""
        if envelope_id in self.envelopes:
            self.envelopes[envelope_id]["status"] = "failed"

            if self.webhook_service:
                await self.webhook_service.send_notification(
                    {"status": "error", "envelope_id": envelope_id, "error": error}
                )
