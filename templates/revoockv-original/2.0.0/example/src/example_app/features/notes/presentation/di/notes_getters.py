"""Getters through which the notes presentation layer reaches its use cases.

Presentation code imports these functions instead of touching the container or the domain
use case modules directly.
"""

from example_app.core.presentation.di.container import container
from example_app.features.notes.domain.use_cases.add_note_use_case import AddNoteUseCase
from example_app.features.notes.domain.use_cases.delete_note_use_case import DeleteNoteUseCase
from example_app.features.notes.domain.use_cases.list_notes_use_case import ListNotesUseCase
from example_app.features.notes.domain.use_cases.update_note_use_case import UpdateNoteUseCase


def list_notes_use_case() -> ListNotesUseCase:
    """Return the registered ``ListNotesUseCase``."""
    return container.get(ListNotesUseCase)


def add_note_use_case() -> AddNoteUseCase:
    """Return the registered ``AddNoteUseCase``."""
    return container.get(AddNoteUseCase)


def update_note_use_case() -> UpdateNoteUseCase:
    """Return the registered ``UpdateNoteUseCase``."""
    return container.get(UpdateNoteUseCase)


def delete_note_use_case() -> DeleteNoteUseCase:
    """Return the registered ``DeleteNoteUseCase``."""
    return container.get(DeleteNoteUseCase)
