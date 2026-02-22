"""Abstract base class for calendar providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    id: str
    title: str
    start: datetime
    end: datetime
    all_day: bool = False


class CalendarProvider(ABC):
    """Abstract interface for calendar providers (Google, Outlook, etc.)."""

    @abstractmethod
    async def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Generate the OAuth authorization URL."""
        ...

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange an authorization code for tokens.

        Returns: {"access_token": str, "refresh_token": str, "expires_at": datetime}
        """
        ...

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token.

        Returns: {"access_token": str, "expires_at": datetime}
        """
        ...

    @abstractmethod
    async def get_busy_times(
        self,
        access_token: str,
        calendar_id: str,
        date_from: date,
        date_to: date,
    ) -> list[CalendarEvent]:
        """Get busy time periods from the calendar."""
        ...

    @abstractmethod
    async def create_event(
        self,
        access_token: str,
        calendar_id: str,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
    ) -> CalendarEvent:
        """Create a new calendar event."""
        ...

    @abstractmethod
    async def delete_event(
        self,
        access_token: str,
        calendar_id: str,
        event_id: str,
    ) -> bool:
        """Delete a calendar event."""
        ...
