from typing import Optional
from ..notification import WebhookService
from ..tracking import ProgressTracker, BatchProgressTracker
from ..docusign import EnvelopeService
import os


class DocumentDownloader:
    def __init__(
        self,
        envelope_service: EnvelopeService,
        webhook_service: Optional[WebhookService] = None,
        batch_progress: Optional[BatchProgressTracker] = None,
    ):
        self.envelope_service = envelope_service
        self.webhook_service = webhook_service
        self.progress_tracker = ProgressTracker(webhook_service)
        self.batch_progress = batch_progress

        # Get account_id from envelope_service
        self.account_id = envelope_service.account_id

        # Get the backend directory path (going up 3 levels from downloader.py)
        # downloader.py -> document -> services -> backend
        backend_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.download_path = os.path.join(
            backend_dir, "data", "docusign_downloads", self.account_id
        )
        os.makedirs(self.download_path, exist_ok=True)

    async def download_envelope_documents(self, envelope_id: str):
        """Download all documents for an envelope"""
        try:
            # Get documents list
            docs_info = await self.envelope_service.get_envelope_documents(envelope_id)

            # Initialize progress tracking
            await self.progress_tracker.start_envelope(
                envelope_id, len(docs_info["documents"])
            )

            # Register with batch tracker if available
            if self.batch_progress:
                await self.batch_progress.register_envelope(
                    envelope_id, len(docs_info["documents"])
                )

            envelope_dir = os.path.join(self.download_path, envelope_id)
            os.makedirs(envelope_dir, exist_ok=True)

            downloaded_files = []
            existing_files = []

            for doc in docs_info["documents"]:
                temp_file_path, content_type, filename = (
                    await self.envelope_service.get_document(
                        envelope_id, doc["document_id"]
                    )
                )

                final_path = os.path.join(envelope_dir, filename)

                # Check if file already exists
                if os.path.exists(final_path):
                    # Clean up temp file since we won't use it
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    existing_files.append(filename)
                else:
                    # Move new file to final location
                    os.rename(temp_file_path, final_path)
                    downloaded_files.append(filename)

                # Update progress regardless of whether file was new or existing
                await self.progress_tracker.update_document_progress(
                    envelope_id, filename
                )

                # Update batch progress if available
                if self.batch_progress:
                    await self.batch_progress.update_envelope_progress(
                        envelope_id, filename
                    )

            # Mark envelope complete with all files
            all_files = downloaded_files + existing_files
            await self.progress_tracker.complete_envelope(envelope_id, all_files)

            # Update batch progress if available
            if self.batch_progress:
                await self.batch_progress.complete_envelope(envelope_id)

            return envelope_dir, {
                "downloaded": downloaded_files,
                "existing": existing_files,
            }

        except Exception as e:
            await self.progress_tracker.mark_envelope_failed(envelope_id, str(e))
            raise
