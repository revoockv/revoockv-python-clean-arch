"""Note entity."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Note:
    """A note the user wrote; ``updated_at`` equals ``created_at`` until it is edited."""

    id: str
    text: str
    created_at: datetime
    updated_at: datetime
