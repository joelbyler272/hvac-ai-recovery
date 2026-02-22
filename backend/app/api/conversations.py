import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.services.crud import (
    get_conversations,
    get_conversation_detail,
    get_conversation_messages,
    update_conversation_status,
)
from app.services.sms import send_sms, save_message
from app.api.schemas import convo_to_dict, msg_to_dict

router = APIRouter()


class SendMessageRequest(BaseModel):
    body: str


@router.get("/")
async def list_conversations(
    status: str = None,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """List active conversations."""
    convos = await get_conversations(db, business.id, status=status)
    return {"conversations": [convo_to_dict(c, lead=l) for c, l in convos]}


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Full conversation with messages."""
    convo = await get_conversation_detail(db, business.id, uuid.UUID(conversation_id))
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await get_conversation_messages(db, uuid.UUID(conversation_id))
    return {
        "conversation": convo_to_dict(convo),
        "messages": [msg_to_dict(m) for m in messages],
    }


@router.post("/{conversation_id}/takeover")
async def takeover_conversation(
    conversation_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Human takes over from AI."""
    convo = await update_conversation_status(
        db, business.id, uuid.UUID(conversation_id), "human_active"
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": convo_to_dict(convo)}


@router.post("/{conversation_id}/return-ai")
async def return_to_ai(
    conversation_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Return conversation to AI handling."""
    convo = await update_conversation_status(
        db, business.id, uuid.UUID(conversation_id), "active"
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": convo_to_dict(convo)}


@router.post("/{conversation_id}/message")
async def send_manual_message(
    conversation_id: str,
    request: SendMessageRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Send a manual message in the conversation."""
    convo = await get_conversation_detail(db, business.id, uuid.UUID(conversation_id))
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get lead phone from conversation
    from sqlalchemy import select
    from app.models.lead import Lead

    lead_result = await db.execute(select(Lead).where(Lead.id == convo.lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await send_sms(
        db,
        to=lead.phone,
        from_=business.twilio_number,
        body=request.body,
        conversation_id=convo.id,
        business_id=business.id,
        sender_type="human",
    )

    return {"status": "sent"}
