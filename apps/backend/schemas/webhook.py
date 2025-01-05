from typing import Dict, Optional
from pydantic import BaseModel


class WebhookSchema(BaseModel):
    url: str
    headers: Optional[Dict[str, str]] = None
