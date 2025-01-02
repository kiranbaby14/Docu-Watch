from fastapi.security import OAuth2AuthorizationCodeBearer
from .config import CONFIG

# OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{CONFIG['authorization_server']}/oauth/auth",
    tokenUrl=f"{CONFIG['authorization_server']}/oauth/token",
)
