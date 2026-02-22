"""Multi-tenancy middleware — ensures all queries are scoped to a business."""
import uuid
from sqlalchemy import Select


def scope_to_business(query: Select, business_id: uuid.UUID, model) -> Select:
    """Add business_id filter to any SQLAlchemy query.

    Usage:
        query = select(Lead)
        query = scope_to_business(query, business.id, Lead)
    """
    return query.where(model.business_id == business_id)
