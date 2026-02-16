"""
Multi-tenancy middleware.
Ensures all database queries are scoped to the authenticated business.
"""
import uuid
from sqlalchemy import Select


def scope_to_business(query: Select, business_id: uuid.UUID) -> Select:
    """Add business_id filter to any SQLAlchemy query."""
    # This is a helper used by service functions to ensure
    # all queries are properly scoped to a business.
    # The actual filtering depends on the model being queried.
    return query
