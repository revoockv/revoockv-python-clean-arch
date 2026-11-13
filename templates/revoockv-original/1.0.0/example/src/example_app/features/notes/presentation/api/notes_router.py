"""HTTP routes of the notes feature."""

from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from example_app.core.domain.entities.result import Failure, Success
from example_app.features.notes.presentation.api.schemas.note_response import NoteResponse
from example_app.features.notes.presentation.api.schemas.note_text_request import NoteTextRequest
from example_app.features.notes.presentation.di.notes_getters import (
    add_note_use_case,
    delete_note_use_case,
    list_notes_use_case,
    update_note_use_case,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("")
async def list_notes() -> list[NoteResponse]:
    """Return every note, newest first; 500 with the error message on failure."""
    match await list_notes_use_case()():
        case Success(notes):
            return [NoteResponse.from_entity(note) for note in notes]
        case Failure(error):
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error)


@router.post("", status_code=HTTPStatus.CREATED)
async def add_note(body: NoteTextRequest) -> NoteResponse:
    """Add a note; 422 with the error message when it is refused."""
    match await add_note_use_case()(text=body.text):
        case Success(note):
            return NoteResponse.from_entity(note)
        case Failure(error):
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=error)


@router.put("/{note_id}")
async def update_note(note_id: str, body: NoteTextRequest) -> NoteResponse:
    """Replace the text of a note; 422 with the error message when it is refused."""
    match await update_note_use_case()(note_id=note_id, text=body.text):
        case Success(note):
            return NoteResponse.from_entity(note)
        case Failure(error):
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=error)


@router.delete("/{note_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_note(note_id: str) -> None:
    """Delete a note; 404 with the error message on failure."""
    match await delete_note_use_case()(note_id=note_id):
        case Success():
            return
        case Failure(error):
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=error)
