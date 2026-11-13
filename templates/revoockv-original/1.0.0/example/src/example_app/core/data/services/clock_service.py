"""Clock service: the only source of the current time."""

from datetime import UTC, datetime


class ClockService:
    """Returns the current UTC time; tests pass a subclass with a fixed time."""

    def now(self) -> datetime:
        """Return the current time in UTC."""
        return datetime.now(UTC)
