from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    ds_client_id: str = os.getenv("DS_CLIENT_ID")
    ds_client_secret: str = os.getenv("DS_CLIENT_SECRET")
    authorization_server: str = os.getenv(
        "DS_AUTH_SERVER", "https://account-d.docusign.com"
    )
    app_url: str = os.getenv("APP_URL", "http://localhost:8000/api")
    callback_route: str = os.getenv("CALLBACK_ROUTE", "/callback")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


CONFIG = {
    "ds_client_id": get_settings().ds_client_id,
    "ds_client_secret": get_settings().ds_client_secret,
    "authorization_server": get_settings().authorization_server,
    "app_url": get_settings().app_url,
    "callback_route": get_settings().callback_route,
}
