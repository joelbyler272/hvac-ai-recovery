"""Google Calendar provider implementation."""
import logging
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.services.calendar.base import CalendarProvider, CalendarEvent

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar integration via OAuth 2.0 + Calendar API."""

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret

    async def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": expires_at,
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
        return {
            "access_token": data["access_token"],
            "expires_at": expires_at,
        }

    async def get_busy_times(
        self,
        access_token: str,
        calendar_id: str,
        date_from: date,
        date_to: date,
    ) -> list[CalendarEvent]:
        time_min = datetime.combine(date_from, datetime.min.time()).isoformat() + "Z"
        time_max = datetime.combine(date_to, datetime.max.time()).isoformat() + "Z"

        cal_id = calendar_id or "primary"

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GOOGLE_CALENDAR_API}/calendars/{cal_id}/events",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": 250,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        events = []
        for item in data.get("items", []):
            # Skip cancelled events
            if item.get("status") == "cancelled":
                continue

            start = item.get("start", {})
            end = item.get("end", {})

            all_day = "date" in start
            if all_day:
                start_dt = datetime.fromisoformat(start["date"])
                end_dt = datetime.fromisoformat(end["date"])
            else:
                start_dt = datetime.fromisoformat(start.get("dateTime", ""))
                end_dt = datetime.fromisoformat(end.get("dateTime", ""))

            events.append(CalendarEvent(
                id=item["id"],
                title=item.get("summary", "Busy"),
                start=start_dt,
                end=end_dt,
                all_day=all_day,
            ))

        return events

    async def create_event(
        self,
        access_token: str,
        calendar_id: str,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
    ) -> CalendarEvent:
        cal_id = calendar_id or "primary"
        body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GOOGLE_CALENDAR_API}/calendars/{cal_id}/events",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        return CalendarEvent(
            id=data["id"],
            title=data.get("summary", title),
            start=start,
            end=end,
        )

    async def delete_event(
        self,
        access_token: str,
        calendar_id: str,
        event_id: str,
    ) -> bool:
        cal_id = calendar_id or "primary"
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{GOOGLE_CALENDAR_API}/calendars/{cal_id}/events/{event_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return resp.status_code in (200, 204)
