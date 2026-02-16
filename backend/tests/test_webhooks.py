"""Tests for Twilio webhook endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# TODO: Add webhook tests with mocked Twilio payloads
# def test_voice_incoming():
# def test_call_completed_missed():
# def test_call_completed_answered():
# def test_sms_incoming():
# def test_sms_stop_keyword():
