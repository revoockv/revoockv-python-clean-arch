"""Notes statistics entity."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Self

from example_app.features.statistics.domain.entities.note_facts import NoteFacts


@dataclass(frozen=True, slots=True)
class NotesStatistics:
    """Numbers over every note: count, words, added today and edited."""

    notes: int
    words: int
    added_today: int
    edited: int

    @classmethod
    def of(cls, facts: Iterable[NoteFacts], *, now: datetime) -> Self:
        """Count the statistics of ``facts``; "today" is the date of ``now``."""
        items = tuple(facts)
        return cls(
            notes=len(items),
            words=sum(fact.words for fact in items),
            added_today=sum(1 for fact in items if fact.created_at.date() == now.date()),
            edited=sum(1 for fact in items if fact.updated_at != fact.created_at),
        )
