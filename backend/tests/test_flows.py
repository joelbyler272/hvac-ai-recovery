"""End-to-end flow tests — verifying serialization and schemas."""
import uuid
from datetime import datetime, date, time
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.api.schemas import (
    lead_to_dict,
    convo_to_dict,
    msg_to_dict,
    call_to_dict,
    appt_to_dict,
    metric_to_dict,
    biz_to_dict,
    activity_to_dict,
)


class TestLeadToDict:
    def _make_lead(self, **overrides):
        lead = MagicMock()
        lead.id = uuid.uuid4()
        lead.business_id = uuid.uuid4()
        lead.phone = "+15551234567"
        lead.name = "Sarah M."
        lead.email = "sarah@example.com"
        lead.address = "123 Main St"
        lead.service_needed = "AC not cooling"
        lead.urgency = "soon"
        lead.status = "qualifying"
        lead.source = "missed_call"
        lead.estimated_value = Decimal("350.00")
        lead.preferred_time = "tomorrow morning"
        lead.notes = "Needs unit check"
        lead.created_at = datetime(2026, 2, 16, 14, 30)
        lead.updated_at = datetime(2026, 2, 16, 14, 35)
        for k, v in overrides.items():
            setattr(lead, k, v)
        return lead

    def test_serializes_all_fields(self):
        lead = self._make_lead()
        d = lead_to_dict(lead)

        assert d["phone"] == "+15551234567"
        assert d["name"] == "Sarah M."
        assert d["status"] == "qualifying"
        assert d["preferred_time"] == "tomorrow morning"
        assert d["estimated_value"] == 350.0
        assert isinstance(d["id"], str)

    def test_handles_none_estimated_value(self):
        lead = self._make_lead(estimated_value=None)
        d = lead_to_dict(lead)

        assert d["estimated_value"] is None

    def test_handles_none_timestamps(self):
        lead = self._make_lead(created_at=None, updated_at=None)
        d = lead_to_dict(lead)

        assert d["created_at"] is None
        assert d["updated_at"] is None


class TestConvoToDict:
    def test_includes_lead_when_provided(self):
        convo = MagicMock()
        convo.id = uuid.uuid4()
        convo.business_id = uuid.uuid4()
        convo.lead_id = uuid.uuid4()
        convo.call_id = None
        convo.status = "active"
        convo.follow_up_count = 0
        convo.next_follow_up_at = None
        convo.qualification_data = {}
        convo.created_at = datetime.utcnow()
        convo.updated_at = datetime.utcnow()

        lead = MagicMock()
        lead.id = uuid.uuid4()
        lead.business_id = uuid.uuid4()
        lead.phone = "+15551234567"
        lead.name = "Test"
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

        d = convo_to_dict(convo, lead=lead)

        assert "lead" in d
        assert d["lead"]["phone"] == "+15551234567"

    def test_omits_lead_when_not_provided(self):
        convo = MagicMock()
        convo.id = uuid.uuid4()
        convo.business_id = uuid.uuid4()
        convo.lead_id = uuid.uuid4()
        convo.call_id = None
        convo.status = "active"
        convo.follow_up_count = 0
        convo.next_follow_up_at = None
        convo.qualification_data = {}
        convo.created_at = datetime.utcnow()
        convo.updated_at = datetime.utcnow()

        d = convo_to_dict(convo)

        assert "lead" not in d


class TestCallToDict:
    def test_serializes_call(self):
        call = MagicMock()
        call.id = uuid.uuid4()
        call.business_id = uuid.uuid4()
        call.twilio_call_sid = "CA123"
        call.caller_phone = "+15551234567"
        call.status = "missed"
        call.duration_seconds = None
        call.is_after_hours = True
        call.recording_url = None
        call.transcription = None
        call.created_at = datetime(2026, 2, 16, 14, 30)

        d = call_to_dict(call)

        assert d["status"] == "missed"
        assert d["is_after_hours"] is True
        assert d["caller_phone"] == "+15551234567"


class TestActivityToDict:
    def test_call_activity(self):
        call = MagicMock()
        call.id = uuid.uuid4()
        call.status = "missed"
        call.caller_phone = "+15551234567"
        call.created_at = datetime(2026, 2, 16, 14, 30)

        d = activity_to_dict("call", call)

        assert d["type"] == "call"
        assert "Missed" in d["description"]

    def test_message_activity(self):
        msg = MagicMock()
        msg.id = uuid.uuid4()
        msg.direction = "inbound"
        msg.sender_type = "caller"
        msg.body = "My AC is broken"
        msg.created_at = datetime(2026, 2, 16, 14, 30)

        d = activity_to_dict("message", msg)

        assert d["type"] == "message"
        assert "Received" in d["description"]
        assert d["body_preview"] == "My AC is broken"

    def test_message_body_truncated(self):
        msg = MagicMock()
        msg.id = uuid.uuid4()
        msg.direction = "outbound"
        msg.sender_type = "ai"
        msg.body = "x" * 100
        msg.created_at = datetime.utcnow()

        d = activity_to_dict("message", msg)

        assert d["body_preview"].endswith("...")
        assert len(d["body_preview"]) <= 84

    def test_lead_activity(self):
        lead = MagicMock()
        lead.id = uuid.uuid4()
        lead.status = "qualified"
        lead.name = "Sarah M."
        lead.phone = "+15551234567"
        lead.updated_at = datetime.utcnow()

        d = activity_to_dict("lead", lead)

        assert d["type"] == "lead"
        assert "Sarah M." in d["description"]

    def test_unknown_type_returns_empty(self):
        d = activity_to_dict("unknown", MagicMock())
        assert d == {}


class TestApptToDict:
    def test_serializes_appointment(self):
        appt = MagicMock()
        appt.id = uuid.uuid4()
        appt.business_id = uuid.uuid4()
        appt.lead_id = uuid.uuid4()
        appt.conversation_id = None
        appt.scheduled_date = date(2026, 2, 17)
        appt.scheduled_time = time(14, 0)
        appt.duration_minutes = 60
        appt.service_type = "AC Repair"
        appt.address = "123 Main St"
        appt.status = "scheduled"
        appt.notes = None
        appt.created_at = datetime.utcnow()
        appt.updated_at = datetime.utcnow()

        d = appt_to_dict(appt)

        assert d["scheduled_date"] == "2026-02-17"
        assert d["scheduled_time"] == "14:00:00"
        assert d["service_type"] == "AC Repair"


class TestMetricToDict:
    def test_serializes_metric(self):
        m = MagicMock()
        m.id = uuid.uuid4()
        m.date = date(2026, 2, 16)
        m.total_calls = 12
        m.missed_calls = 4
        m.recovered_calls = 3
        m.leads_captured = 3
        m.leads_qualified = 2
        m.appointments_booked = 1
        m.estimated_revenue = Decimal("700.00")
        m.messages_sent = 15
        m.messages_received = 10

        d = metric_to_dict(m)

        assert d["total_calls"] == 12
        assert d["estimated_revenue"] == 700.0
        assert d["date"] == "2026-02-16"
