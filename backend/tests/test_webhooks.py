"""Tests for Twilio webhook endpoints."""
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_check_version():
    response = client.get("/health")
    assert response.json()["version"] == "1.0.0"


class TestVoiceIncoming:
    """Tests for POST /webhook/voice/incoming."""

    @patch("app.api.webhooks.voice.get_business_by_twilio_number")
    def test_unknown_number_returns_error_twiml(self, mock_get_biz):
        mock_get_biz.return_value = None

        response = client.post(
            "/webhook/voice/incoming",
            data={"From": "+15551234567", "To": "+15550001111", "CallSid": "CA123"},
        )

        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "not configured" in response.text

    @patch("app.api.webhooks.voice.schedule_follow_up")
    @patch("app.api.webhooks.voice.notify_owner")
    @patch("app.api.webhooks.voice.send_sms")
    @patch("app.api.webhooks.voice.create_conversation")
    @patch("app.api.webhooks.voice.create_or_get_lead")
    @patch("app.api.webhooks.voice.get_active_conversation")
    @patch("app.api.webhooks.voice.is_opted_out")
    @patch("app.api.webhooks.voice.update_call")
    @patch("app.api.webhooks.voice.get_call")
    @patch("app.api.webhooks.voice.get_business_by_twilio_number")
    @patch("app.api.webhooks.voice.create_call_record")
    @patch("app.api.webhooks.voice.is_after_hours")
    def test_incoming_call_returns_dial_twiml(
        self, mock_after_hrs, mock_create_call, mock_get_biz,
        mock_get_call, mock_update_call, mock_opted_out,
        mock_get_convo, mock_create_lead, mock_create_convo,
        mock_send_sms, mock_notify, mock_schedule,
    ):
        biz = MagicMock()
        biz.id = uuid.uuid4()
        biz.business_phone = "+15559876543"
        biz.name = "Test HVAC"
        mock_get_biz.return_value = biz
        mock_after_hrs.return_value = False

        call = MagicMock()
        call.id = uuid.uuid4()
        mock_create_call.return_value = call

        response = client.post(
            "/webhook/voice/incoming",
            data={"From": "+15551234567", "To": "+15550001111", "CallSid": "CA123"},
        )

        assert response.status_code == 200
        assert "<Dial" in response.text
        assert biz.business_phone in response.text


