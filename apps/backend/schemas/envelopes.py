from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Envelope(BaseModel):
    envelope_id: str
    status: str
    subject: str
    sent_date: str
    last_modified: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
