from fastapi import APIRouter, Depends
from ..services.docusign import DocuSignService

router = APIRouter()
docusign_service = DocuSignService()


@router.get("/auth/docusign/callback")
async def docusign_callback(code: str):
    token_data = await docusign_service.get_access_token(code)
    return token_data


@router.get("/contracts")
async def get_contracts(access_token: str):
    contracts = await docusign_service.get_user_contracts(access_token)
    return contracts
