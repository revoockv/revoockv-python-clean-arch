"""Note DTO: a row of the ``notes`` table."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from example_app.core.data.data_sources.database_data_source import Row
from example_app.features.notes.domain.entities.note import Note


@dataclass(frozen=True, slots=True)
class NoteModel:
    """Storage representation of a note (ISO timestamps), mapped to and from ``Note``."""

    id: str
    text: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: Row) -> Self:
        """Build the model from a database row."""
        return cls(
            id=str(row["id"]),
            text=str(row["text"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def to_row(self) -> Row:
        """Serialize the model to a database row."""
        return {
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_entity(cls, entity: Note) -> Self:
        """Build the model from a domain entity."""
        return cls(
            id=entity.id,
            text=entity.text,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat(),
        )

    def to_entity(self) -> Note:
        """Map the model to a domain entity."""
        return Note(
            id=self.id,
            text=self.text,
            created_at=datetime.fromisoformat(self.created_at),
            updated_at=datetime.fromisoformat(self.updated_at),
        )
