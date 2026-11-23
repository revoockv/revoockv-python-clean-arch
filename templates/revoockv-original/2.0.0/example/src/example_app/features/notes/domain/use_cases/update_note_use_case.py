"""Update note use case."""

from example_app.core.domain.entities.result import Failure, Result
from example_app.features.notes.domain.entities.note import Note
from example_app.features.notes.domain.repositories.notes_repository import NotesRepository


class UpdateNoteUseCase:
    """Edits a note; the new text is trimmed and must not be blank."""

    _EMPTY_TEXT_ERROR = "Note text must not be empty"

    def __init__(self, repository: NotesRepository) -> None:
        self._repository = repository

    async def __call__(self, *, note_id: str, text: str) -> Result[Note]:
        """Replace the text of ``note_id`` with the trimmed ``text``; fails when it is blank."""
        trimmed = text.strip()
        if not trimmed:
            return Failure(self._EMPTY_TEXT_ERROR)
        return await self._repository.update_note(note_id=note_id, text=trimmed)
