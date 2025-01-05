from typing import Dict, Any, Optional
from ..notification.webhook import WebhookService


class BatchProgressTracker:
    def __init__(
        self, total_envelopes: int, webhook_service: Optional[WebhookService] = None
    ):
        self.total_envelopes = total_envelopes
        self.completed_envelopes = 0
        self.total_documents = 0
        self.completed_documents = 0
        self.envelope_statuses = {}
        self.webhook_service = webhook_service

    async def register_envelope(self, envelope_id: str, total_documents: int):
        """Register a new envelope in the batch"""
        self.envelope_statuses[envelope_id] = {
            "total_documents": total_documents,
            "completed_documents": 0,
            "status": "pending",
        }
        self.total_documents += total_documents

        if self.webhook_service:
            await self.webhook_service.send_notification(
                {
                    "status": "batch_progress",
                    "overall_progress": self._get_overall_progress(),
                    "envelope_statuses": self.envelope_statuses,
                }
            )

    async def update_envelope_progress(self, envelope_id: str, document_name: str):
        """Update progress for a specific envelope"""
        if envelope_id in self.envelope_statuses:
            self.envelope_statuses[envelope_id]["completed_documents"] += 1
            self.completed_documents += 1

            if self.webhook_service:
                await self.webhook_service.send_notification(
                    {
                        "status": "batch_progress",
                        "overall_progress": self._get_overall_progress(),
                        "current_envelope": {
                            "id": envelope_id,
                            "current_document": document_name,
                            "completed": self.envelope_statuses[envelope_id][
                                "completed_documents"
                            ],
                            "total": self.envelope_statuses[envelope_id][
                                "total_documents"
                            ],
                        },
                        "envelope_statuses": self.envelope_statuses,
                    }
                )

    async def complete_envelope(self, envelope_id: str):
        """Mark an envelope as completed"""
        if envelope_id in self.envelope_statuses:
            self.envelope_statuses[envelope_id]["status"] = "completed"
            self.completed_envelopes += 1

            if (
                self.completed_envelopes == self.total_envelopes
                and self.webhook_service
            ):
                await self.webhook_service.send_notification(
                    {
                        "status": "batch_completed",
                        "overall_progress": self._get_overall_progress(),
                        "envelope_statuses": self.envelope_statuses,
                    }
                )

    def _get_overall_progress(self) -> Dict[str, Any]:
        """Calculate overall batch progress"""
        return {
            "completed_envelopes": self.completed_envelopes,
            "total_envelopes": self.total_envelopes,
            "completed_documents": self.completed_documents,
            "total_documents": self.total_documents,
            "percentage": (
                round((self.completed_documents / self.total_documents * 100), 2)
                if self.total_documents > 0
                else 0
            ),
        }
