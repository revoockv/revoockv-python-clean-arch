"""Notes data source over the app database."""

import uuid
from dataclasses import replace

from example_app.core.data.data_sources.database_data_source import (
    DatabaseDataSource,
    DatabaseDataSourceError,
)
from example_app.core.data.services.clock_service import ClockService
from example_app.features.notes.data.data_sources.notes_data_source import NotesDataSource
from example_app.features.notes.data.models.note_model import NoteModel


class DatabaseNotesDataSource(NotesDataSource):
    """Keeps notes in the ``notes`` table; creates UUID v4 ids and timestamps from the clock."""

    _TABLE = "notes"
    _UNKNOWN_ID = "notes: no row {note_id}"

    def __init__(self, *, database: DatabaseDataSource, clock: ClockService) -> None:
        self._database = database
        self._clock = clock

    async def list_notes(self) -> list[NoteModel]:
        """Read the table, newest first."""
        models = [NoteModel.from_row(row) for row in await self._database.rows(table=self._TABLE)]
        return sorted(models, key=lambda model: model.created_at, reverse=True)

    async def add_note(self, *, text: str) -> NoteModel:
        """Insert a note with a new id."""
        now = self._clock.now().isoformat()
        model = NoteModel(id=str(uuid.uuid4()), text=text, created_at=now, updated_at=now)
        await self._database.insert(table=self._TABLE, row=model.to_row())
        return model

    async def update_note(self, *, note_id: str, text: str) -> NoteModel:
        """Update the text and ``updated_at`` of ``note_id``."""
        current = next((m for m in await self.list_notes() if m.id == note_id), None)
        if current is None:
            raise DatabaseDataSourceError(self._UNKNOWN_ID.format(note_id=note_id))
        model = replace(current, text=text, updated_at=self._clock.now().isoformat())
        await self._database.update(table=self._TABLE, row=model.to_row())
        return model

    async def delete_note(self, *, note_id: str) -> None:
        """Delete the row ``note_id``."""
        await self._database.delete(table=self._TABLE, row_id=note_id)
