"""Note response body."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel

from example_app.features.notes.domain.entities.note import Note


class NoteResponse(BaseModel):
    """Public representation of a note."""

    id: str
    text: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Note) -> Self:
        """Build the response from a domain entity."""
        return cls(
            id=entity.id,
            text=entity.text,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
