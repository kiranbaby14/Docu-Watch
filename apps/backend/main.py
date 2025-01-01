from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from docusign_esign import ApiClient, EnvelopesApi
from pydantic import BaseModel
import os
import uvicorn
import requests
from typing import List
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


CONFIG = {
    "ds_client_id": os.getenv("DS_CLIENT_ID"),
    "ds_client_secret": os.getenv("DS_CLIENT_SECRET"),
    "authorization_server": os.getenv("DS_AUTH_SERVER"),
    "app_url": os.getenv("APP_URL"),
    "callback_route": os.getenv("CALLBACK_ROUTE"),
}


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class Contract(BaseModel):
    envelope_id: str
    status: str
    subject: str
    sent_date: str
    last_modified: str


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{CONFIG['authorization_server']}/oauth/auth",
    tokenUrl=f"{CONFIG['authorization_server']}/oauth/token",
)


@app.get("/")
async def root():
    return {"message": "DocuSign Integration API"}


@app.get("/login")
async def login():
    auth_url = (
        f"{CONFIG['authorization_server']}/oauth/auth?"
        f"response_type=code&"
        f"client_id={CONFIG['ds_client_id']}&"
        f"redirect_uri={CONFIG['app_url']}{CONFIG['callback_route']}&"
        f"scope=signature%20extended"
    )
    return RedirectResponse(auth_url)


@app.get("/callback")
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

    # Instead of returning JSON, redirect to frontend with token
    token_data = response.json()
    frontend_url = "http://localhost:3000/dashboard"  # Adjust this to the frontend URL
    return RedirectResponse(
        url=f"{frontend_url}?access_token={token_data['access_token']}"
    )


@app.get("/envelopes")
async def list_envelopes(token: str):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        user_info = requests.get(
            f"{CONFIG['authorization_server']}/oauth/userinfo", headers=headers
        ).json()

        account_id = user_info["accounts"][0]["account_id"]
        base_path = user_info["accounts"][0]["base_uri"]

        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {token}")

        envelope_api = EnvelopesApi(api_client)
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

        results = envelope_api.list_status_changes(
            account_id=account_id, from_date=from_date
        )

        return {"envelopes": results.to_dict()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import traceback


@app.post("/refresh")
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

    return response.json()


@app.get("/contracts", response_model=List[Contract])
async def get_contracts(token: str = Depends(oauth2_scheme)):
    try:
        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        user_info_response = requests.get(
            f"{CONFIG['authorization_server']}/oauth/userinfo", headers=headers
        )

        # Handle token issues with structured response
        if user_info_response.status_code == 401:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "code": "token_expired",
                    "message": "Your session has expired. Please login again.",
                    "details": user_info_response.text,
                },
            )

        if user_info_response.status_code != 200:
            return JSONResponse(
                status_code=user_info_response.status_code,
                content={
                    "status": "error",
                    "code": "user_info_failed",
                    "message": "Failed to get user information",
                    "details": user_info_response.text,
                },
            )

        user_info = user_info_response.json()

        if not user_info.get("accounts"):
            raise HTTPException(
                status_code=400, detail="No DocuSign accounts found for this user"
            )

        account_id = user_info["accounts"][0]["account_id"]
        base_uri = user_info["accounts"][0]["base_uri"]
        base_path = f"{base_uri}/restapi"

        # Setup DocuSign client
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header(
            header_name="Authorization", header_value=f"Bearer {token}"
        )

        # Get envelopes
        envelopes_api = EnvelopesApi(api_client)
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            response = envelopes_api.list_status_changes(
                account_id=account_id,
                from_date=from_date,
                from_to_status="completed",  # Find envelopes completed during period
            )
        except Exception as api_error:
            error_traceback = traceback.format_exc()
            print(f"DocuSign API Error Full Traceback:\n{error_traceback}")
            raise HTTPException(
                status_code=500,
                detail=f"DocuSign API error: {str(api_error)}\nTraceback: {error_traceback}",
            )

        contracts = []
        for envelope in response.envelopes:
            contracts.append(
                Contract(
                    envelope_id=envelope.envelope_id,
                    status=envelope.status,
                    subject=envelope.email_subject or "",
                    sent_date=envelope.sent_date_time or "",
                    last_modified=envelope.last_modified_date_time or "",
                )
            )

        return contracts
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Unexpected error full traceback:\n{error_traceback}")
        raise HTTPException(
            status_code=500, detail=f"Error: {str(e)}\nTraceback: {error_traceback}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
