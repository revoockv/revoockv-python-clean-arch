"""Notes data source contract."""

from abc import ABC, abstractmethod

from example_app.features.notes.data.models.note_model import NoteModel


class NotesDataSource(ABC):
    """Stores notes. May raise; the repository converts errors to ``Failure``."""

    @abstractmethod
    async def list_notes(self) -> list[NoteModel]:
        """Return every stored note, newest first."""

    @abstractmethod
    async def add_note(self, *, text: str) -> NoteModel:
        """Store a new note and return it with its id and timestamps."""

    @abstractmethod
    async def update_note(self, *, note_id: str, text: str) -> NoteModel:
        """Replace the text of ``note_id`` and return the changed note."""

    @abstractmethod
    async def delete_note(self, *, note_id: str) -> None:
        """Remove ``note_id``."""
