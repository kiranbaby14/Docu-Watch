from docusign_esign import ApiClient, EnvelopesApi
from fastapi import HTTPException
import requests


class DocuSignService:
    def __init__(self):
        self.api_client = ApiClient()
        self.account_id = None

    async def get_access_token(self, code: str):
        token_url = f"https://{settings.DOCUSIGN_AUTHORIZATION_SERVER}/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.DOCUSIGN_CLIENT_ID,
            "client_secret": settings.DOCUSIGN_CLIENT_SECRET,
            "redirect_uri": settings.DOCUSIGN_CALLBACK_URL,
        }
        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        return response.json()

    async def get_user_contracts(self, access_token: str):
        self.api_client.host = "https://demo.docusign.net/restapi"
        self.api_client.set_default_header("Authorization", f"Bearer {access_token}")

        envelopes_api = EnvelopesApi(self.api_client)
        response = envelopes_api.list_status_changes(self.account_id)
        return response.envelopes
