"""Delete note use case."""

from example_app.core.domain.entities.result import Result
from example_app.features.notes.domain.repositories.notes_repository import NotesRepository


class DeleteNoteUseCase:
    """Deletes a note."""

    def __init__(self, repository: NotesRepository) -> None:
        self._repository = repository

    async def __call__(self, *, note_id: str) -> Result[None]:
        """Delete the note ``note_id``."""
        return await self._repository.delete_note(note_id=note_id)
