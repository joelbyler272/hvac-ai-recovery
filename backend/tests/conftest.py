"""Shared test fixtures."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_business():
    biz = MagicMock()
    biz.id = uuid.uuid4()
    biz.name = "Smith's Heating & Air"
    biz.owner_name = "John Smith"
    biz.owner_email = "john@smithhvac.com"
    biz.owner_phone = "+15551234567"
    biz.business_phone = "+15559876543"
    biz.twilio_number = "+15550001111"
    biz.timezone = "America/New_York"
    biz.business_hours = {
        "monday": {"open": "08:00", "close": "17:00"},
        "tuesday": {"open": "08:00", "close": "17:00"},
        "wednesday": {"open": "08:00", "close": "17:00"},
        "thursday": {"open": "08:00", "close": "17:00"},
        "friday": {"open": "08:00", "close": "17:00"},
        "saturday": None,
        "sunday": None,
    }
    biz.services = ["AC Repair", "Heating", "Maintenance"]
    biz.avg_job_value = 350.00
    biz.ai_greeting = None
    biz.ai_instructions = None
    biz.notification_prefs = {
        "sms": True,
        "email": True,
        "quiet_start": "21:00",
        "quiet_end": "07:00",
    }
    biz.subscription_status = "active"
    return biz


@pytest.fixture
def mock_lead():
    lead = MagicMock()
    lead.id = uuid.uuid4()
    lead.business_id = uuid.uuid4()
    lead.phone = "+15552223333"
    lead.name = None
    lead.email = None
    lead.address = None
    lead.service_needed = None
    lead.urgency = None
    lead.status = "new"
    lead.source = "missed_call"
    lead.estimated_value = None
    lead.preferred_time = None
    lead.notes = None
    lead.created_at = datetime.utcnow()
    lead.updated_at = datetime.utcnow()
    return lead


@pytest.fixture
def mock_conversation():
    convo = MagicMock()
    convo.id = uuid.uuid4()
    convo.business_id = uuid.uuid4()
    convo.lead_id = uuid.uuid4()
    convo.call_id = uuid.uuid4()
    convo.status = "active"
    convo.follow_up_count = 0
    convo.next_follow_up_at = None
    convo.qualification_data = {}
    convo.created_at = datetime.utcnow()
    convo.updated_at = datetime.utcnow()
    return convo
