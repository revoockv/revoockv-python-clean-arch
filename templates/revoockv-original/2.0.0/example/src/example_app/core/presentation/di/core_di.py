"""Core DI: dependencies shared by every feature."""

import logging
import os
from pathlib import Path

from example_app.core.data.data_sources.database_data_source import DatabaseDataSource
from example_app.core.data.data_sources.json_file_database_data_source import (
    JsonFileDatabaseDataSource,
)
from example_app.core.data.services.clock_service import ClockService
from example_app.core.domain.entities.settings import Settings
from example_app.core.presentation.di.container import Container


class CoreDi:
    """Configuration values used by ``register_core``."""

    LOGGER_NAME = "example_app"
    LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    DATABASE_ENV = "EXAMPLE_APP_DATABASE"
    DEFAULT_DATABASE = "notes.json"


def register_core(container: Container) -> None:
    """Register the logger, the settings, the clock and the app database.

    Must run first in ``register_and_init``: every feature receives these.
    """
    logging.basicConfig(level=logging.INFO, format=CoreDi.LOG_FORMAT)
    container.register_singleton(logging.Logger, logging.getLogger(CoreDi.LOGGER_NAME))
    settings = Settings(database_path=os.environ.get(CoreDi.DATABASE_ENV, CoreDi.DEFAULT_DATABASE))
    container.register_singleton(Settings, settings)
    container.register_singleton(ClockService, ClockService())
    container.register_singleton(
        DatabaseDataSource, JsonFileDatabaseDataSource(path=Path(settings.database_path))
    )
