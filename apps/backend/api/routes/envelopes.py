from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
from services.docusign import EnvelopeService
from services.document import DocumentDownloader
from services.notification import WebhookService
from services.tracking import BatchProgressTracker
from services.ai import PDFProcessor
from schemas import EnvelopeSchema, EnvelopeDocumentsSchema, WebhookSchema
from core.oauth2 import validate_docusign_access


router = APIRouter(prefix="/envelopes", tags=["envelopes"])


@router.get("/", response_model=List[EnvelopeSchema])
async def get_envelopes(
    background_tasks: BackgroundTasks,
    webhook_url: Optional[str] = "http://localhost:8000/webhook/docusign",
    webhook_headers: Optional[Dict[str, str]] = {},
    auth_info: dict = Depends(validate_docusign_access),
):
    """Get all completed envelopes and trigger background document downloads"""
    # Initialize services
    envelope_service = EnvelopeService(
        token=auth_info["token"],
        account_id=auth_info["account_id"],
        base_uri=auth_info["base_uri"],
    )

    # Get all completed envelopes
    envelopes = await envelope_service.get_completed_envelopes()

    webhook_service = None
    if webhook_url:
        webhook_config = WebhookSchema(url=webhook_url, headers=webhook_headers)
        webhook_service = WebhookService(webhook_config)

    # Initialize services
    downloader = DocumentDownloader(envelope_service, len(envelopes), webhook_service)
    pdf_processor = PDFProcessor(webhook_service)

    # Start background downloads
    for envelope in envelopes:
        background_tasks.add_task(
            downloader.download_envelope_documents, envelope["envelope_id"]
        )

    # Add tasks to wait for downloads and process PDFs
    async def process_after_download():
        await downloader.wait_for_downloads()
        await pdf_processor.process_background()

    background_tasks.add_task(process_after_download)

    return envelopes


@router.get("/{envelope_id}/documents", response_model=EnvelopeDocumentsSchema)
async def list_envelope_documents(
    envelope_id: str, auth_info: dict = Depends(validate_docusign_access)
):
    envelope_service = EnvelopeService(
        token=auth_info["token"],
        account_id=auth_info["account_id"],
        base_uri=auth_info["base_uri"],
    )
    return await envelope_service.get_envelope_documents(envelope_id)


@router.get("/{envelope_id}/documents/{document_id}/download")
async def download_document(
    envelope_id: str,
    document_id: str,
    auth_info: dict = Depends(validate_docusign_access),
):
    """Download a document from an envelope"""
    envelope_service = EnvelopeService(
        token=auth_info["token"],
        account_id=auth_info["account_id"],
        base_uri=auth_info["base_uri"],
    )

    temp_file_path, content_type, filename = await envelope_service.get_document(
        envelope_id, document_id
    )

    return FileResponse(path=temp_file_path, media_type=content_type, filename=filename)
