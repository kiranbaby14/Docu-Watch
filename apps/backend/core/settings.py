from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # DocuSign Settings
    ds_client_id: str = os.getenv("DS_CLIENT_ID")
    ds_client_secret: str = os.getenv("DS_CLIENT_SECRET")
    authorization_server: str = os.getenv(
        "DS_AUTH_SERVER", "https://account-d.docusign.com"
    )
    app_url: str = os.getenv("APP_URL", "http://localhost:8000/api")
    callback_route: str = os.getenv("CALLBACK_ROUTE", "/callback")

    # Frontend Settings
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    frontend_callback_route: str = os.getenv("FRONTEND_CALLBACK_ROUTE", "/dashboard")

    # Neo4j Settings
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # Gemini Settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-pro")

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def frontend_callback_url(self) -> str:
        """Get the complete frontend callback URL"""
        return f"{self.frontend_url}{self.frontend_callback_route}"

    # Configuration Getters
    def get_docusign_config(self) -> dict:
        """Get DocuSign configuration"""
        return {
            "ds_client_id": self.ds_client_id,
            "ds_client_secret": self.ds_client_secret,
            "authorization_server": self.authorization_server,
            "app_url": self.app_url,
            "callback_route": self.callback_route,
        }

    def get_neo4j_config(self) -> dict:
        """Get Neo4j configuration"""
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password,
            "database": self.neo4j_database,
        }

    def get_gemini_config(self) -> dict:
        """Get Gemini configuration"""
        return {
            "api_key": self.gemini_api_key,
            "model": self.gemini_model,
        }


@lru_cache()
def get_settings():
    return Settings()
