from datetime import UTC, datetime

from example_app.features.notes.data.models.note_model import NoteModel
from example_app.features.notes.domain.entities.note import Note


def test_row_and_entity_round_trips() -> None:
    moment = datetime(2026, 11, 13, 9, 0, tzinfo=UTC)
    note = Note(id="1", text="Buy milk", created_at=moment, updated_at=moment)

    model = NoteModel.from_entity(note)

    assert NoteModel.from_row(model.to_row()) == model
    assert model.to_entity() == note
