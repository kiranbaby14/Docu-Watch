from pydantic import BaseModel
from typing import Optional


class EnvelopeSchema(BaseModel):
    envelope_id: str
    status: str
    subject: str
    sent_date: str
    last_modified: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
