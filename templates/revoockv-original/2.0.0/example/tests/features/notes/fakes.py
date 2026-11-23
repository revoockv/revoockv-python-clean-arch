from datetime import UTC, datetime

from example_app.core.domain.entities.result import Result, Success
from example_app.features.notes.domain.entities.note import Note
from example_app.features.notes.domain.repositories.notes_repository import NotesRepository

MOMENT = datetime(2026, 11, 13, tzinfo=UTC)


class FakeNotesRepository(NotesRepository):
    """Records the calls; ``result`` is returned by add and update."""

    def __init__(self, result: Result[Note] | None = None) -> None:
        self.result = result or Success(
            Note(id="1", text="x", created_at=MOMENT, updated_at=MOMENT)
        )
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def list_notes(self) -> Result[tuple[Note, ...]]:
        return Success(())

    async def add_note(self, *, text: str) -> Result[Note]:
        self.calls.append(("add", {"text": text}))
        return self.result

    async def update_note(self, *, note_id: str, text: str) -> Result[Note]:
        self.calls.append(("update", {"note_id": note_id, "text": text}))
        return self.result

    async def delete_note(self, *, note_id: str) -> Result[None]:
        self.calls.append(("delete", {"note_id": note_id}))
        return Success(None)
