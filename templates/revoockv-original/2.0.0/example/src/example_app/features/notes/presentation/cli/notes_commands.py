"""CLI commands of the notes feature."""

import asyncio
from typing import Annotated

import typer

from example_app.core.domain.entities.result import Failure, Success
from example_app.features.notes.domain.entities.note import Note
from example_app.features.notes.presentation.di.notes_getters import (
    add_note_use_case,
    delete_note_use_case,
    list_notes_use_case,
    update_note_use_case,
)

commands = typer.Typer(help="Notes commands.", no_args_is_help=True)


class NotesCommandsText:
    """User-facing CLI text of the notes commands."""

    NOTE_LINE = "{id}  {text}"
    NO_NOTES = "No notes yet"
    ADDED = "Added {id}"
    UPDATED = "Updated {id}"
    DELETED = "Deleted {id}"


def _line(note: Note) -> str:
    """Format one note for the terminal."""
    return NotesCommandsText.NOTE_LINE.format(id=note.id, text=note.text)


def _fail(error: str) -> typer.Exit:
    """Print ``error`` to stderr and return the exit to raise."""
    typer.echo(error, err=True)
    return typer.Exit(code=1)


@commands.command("list")
def list_notes() -> None:
    """Print every note, newest first."""
    match asyncio.run(list_notes_use_case()()):
        case Success(notes) if notes:
            for note in notes:
                typer.echo(_line(note))
        case Success():
            typer.echo(NotesCommandsText.NO_NOTES)
        case Failure(error):
            raise _fail(error)


@commands.command("add")
def add(text: Annotated[str, typer.Argument(help="Note text.")]) -> None:
    """Add a note; exits with code 1 when the text is blank or saving fails."""
    match asyncio.run(add_note_use_case()(text=text)):
        case Success(note):
            typer.echo(NotesCommandsText.ADDED.format(id=note.id))
        case Failure(error):
            raise _fail(error)


@commands.command("edit")
def edit(
    note_id: Annotated[str, typer.Argument(help="Id of the note.")],
    text: Annotated[str, typer.Argument(help="New text.")],
) -> None:
    """Replace the text of a note; exits with code 1 on failure."""
    match asyncio.run(update_note_use_case()(note_id=note_id, text=text)):
        case Success(note):
            typer.echo(NotesCommandsText.UPDATED.format(id=note.id))
        case Failure(error):
            raise _fail(error)


@commands.command("delete")
def delete(note_id: Annotated[str, typer.Argument(help="Id of the note.")]) -> None:
    """Delete a note; exits with code 1 on failure."""
    match asyncio.run(delete_note_use_case()(note_id=note_id)):
        case Success():
            typer.echo(NotesCommandsText.DELETED.format(id=note_id))
        case Failure(error):
            raise _fail(error)
