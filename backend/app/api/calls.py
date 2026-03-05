import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.models.call import Call
from app.services.crud import get_calls
from app.api.schemas import call_to_dict

router = APIRouter()


@router.get("/")
async def list_calls(
    status: str | None = None,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """List calls for the business."""
    calls = await get_calls(db, business.id, status=status)
    return {"calls": [call_to_dict(c) for c in calls]}


@router.get("/{call_id}/recording")
async def get_call_recording(
    call_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Get the voice AI call recording URL."""
    result = await db.execute(
        select(Call).where(
            Call.id == uuid.UUID(call_id),
            Call.business_id == business.id,
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if not call.recording_url:
        raise HTTPException(status_code=404, detail="No recording available")

    return {"recording_url": call.recording_url}


@router.get("/{call_id}/transcript")
async def get_call_transcript(
    call_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Get the voice AI call transcript."""
    result = await db.execute(
        select(Call).where(
            Call.id == uuid.UUID(call_id),
            Call.business_id == business.id,
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "transcript": call.voice_ai_transcript or call.transcription,
        "duration_seconds": call.voice_ai_duration_seconds or call.duration_seconds,
        "voice_ai_used": call.voice_ai_used,
    }
