from fastapi import APIRouter

router = APIRouter()


@router.get("/businesses")
async def list_businesses():
    """List all client businesses (admin only)."""
    # TODO: Implement admin auth + business listing
    return {"businesses": []}


@router.post("/businesses")
async def onboard_business():
    """Onboard a new client business."""
    # TODO: Implement business onboarding
    return {"business": None}


@router.patch("/businesses/{business_id}")
async def update_business(business_id: str):
    """Update client configuration."""
    # TODO: Implement business update
    return {"business": None}


@router.post("/businesses/{business_id}/provision")
async def provision_number(business_id: str):
    """Provision a Twilio number for a business."""
    # TODO: Implement Twilio number provisioning
    return {"twilio_number": None}


@router.get("/health")
async def system_health():
    """System health check."""
    return {"status": "healthy"}


@router.get("/metrics")
async def system_metrics():
    """Cross-client metrics."""
    # TODO: Implement system-wide metrics
    return {"metrics": None}
