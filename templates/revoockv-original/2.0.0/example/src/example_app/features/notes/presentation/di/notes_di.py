"""DI registration for the notes feature."""

import logging

from example_app.core.data.data_sources.database_data_source import DatabaseDataSource
from example_app.core.data.services.clock_service import ClockService
from example_app.core.presentation.di.container import Container
from example_app.features.notes.data.data_sources.database_notes_data_source import (
    DatabaseNotesDataSource,
)
from example_app.features.notes.data.data_sources.notes_data_source import NotesDataSource
from example_app.features.notes.data.repositories.notes_repository_impl import NotesRepositoryImpl
from example_app.features.notes.domain.repositories.notes_repository import NotesRepository
from example_app.features.notes.domain.use_cases.add_note_use_case import AddNoteUseCase
from example_app.features.notes.domain.use_cases.delete_note_use_case import DeleteNoteUseCase
from example_app.features.notes.domain.use_cases.list_notes_use_case import ListNotesUseCase
from example_app.features.notes.domain.use_cases.update_note_use_case import UpdateNoteUseCase


def register_notes(container: Container) -> None:
    """Register data sources, repositories and use cases of the notes feature.

    Order: data sources → repositories (by domain interface) → use cases.
    """
    container.register_singleton(
        NotesDataSource,
        DatabaseNotesDataSource(
            database=container.get(DatabaseDataSource), clock=container.get(ClockService)
        ),
    )
    container.register_singleton(
        NotesRepository,
        NotesRepositoryImpl(
            data_source=container.get(NotesDataSource), logger=container.get(logging.Logger)
        ),
    )
    repository = container.get(NotesRepository)
    container.register_singleton(ListNotesUseCase, ListNotesUseCase(repository))
    container.register_singleton(AddNoteUseCase, AddNoteUseCase(repository))
    container.register_singleton(UpdateNoteUseCase, UpdateNoteUseCase(repository))
    container.register_singleton(DeleteNoteUseCase, DeleteNoteUseCase(repository))
