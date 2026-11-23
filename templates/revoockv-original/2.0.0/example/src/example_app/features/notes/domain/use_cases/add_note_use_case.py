"""Add note use case."""

from example_app.core.domain.entities.result import Failure, Result
from example_app.features.notes.domain.entities.note import Note
from example_app.features.notes.domain.repositories.notes_repository import NotesRepository


class AddNoteUseCase:
    """Adds a note; the text is trimmed and must not be blank."""

    _EMPTY_TEXT_ERROR = "Note text must not be empty"

    def __init__(self, repository: NotesRepository) -> None:
        self._repository = repository

    async def __call__(self, *, text: str) -> Result[Note]:
        """Add a note with the trimmed ``text``; fails when it is blank."""
        trimmed = text.strip()
        if not trimmed:
            return Failure(self._EMPTY_TEXT_ERROR)
        return await self._repository.add_note(text=trimmed)
