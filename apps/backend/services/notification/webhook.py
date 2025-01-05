from typing import Dict, Any
import httpx

from schemas import WebhookSchema


class WebhookService:
    def __init__(self, webhook_config: WebhookSchema):
        self.config = webhook_config

    async def send_notification(self, payload: Dict[str, Any]):
        """Send webhook notification"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.config.url,
                    json=payload,
                    headers=self.config.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
            except Exception as e:
                print(f"Webhook notification failed: {str(e)}")
                return False
