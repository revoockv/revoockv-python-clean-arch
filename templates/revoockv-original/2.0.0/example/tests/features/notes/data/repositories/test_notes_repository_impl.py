import logging
from datetime import timedelta

from example_app.core.data.data_sources.in_memory_database_data_source import (
    InMemoryDatabaseDataSource,
)
from example_app.core.domain.entities.result import Failure, Success
from example_app.features.notes.data.data_sources.database_notes_data_source import (
    DatabaseNotesDataSource,
)
from example_app.features.notes.data.repositories.notes_repository_impl import NotesRepositoryImpl
from example_app.features.notes.domain.entities.note_failure import NoteFailure
from tests.conftest import FixedClockService


def _repository(clock: FixedClockService) -> NotesRepositoryImpl:
    data_source = DatabaseNotesDataSource(database=InMemoryDatabaseDataSource(), clock=clock)
    return NotesRepositoryImpl(data_source=data_source, logger=logging.getLogger("test"))


async def test_add_list_update_delete(clock: FixedClockService) -> None:
    repository = _repository(clock)
    match await repository.add_note(text="first"):
        case Success(first):
            pass
        case Failure(failure):
            raise AssertionError(failure)
    clock.moment += timedelta(minutes=1)
    await repository.add_note(text="second")

    match await repository.list_notes():
        case Success(notes):
            assert [n.text for n in notes] == ["second", "first"]
        case Failure(failure):
            raise AssertionError(failure)

    match await repository.update_note(note_id=first.id, text="edited"):
        case Success(updated):
            assert updated.text == "edited"
            assert updated.updated_at > updated.created_at
        case Failure(failure):
            raise AssertionError(failure)

    assert await repository.delete_note(note_id=first.id) == Success(None)


async def test_unknown_id_becomes_failure(clock: FixedClockService) -> None:
    repository = _repository(clock)

    assert await repository.update_note(note_id="missing", text="x") == Failure(
        NoteFailure.NOT_FOUND
    )
    assert await repository.delete_note(note_id="missing") == Failure(NoteFailure.NOT_FOUND)
