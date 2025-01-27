from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from semantic_kernel.contents.chat_history import ChatHistory
from services.ai import ChatService
from core.oauth2 import validate_docusign_access
from schemas import ChatMessage, ChatResponse


router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize service
chat_service = ChatService()

# Store chat histories for different users
chat_histories: Dict[str, ChatHistory] = {}


@router.post("/", response_model=ChatResponse)
async def chat(
    message: ChatMessage, auth_info: dict = Depends(validate_docusign_access)
):
    try:
        # Get response from chat service
        response = await chat_service.get_chat_response(
            message=message.message, user_id=auth_info["account_id"]
        )

        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.delete("/history")
async def clear_chat_history(auth_info: dict = Depends(validate_docusign_access)):
    """Clear chat history for the current user"""
    try:
        chat_service.clear_history(auth_info["account_id"])
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error clearing chat history: {str(e)}"
        )
