from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
import requests
from urllib.parse import urlencode

from core.settings import Settings, get_settings
from schemas.envelope import TokenSchema
from services.auth import AuthService

router = APIRouter(tags=["authentication"])


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(settings)


@router.get("/login")
async def login(auth_service: AuthService = Depends(get_auth_service)):
    login_url = auth_service.get_login_url()
    return RedirectResponse(login_url)


@router.get("/callback")
async def callback(code: str, auth_service: AuthService = Depends(get_auth_service)):
    redirect_url = await auth_service.exchange_code_for_token(code)
    return RedirectResponse(url=redirect_url)


@router.post("/refresh")
async def refresh_token(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
):
    token_data = await auth_service.refresh_token(refresh_token)
    return TokenSchema(**token_data)
