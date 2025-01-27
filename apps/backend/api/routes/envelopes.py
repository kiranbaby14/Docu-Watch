from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os
import json
from typing import List, Optional, Dict
from services.docusign import EnvelopeService
from services.document import DocumentDownloader
from services.notification import WebhookService
from services.ai import PDFProcessor
from schemas import (
    EnvelopeSchema,
    EnvelopeDocumentsSchema,
    WebhookSchema,
    TerminateMessage,
)
from core.oauth2 import validate_docusign_access


router = APIRouter(prefix="/envelopes", tags=["envelopes"])


@router.get("/", response_model=List[EnvelopeSchema])
async def get_envelopes(
    background_tasks: BackgroundTasks,
    webhook_url: Optional[str] = None,
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

    webhook_termination_message = TerminateMessage(terminate=True)

    webhook_service = None
    if webhook_url:
        webhook_config = WebhookSchema(url=webhook_url, headers=webhook_headers)
        webhook_service = WebhookService(webhook_config)
        if not envelopes:
            await webhook_service.send_notification(
                webhook_termination_message.model_dump()
            )

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
        await pdf_processor.process_background(auth_info["account_id"])

    if envelopes:
        background_tasks.add_task(process_after_download)

    return envelopes


@router.get("/json_files", response_model=List[dict])
async def get_json_files(auth_info: dict = Depends(validate_docusign_access)):
    """
    Retrieve all JSON files associated with the authenticated account.

    Returns:
        List[dict]: A list of JSON objects from the processed documents
    """
    try:
        # Extract account_id from auth info
        account_id = auth_info["account_id"]

        # Get the backend directory path
        backend_dir = Path(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        output_path = backend_dir / "data" / "output" / account_id

        if not output_path.exists():
            return JSONResponse(
                content={"message": "No processed documents found for this account"},
                status_code=404,
            )

        json_files = []

        # Recursively find all JSON files in the account directory
        for json_path in output_path.rglob("*.json"):
            try:
                with open(json_path, "r") as f:
                    json_content = json.load(f)
                    json_files.append(json_content)
            except json.JSONDecodeError as e:
                continue  # Skip invalid JSON files
            except Exception as e:
                continue  # Skip files with other errors

        if not json_files:
            return JSONResponse(
                content={"message": "No valid JSON files found for this account"},
                status_code=404,
            )

        return json_files

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving JSON files: {str(e)}"
        )


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
