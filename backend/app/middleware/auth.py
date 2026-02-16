from fastapi import Request, HTTPException

from app.models.business import Business


async def get_current_business(request: Request) -> Business:
    """
    Extract business from JWT token.
    All downstream queries use this business_id for multi-tenant scoping.
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    # TODO: Validate JWT via Supabase Auth
    # user = supabase.auth.get_user(token)
    # if not user:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    #
    # business = await get_business_by_user_id(user.id)
    # if not business:
    #     raise HTTPException(status_code=403, detail="No business associated")
    #
    # return business

    raise HTTPException(status_code=501, detail="Auth not yet implemented")
