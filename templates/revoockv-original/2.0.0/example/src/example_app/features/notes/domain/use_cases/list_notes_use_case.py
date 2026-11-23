"""List notes use case."""

from example_app.core.domain.entities.result import Result
from example_app.features.notes.domain.entities.note import Note
from example_app.features.notes.domain.entities.note_failure import NoteFailure
from example_app.features.notes.domain.repositories.notes_repository import NotesRepository


class ListNotesUseCase:
    """Shows the user's notes, newest first."""

    def __init__(self, repository: NotesRepository) -> None:
        self._repository = repository

    async def __call__(self) -> Result[tuple[Note, ...], NoteFailure]:
        """Return every note, newest first."""
        return await self._repository.list_notes()
