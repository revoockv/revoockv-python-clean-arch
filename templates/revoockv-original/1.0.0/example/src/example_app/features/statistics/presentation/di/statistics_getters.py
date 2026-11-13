"""Getters through which the statistics presentation layer reaches its use cases."""

from example_app.core.presentation.di.container import container
from example_app.features.statistics.domain.use_cases.get_notes_statistics_use_case import (
    GetNotesStatisticsUseCase,
)


def get_notes_statistics_use_case() -> GetNotesStatisticsUseCase:
    """Return the registered ``GetNotesStatisticsUseCase``."""
    return container.get(GetNotesStatisticsUseCase)
