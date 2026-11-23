"""Note facts entity: what the statistics need to know about one note."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NoteFacts:
    """Word count and timestamps of one note."""

    words: int
    created_at: datetime
    updated_at: datetime
