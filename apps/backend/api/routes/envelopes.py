from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from typing import List
from services.envelope import EnvelopeService
from schemas.envelope import EnvelopeSchema
from schemas.document import EnvelopeDocuments
from core.oauth2 import validate_docusign_access

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


@router.get("/", response_model=List[EnvelopeSchema])
async def get_envelopes(auth_info: dict = Depends(validate_docusign_access)):
    docusign_envelope_service = EnvelopeService(
        token=auth_info["token"],
        account_id=auth_info["account_id"],
        base_uri=auth_info["base_uri"],
    )
    return await docusign_envelope_service.get_completed_envelopes()


@router.get("/{envelope_id}/documents", response_model=EnvelopeDocuments)
async def list_envelope_documents(
    envelope_id: str, auth_info: dict = Depends(validate_docusign_access)
):
    docusign_envelope_service = EnvelopeService(
        token=auth_info["token"],
        account_id=auth_info["account_id"],
        base_uri=auth_info["base_uri"],
    )
    return await docusign_envelope_service.get_envelope_documents(envelope_id)


@router.get("/{envelope_id}/documents/{document_id}/download")
async def download_document(
    envelope_id: str,
    document_id: str,
    auth_info: dict = Depends(validate_docusign_access),
):
    """Download a document from an envelope"""
    docusign_envelope_service = EnvelopeService(
        token=auth_info["token"],
        account_id=auth_info["account_id"],
        base_uri=auth_info["base_uri"],
    )

    temp_file_path, content_type, filename = (
        await docusign_envelope_service.get_document(envelope_id, document_id)
    )

    return FileResponse(path=temp_file_path, media_type=content_type, filename=filename)
