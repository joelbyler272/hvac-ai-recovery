from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.auth import get_current_business
from app.models.business import Business

router = APIRouter()


class SendMessageRequest(BaseModel):
    body: str


@router.get("/")
async def list_conversations(
    business: Business = Depends(get_current_business),
):
    """List active conversations."""
    # TODO: Implement conversations query
    return {"conversations": []}


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str, business: Business = Depends(get_current_business)
):
    """Full conversation with messages."""
    # TODO: Implement conversation detail
    return {"conversation": None, "messages": []}


@router.post("/{conversation_id}/takeover")
async def takeover_conversation(
    conversation_id: str, business: Business = Depends(get_current_business)
):
    """Human takes over from AI."""
    # TODO: Implement takeover
    return {"status": "human_active"}


@router.post("/{conversation_id}/return-ai")
async def return_to_ai(
    conversation_id: str, business: Business = Depends(get_current_business)
):
    """Return conversation to AI handling."""
    # TODO: Implement return to AI
    return {"status": "active"}


@router.post("/{conversation_id}/message")
async def send_manual_message(
    conversation_id: str,
    request: SendMessageRequest,
    business: Business = Depends(get_current_business),
):
    """Send a manual message in the conversation."""
    # TODO: Implement manual message send
    return {"message": None}
