"""Notes repository implementation."""

import logging

from example_app.core.data.data_sources.database_data_source import RowNotFoundError
from example_app.core.domain.entities.result import Failure, Result, Success
from example_app.features.notes.data.data_sources.notes_data_source import NotesDataSource
from example_app.features.notes.domain.entities.note import Note
from example_app.features.notes.domain.entities.note_failure import NoteFailure
from example_app.features.notes.domain.repositories.notes_repository import NotesRepository


class NotesRepositoryImpl(NotesRepository):
    """``NotesRepository`` over a ``NotesDataSource``; turns exceptions into ``NoteFailure``."""

    def __init__(self, *, data_source: NotesDataSource, logger: logging.Logger) -> None:
        self._data_source = data_source
        self._logger = logger

    async def list_notes(self) -> Result[tuple[Note, ...], NoteFailure]:
        """Read the notes and map them to entities."""
        try:
            models = await self._data_source.list_notes()
        except Exception as e:
            self._logger.error("ListNotes: failure — %s", e)
            return Failure(NoteFailure.STORAGE)
        self._logger.info("ListNotes: success — %d note(s)", len(models))
        return Success(tuple(model.to_entity() for model in models))

    async def add_note(self, *, text: str) -> Result[Note, NoteFailure]:
        """Store a new note."""
        try:
            model = await self._data_source.add_note(text=text)
        except Exception as e:
            self._logger.error("AddNote: failure — %s", e)
            return Failure(NoteFailure.STORAGE)
        self._logger.info("AddNote: success — note %s added", model.id)
        return Success(model.to_entity())

    async def update_note(self, *, note_id: str, text: str) -> Result[Note, NoteFailure]:
        """Change the text of a note."""
        try:
            model = await self._data_source.update_note(note_id=note_id, text=text)
        except RowNotFoundError:
            self._logger.warning("UpdateNote: failure — no note %s", note_id)
            return Failure(NoteFailure.NOT_FOUND)
        except Exception as e:
            self._logger.error("UpdateNote: failure — %s", e)
            return Failure(NoteFailure.STORAGE)
        self._logger.info("UpdateNote: success — note %s updated", note_id)
        return Success(model.to_entity())

    async def delete_note(self, *, note_id: str) -> Result[None, NoteFailure]:
        """Delete a note."""
        try:
            await self._data_source.delete_note(note_id=note_id)
        except RowNotFoundError:
            self._logger.warning("DeleteNote: failure — no note %s", note_id)
            return Failure(NoteFailure.NOT_FOUND)
        except Exception as e:
            self._logger.error("DeleteNote: failure — %s", e)
            return Failure(NoteFailure.STORAGE)
        self._logger.info("DeleteNote: success — note %s deleted", note_id)
        return Success(None)
