"""HTTP routes of the notes feature."""

from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from example_app.core.domain.entities.result import Failure, Success
from example_app.core.presentation.api.failure_status import FailureStatus
from example_app.features.notes.domain.entities.note_failure import NoteFailure
from example_app.features.notes.presentation.api.schemas.note_response import NoteResponse
from example_app.features.notes.presentation.api.schemas.note_text_request import NoteTextRequest
from example_app.features.notes.presentation.di.notes_getters import (
    add_note_use_case,
    delete_note_use_case,
    list_notes_use_case,
    update_note_use_case,
)
from example_app.features.notes.presentation.text.note_failure_text import NoteFailureText

router = APIRouter(prefix="/notes", tags=["notes"])


def _http_error(failure: NoteFailure) -> HTTPException:
    """Return the HTTP error that answers ``failure``: its status and its text."""
    return HTTPException(
        status_code=FailureStatus.of(failure.kind), detail=NoteFailureText.of(failure)
    )


@router.get("")
async def list_notes() -> list[NoteResponse]:
    """Return every note, newest first."""
    match await list_notes_use_case()():
        case Success(notes):
            return [NoteResponse.from_entity(note) for note in notes]
        case Failure(failure):
            raise _http_error(failure)


@router.post("", status_code=HTTPStatus.CREATED)
async def add_note(body: NoteTextRequest) -> NoteResponse:
    """Add a note; 422 when the text is blank."""
    match await add_note_use_case()(text=body.text):
        case Success(note):
            return NoteResponse.from_entity(note)
        case Failure(failure):
            raise _http_error(failure)


@router.put("/{note_id}")
async def update_note(note_id: str, body: NoteTextRequest) -> NoteResponse:
    """Replace the text of a note; 422 when the text is blank, 404 when there is no such note."""
    match await update_note_use_case()(note_id=note_id, text=body.text):
        case Success(note):
            return NoteResponse.from_entity(note)
        case Failure(failure):
            raise _http_error(failure)


@router.delete("/{note_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_note(note_id: str) -> None:
    """Delete a note; 404 when there is no such note."""
    match await delete_note_use_case()(note_id=note_id):
        case Success():
            return
        case Failure(failure):
            raise _http_error(failure)
