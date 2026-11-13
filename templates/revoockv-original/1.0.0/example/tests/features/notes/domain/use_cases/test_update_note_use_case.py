from example_app.core.domain.entities.result import Failure
from example_app.features.notes.domain.use_cases.update_note_use_case import UpdateNoteUseCase
from tests.features.notes.fakes import FakeNotesRepository


async def test_trims_text() -> None:
    repository = FakeNotesRepository()

    await UpdateNoteUseCase(repository)(note_id="1", text=" new ")

    assert repository.calls == [("update", {"note_id": "1", "text": "new"})]


async def test_refuses_blank_text() -> None:
    repository = FakeNotesRepository()

    result = await UpdateNoteUseCase(repository)(note_id="1", text="")

    assert result == Failure("Note text must not be empty")
    assert repository.calls == []
