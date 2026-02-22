"""Microsoft Outlook / Graph API calendar provider implementation."""
import logging
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.services.calendar.base import CalendarProvider, CalendarEvent

logger = logging.getLogger(__name__)

MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_API = "https://graph.microsoft.com/v1.0"

SCOPES = ["Calendars.ReadWrite", "offline_access"]


class OutlookCalendarProvider(CalendarProvider):
    """Microsoft Outlook calendar integration via OAuth 2.0 + Graph API."""

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.microsoft_client_id
        self.client_secret = settings.microsoft_client_secret

    async def get_auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "response_mode": "query",
        }
        return f"{MS_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                MS_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "scope": " ".join(SCOPES),
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
                MS_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": " ".join(SCOPES),
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

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API}/me/calendarView",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "startDateTime": time_min,
                    "endDateTime": time_max,
                    "$top": 250,
                    "$orderby": "start/dateTime",
                    "$select": "id,subject,start,end,isAllDay,showAs",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        events = []
        for item in data.get("value", []):
            # Skip free/tentative events — only count busy/oof
            show_as = item.get("showAs", "busy")
            if show_as in ("free", "tentative"):
                continue

            all_day = item.get("isAllDay", False)
            start_str = item["start"]["dateTime"]
            end_str = item["end"]["dateTime"]

            start_dt = datetime.fromisoformat(start_str.rstrip("Z"))
            end_dt = datetime.fromisoformat(end_str.rstrip("Z"))

            events.append(CalendarEvent(
                id=item["id"],
                title=item.get("subject", "Busy"),
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
        body = {
            "subject": title,
            "body": {"contentType": "text", "content": description},
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_API}/me/events",
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
            title=data.get("subject", title),
            start=start,
            end=end,
        )

    async def delete_event(
        self,
        access_token: str,
        calendar_id: str,
        event_id: str,
    ) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{GRAPH_API}/me/events/{event_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return resp.status_code in (200, 204)
