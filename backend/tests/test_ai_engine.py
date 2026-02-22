"""Tests for AI conversation engine."""
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_engine import build_system_prompt, check_business_hours


class TestBuildSystemPrompt:
    """Tests for system prompt generation."""

    def _make_business(self, **overrides):
        biz = MagicMock()
        biz.name = "Smith's Heating & Air"
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
        biz.ai_instructions = None
        for k, v in overrides.items():
            setattr(biz, k, v)
        return biz

    def _make_lead(self, **overrides):
        lead = MagicMock()
        lead.name = None
        lead.service_needed = None
        lead.urgency = None
        lead.address = None
        for k, v in overrides.items():
            setattr(lead, k, v)
        return lead

    def test_prompt_includes_business_name(self):
        biz = self._make_business()
        lead = self._make_lead()
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "Smith's Heating & Air" in prompt

    def test_prompt_includes_services(self):
        biz = self._make_business()
        lead = self._make_lead()
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "AC Repair" in prompt
        assert "Heating" in prompt
        assert "Maintenance" in prompt

    def test_prompt_includes_lead_info_when_known(self):
        biz = self._make_business()
        lead = self._make_lead(name="Sarah", service_needed="AC not cooling")
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "Sarah" in prompt
        assert "AC not cooling" in prompt

    def test_prompt_shows_unknown_for_missing_lead_info(self):
        biz = self._make_business()
        lead = self._make_lead()
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "Unknown" in prompt

    def test_prompt_includes_custom_instructions(self):
        biz = self._make_business(ai_instructions="Always mention our 24/7 emergency line")
        lead = self._make_lead()
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "24/7 emergency line" in prompt

    def test_prompt_omits_instructions_when_none(self):
        biz = self._make_business(ai_instructions=None)
        lead = self._make_lead()
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "ADDITIONAL INSTRUCTIONS" not in prompt

    def test_prompt_contains_qualification_signals(self):
        biz = self._make_business()
        lead = self._make_lead()
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "[QUALIFIED]" in prompt
        assert "[HUMAN_NEEDED]" in prompt
        assert "[EMERGENCY]" in prompt

    def test_prompt_includes_empty_services_fallback(self):
        biz = self._make_business(services=[])
        lead = self._make_lead()
        convo = MagicMock()

        prompt = build_system_prompt(biz, lead, convo)

        assert "HVAC Services" in prompt


class TestCheckBusinessHours:
    """Tests for business hours checking."""

    def _make_business(self):
        biz = MagicMock()
        biz.business_hours = {
            "monday": {"open": "08:00", "close": "17:00"},
            "tuesday": {"open": "08:00", "close": "17:00"},
            "wednesday": {"open": "08:00", "close": "17:00"},
            "thursday": {"open": "08:00", "close": "17:00"},
            "friday": {"open": "08:00", "close": "17:00"},
            "saturday": None,
            "sunday": None,
        }
        return biz

    def test_within_hours_returns_true(self):
        biz = self._make_business()
        # Monday at 10:00 AM
        test_time = datetime(2026, 2, 16, 10, 0, 0)  # This is a Monday

        result = check_business_hours(biz, test_time)

        assert result is True

    def test_before_hours_returns_false(self):
        biz = self._make_business()
        # Monday at 6:00 AM
        test_time = datetime(2026, 2, 16, 6, 0, 0)

        result = check_business_hours(biz, test_time)

        assert result is False

    def test_after_hours_returns_false(self):
        biz = self._make_business()
        # Monday at 8:00 PM
        test_time = datetime(2026, 2, 16, 20, 0, 0)

        result = check_business_hours(biz, test_time)

        assert result is False

    def test_weekend_returns_false(self):
        biz = self._make_business()
        # Sunday at noon
        test_time = datetime(2026, 2, 15, 12, 0, 0)  # This is a Sunday

        result = check_business_hours(biz, test_time)

        assert result is False

    def test_at_closing_time_returns_true(self):
        biz = self._make_business()
        # Monday at exactly 5:00 PM
        test_time = datetime(2026, 2, 16, 17, 0, 0)

        result = check_business_hours(biz, test_time)

        assert result is True

    def test_at_opening_time_returns_true(self):
        biz = self._make_business()
        # Monday at exactly 8:00 AM
        test_time = datetime(2026, 2, 16, 8, 0, 0)

        result = check_business_hours(biz, test_time)

        assert result is True
