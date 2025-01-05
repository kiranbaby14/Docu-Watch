from fastapi import APIRouter
from typing import Dict

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Simple in-memory storage for progress
# In production, you might want to use Redis or a database
progress_store: Dict[str, dict] = {}


@router.post("/docusign")
async def receive_webhook(payload: dict):
    """Receive and store webhook notifications"""
    if "envelope_id" in payload:
        progress_store[payload["envelope_id"]] = payload
    return {"status": "received"}


@router.get("/progress/{envelope_id}")
async def get_progress(envelope_id: str):
    """Get progress for a specific envelope"""
    return progress_store.get(envelope_id, {"status": "not_found"})


@router.get("/progress")
async def get_all_progress():
    """Get progress for all envelopes"""
    return progress_store
