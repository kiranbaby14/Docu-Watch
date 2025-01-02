from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import List
from services.docusign import DocuSignService
from services.documents import DocumentService
from schemas.envelopes import Envelope
from schemas.documents import EnvelopeDocuments
from core.oauth2 import oauth2_scheme

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


@router.get("/", response_model=List[Envelope])
async def get_envelopes(token: str = Depends(oauth2_scheme)):
    docusign_service = DocuSignService(token)
    return await docusign_service.get_completed_envelopes()


@router.get("/{envelope_id}/documents", response_model=EnvelopeDocuments)
async def list_envelope_documents(
    envelope_id: str, token: str = Depends(oauth2_scheme)
):
    docusign_service = DocuSignService(token)
    return await docusign_service.get_envelope_documents(envelope_id)


@router.get("/{envelope_id}/documents/{document_id}/download")
async def download_document(
    envelope_id: str, document_id: str, token: str = Depends(oauth2_scheme)
):
    """Download a document from an envelope"""
    docusign_service = DocuSignService(token)

    temp_file_path, content_type, filename = await docusign_service.get_document(
        envelope_id, document_id
    )

    return FileResponse(path=temp_file_path, media_type=content_type, filename=filename)
