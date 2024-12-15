from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DOCUSIGN_CLIENT_ID: str
    DOCUSIGN_CLIENT_SECRET: str
    DOCUSIGN_AUTHORIZATION_SERVER: str = "account-d.docusign.com"
    DOCUSIGN_CALLBACK_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
