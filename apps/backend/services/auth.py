from fastapi import HTTPException
import requests
from urllib.parse import urlencode
from core.settings import Settings


class AuthService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_login_url(self) -> str:
        params = {
            "response_type": "code",
            "client_id": self.settings.ds_client_id,
            "redirect_uri": f"{self.settings.app_url}{self.settings.callback_route}",
            "scope": "signature extended",
        }
        return f"{self.settings.authorization_server}/oauth/auth?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict:
        token_url = f"{self.settings.authorization_server}/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.settings.ds_client_id,
            "client_secret": self.settings.ds_client_secret,
            "redirect_uri": f"{self.settings.app_url}{self.settings.callback_route}",
        }

        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token acquisition failed")

        token_data = response.json()
        redirect_url = self.get_frontend_redirect_url(token_data["access_token"])

        return redirect_url

    def get_frontend_redirect_url(self, access_token: str) -> str:
        """Construct frontend redirect URL with token"""
        return f"{self.settings.frontend_callback_url}?access_token={access_token}"

    async def refresh_token(self, refresh_token: str) -> dict:
        token_url = f"{self.settings.authorization_server}/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.settings.ds_client_id,
            "client_secret": self.settings.ds_client_secret,
        }

        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Token refresh failed")

        return response.json()
