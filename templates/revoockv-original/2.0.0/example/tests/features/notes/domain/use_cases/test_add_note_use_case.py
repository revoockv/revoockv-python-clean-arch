from example_app.core.domain.entities.result import Failure
from example_app.features.notes.domain.entities.note_failure import NoteFailure
from example_app.features.notes.domain.use_cases.add_note_use_case import AddNoteUseCase
from tests.features.notes.fakes import FakeNotesRepository


async def test_trims_text_and_passes_the_repository_result() -> None:
    repository = FakeNotesRepository()

    result = await AddNoteUseCase(repository)(text="  Buy milk ")

    assert result == repository.result
    assert repository.calls == [("add", {"text": "Buy milk"})]


async def test_refuses_blank_text_without_calling_the_repository() -> None:
    repository = FakeNotesRepository()

    result = await AddNoteUseCase(repository)(text="   ")

    assert result == Failure(NoteFailure.EMPTY_TEXT)
    assert repository.calls == []
