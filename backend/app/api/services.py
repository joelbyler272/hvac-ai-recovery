import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_business
from app.models.business import Business
from app.services.crud import (
    get_services,
    create_service,
    update_service,
    delete_service,
    reorder_services,
)
from app.api.schemas import service_to_dict

router = APIRouter()


class CreateServiceRequest(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    duration_minutes: int = 60
    is_bookable: bool = False
    sort_order: int = 0


class ReorderItem(BaseModel):
    id: str
    sort_order: int


class ReorderRequest(BaseModel):
    order: list[ReorderItem]


@router.get("/")
async def list_services(
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """List active services for the business."""
    services = await get_services(db, business.id)
    return {"services": [service_to_dict(s) for s in services]}


@router.post("/")
async def create_service_endpoint(
    request: CreateServiceRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service."""
    if request.is_bookable and request.price is None:
        raise HTTPException(
            status_code=400,
            detail="Bookable services must have a price",
        )

    svc = await create_service(
        db,
        business.id,
        name=request.name,
        description=request.description,
        price=request.price,
        duration_minutes=request.duration_minutes,
        is_bookable=request.is_bookable,
        sort_order=request.sort_order,
    )
    return {"service": service_to_dict(svc)}


@router.patch("/{service_id}")
async def update_service_endpoint(
    service_id: str,
    request: Request,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Update a service."""
    body = await request.json()
    allowed = {"name", "description", "price", "duration_minutes", "is_bookable", "sort_order"}
    update_data = {k: v for k, v in body.items() if k in allowed}

    # Validate: bookable services must have a price
    if update_data.get("is_bookable") and update_data.get("price") is None:
        # Check if existing service already has a price
        from app.services.crud import get_service
        existing = await get_service(db, business.id, uuid.UUID(service_id))
        if existing and existing.price is None and "price" not in update_data:
            raise HTTPException(
                status_code=400,
                detail="Bookable services must have a price",
            )

    svc = await update_service(db, business.id, uuid.UUID(service_id), **update_data)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"service": service_to_dict(svc)}


@router.delete("/{service_id}")
async def delete_service_endpoint(
    service_id: str,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a service."""
    deleted = await delete_service(db, business.id, uuid.UUID(service_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"deleted": True}


@router.post("/reorder")
async def reorder_services_endpoint(
    request: ReorderRequest,
    business: Business = Depends(get_current_business),
    db: AsyncSession = Depends(get_db),
):
    """Bulk update sort order for services."""
    await reorder_services(
        db,
        business.id,
        [{"id": item.id, "sort_order": item.sort_order} for item in request.order],
    )
    services = await get_services(db, business.id)
    return {"services": [service_to_dict(s) for s in services]}