class TestCallCompleted:
    """Tests for POST /webhook/voice/call-completed."""

    @patch("app.api.webhooks.voice.get_business_by_twilio_number")
    @patch("app.api.webhooks.voice.get_call")
    @patch("app.api.webhooks.voice.update_call")
    def test_answered_call_updates_status(self, mock_update, mock_get_call, mock_get_biz):
        call = MagicMock()
        call.id = uuid.uuid4()
        call.business_id = uuid.uuid4()
        mock_get_call.return_value = call

        biz = MagicMock()
        biz.id = call.business_id
        mock_get_biz.return_value = biz

        response = client.post(
            "/webhook/voice/call-completed",
            params={"call_id": str(call.id)},
            data={
                "DialCallStatus": "completed",
                "DialCallDuration": "45",
                "From": "+15551234567",
                "To": "+15550001111",
            },
        )

        assert response.status_code == 200
        mock_update.assert_called_once()

    @patch("app.api.webhooks.voice.schedule_follow_up")
    @patch("app.api.webhooks.voice.notify_owner")
    @patch("app.api.webhooks.voice.send_sms")
    @patch("app.api.webhooks.voice.create_conversation")
    @patch("app.api.webhooks.voice.create_or_get_lead")
    @patch("app.api.webhooks.voice.get_active_conversation")
    @patch("app.api.webhooks.voice.is_opted_out")
    @patch("app.api.webhooks.voice.update_call")
    @patch("app.api.webhooks.voice.get_call")
    @patch("app.api.webhooks.voice.get_business_by_twilio_number")
    def test_missed_call_triggers_sms(
        self, mock_get_biz, mock_get_call, mock_update_call,
        mock_opted_out, mock_get_convo, mock_create_lead,
        mock_create_convo, mock_send_sms, mock_notify, mock_schedule,
    ):
        call = MagicMock()
        call.id = uuid.uuid4()
        call.business_id = uuid.uuid4()
        call.is_after_hours = False
        mock_get_call.return_value = call

        biz = MagicMock()
        biz.id = call.business_id
        biz.name = "Test HVAC"
        biz.ai_greeting = None
        biz.twilio_number = "+15550001111"
        mock_get_biz.return_value = biz

        mock_opted_out.return_value = False
        mock_get_convo.return_value = None

        lead = MagicMock()
        lead.id = uuid.uuid4()
        mock_create_lead.return_value = lead

        convo = MagicMock()
        convo.id = uuid.uuid4()
        mock_create_convo.return_value = convo

        response = client.post(
            "/webhook/voice/call-completed",
            params={"call_id": str(call.id)},
            data={
                "DialCallStatus": "no-answer",
                "From": "+15551234567",
                "To": "+15550001111",
            },
        )

        assert response.status_code == 200
        assert "text you right away" in response.text
        mock_send_sms.assert_called_once()
        mock_notify.assert_called_once()
        mock_schedule.assert_called_once()

    @patch("app.api.webhooks.voice.update_call")
    @patch("app.api.webhooks.voice.get_call")
    @patch("app.api.webhooks.voice.get_business_by_twilio_number")
    @patch("app.api.webhooks.voice.is_opted_out")
    def test_opted_out_caller_not_texted(
        self, mock_opted_out, mock_get_biz, mock_get_call, mock_update,
    ):
        call = MagicMock()
        call.id = uuid.uuid4()
        call.business_id = uuid.uuid4()
        mock_get_call.return_value = call

        biz = MagicMock()
        biz.id = call.business_id
        mock_get_biz.return_value = biz

        mock_opted_out.return_value = True

        response = client.post(
            "/webhook/voice/call-completed",
            params={"call_id": str(call.id)},
            data={
                "DialCallStatus": "no-answer",
                "From": "+15551234567",
                "To": "+15550001111",
            },
        )

        assert response.status_code == 200
        assert "missed your call" in response.text


class TestSmsIncoming:
    """Tests for POST /webhook/sms/incoming."""

    @patch("app.api.webhooks.sms.get_business_by_twilio_number")
    def test_unknown_number_returns_200(self, mock_get_biz):
        mock_get_biz.return_value = None

        response = client.post(
            "/webhook/sms/incoming",
            data={"From": "+15551234567", "To": "+15550001111", "Body": "Hello"},
        )

        assert response.status_code == 200

    @patch("app.api.webhooks.sms.handle_opt_out")
    @patch("app.api.webhooks.sms.get_business_by_twilio_number")
    def test_stop_keyword_triggers_opt_out(self, mock_get_biz, mock_opt_out):
        biz = MagicMock()
        biz.id = uuid.uuid4()
        biz.name = "Test HVAC"
        mock_get_biz.return_value = biz

        response = client.post(
            "/webhook/sms/incoming",
            data={"From": "+15551234567", "To": "+15550001111", "Body": "STOP"},
        )

        assert response.status_code == 200
        assert "unsubscribed" in response.text
        mock_opt_out.assert_called_once()

    @patch("app.api.webhooks.sms.handle_opt_in")
    @patch("app.api.webhooks.sms.get_business_by_twilio_number")
    def test_start_keyword_triggers_opt_in(self, mock_get_biz, mock_opt_in):
        biz = MagicMock()
        biz.id = uuid.uuid4()
        biz.name = "Test HVAC"
        mock_get_biz.return_value = biz

        response = client.post(
            "/webhook/sms/incoming",
            data={"From": "+15551234567", "To": "+15550001111", "Body": "START"},
        )

        assert response.status_code == 200
        assert "Welcome back" in response.text
        mock_opt_in.assert_called_once()


class TestSmsStatus:
    """Tests for POST /webhook/sms/status."""

    def test_status_callback_returns_200(self):
        response = client.post(
            "/webhook/sms/status",
            data={"MessageSid": "SM123", "MessageStatus": "delivered"},
        )

        assert response.status_code == 200
