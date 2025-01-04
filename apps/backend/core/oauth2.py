from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
import requests

from .settings import get_settings

settings = get_settings()

# OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.authorization_server}/oauth/auth",
    tokenUrl=f"{settings.authorization_server}/oauth/token",
)


async def validate_docusign_access(token: str = Depends(oauth2_scheme)):
    """
    Validates the access token and checks DocuSign account access.

    Args:
        token (str): OAuth2 access token obtained from DocuSign

    Returns:
        dict: Contains validated token and DocuSign account information
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{settings.authorization_server}/oauth/userinfo", headers=headers
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "code": "token_expired",
                    "message": "Your session has expired. Please login again.",
                    "details": response.text,
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    "status": "error",
                    "code": "user_info_failed",
                    "message": "Failed to get user information",
                    "details": response.text,
                },
            )

        # Check DocuSign account access
        user_info = response.json()
        if not user_info.get("accounts"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No DocuSign accounts found for this user",
            )

        return {
            "token": token,
            "account_id": user_info["accounts"][0]["account_id"],
            "base_uri": user_info["accounts"][0]["base_uri"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
