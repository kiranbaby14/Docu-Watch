from pydantic import BaseModel, EmailStr
from typing import Optional


class UserSchema(BaseModel):
    name: str
    email: EmailStr


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
