from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import requests
from core.config import CONFIG
from schemas.envelopes import Token

router = APIRouter(tags=["authentication"])


@router.get("/login")
async def login():
    auth_url = (
        f"{CONFIG['authorization_server']}/oauth/auth?"
        f"response_type=code&"
        f"client_id={CONFIG['ds_client_id']}&"
        f"redirect_uri={CONFIG['app_url']}{CONFIG['callback_route']}&"
        f"scope=signature%20extended"
    )
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(code: str):
    token_url = f"{CONFIG['authorization_server']}/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CONFIG["ds_client_id"],
        "client_secret": CONFIG["ds_client_secret"],
        "redirect_uri": f"{CONFIG['app_url']}{CONFIG['callback_route']}",
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Token acquisition failed")

    frontend_url = "http://localhost:3000/dashboard"
    return RedirectResponse(
        url=f"{frontend_url}?access_token={response.json()['access_token']}"
    )


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    token_url = f"{CONFIG['authorization_server']}/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CONFIG["ds_client_id"],
        "client_secret": CONFIG["ds_client_secret"],
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Token refresh failed")

    return Token(**response.json())
