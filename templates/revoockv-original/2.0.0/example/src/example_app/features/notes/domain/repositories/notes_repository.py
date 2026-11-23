"""Notes repository contract."""

from abc import ABC, abstractmethod

from example_app.core.domain.entities.result import Result
from example_app.features.notes.domain.entities.note import Note
from example_app.features.notes.domain.entities.note_failure import NoteFailure


class NotesRepository(ABC):
    """Reads and changes the user's notes."""

    @abstractmethod
    async def list_notes(self) -> Result[tuple[Note, ...], NoteFailure]:
        """Return every note, newest first."""

    @abstractmethod
    async def add_note(self, *, text: str) -> Result[Note, NoteFailure]:
        """Store a new note with ``text``."""

    @abstractmethod
    async def update_note(self, *, note_id: str, text: str) -> Result[Note, NoteFailure]:
        """Replace the text of the note ``note_id``; ``NOT_FOUND`` when there is none."""

    @abstractmethod
    async def delete_note(self, *, note_id: str) -> Result[None, NoteFailure]:
        """Remove the note ``note_id``; ``NOT_FOUND`` when there is none."""
