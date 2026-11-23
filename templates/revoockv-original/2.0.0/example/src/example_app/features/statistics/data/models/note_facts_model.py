"""Note facts DTO, read from a row of the ``notes`` table."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from example_app.core.data.data_sources.database_data_source import Row
from example_app.features.statistics.domain.entities.note_facts import NoteFacts


@dataclass(frozen=True, slots=True)
class NoteFactsModel:
    """Word count and ISO timestamps of one stored note, mapped to and from ``NoteFacts``."""

    words: int
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: Row) -> Self:
        """Build the model from a ``notes`` row (words are counted from its text)."""
        return cls(
            words=len(str(row["text"]).split()),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @classmethod
    def from_entity(cls, entity: NoteFacts) -> Self:
        """Build the model from a domain entity."""
        return cls(
            words=entity.words,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat(),
        )

    def to_entity(self) -> NoteFacts:
        """Map the model to a domain entity."""
        return NoteFacts(
            words=self.words,
            created_at=datetime.fromisoformat(self.created_at),
            updated_at=datetime.fromisoformat(self.updated_at),
        )
