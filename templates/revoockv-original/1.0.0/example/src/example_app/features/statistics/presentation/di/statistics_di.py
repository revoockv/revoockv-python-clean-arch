"""DI registration for the statistics feature."""

import logging

from example_app.core.data.data_sources.database_data_source import DatabaseDataSource
from example_app.core.data.services.clock_service import ClockService
from example_app.core.presentation.di.container import Container
from example_app.features.statistics.data.data_sources.database_statistics_data_source import (
    DatabaseStatisticsDataSource,
)
from example_app.features.statistics.data.data_sources.statistics_data_source import (
    StatisticsDataSource,
)
from example_app.features.statistics.data.repositories.statistics_repository_impl import (
    StatisticsRepositoryImpl,
)
from example_app.features.statistics.domain.repositories.statistics_repository import (
    StatisticsRepository,
)
from example_app.features.statistics.domain.use_cases.get_notes_statistics_use_case import (
    GetNotesStatisticsUseCase,
)


def register_statistics(container: Container) -> None:
    """Register data sources, repositories and use cases of the statistics feature.

    Order: data sources → repositories (by domain interface) → use cases.
    """
    container.register_singleton(
        StatisticsDataSource,
        DatabaseStatisticsDataSource(database=container.get(DatabaseDataSource)),
    )
    container.register_singleton(
        StatisticsRepository,
        StatisticsRepositoryImpl(
            data_source=container.get(StatisticsDataSource),
            clock=container.get(ClockService),
            logger=container.get(logging.Logger),
        ),
    )
    container.register_singleton(
        GetNotesStatisticsUseCase, GetNotesStatisticsUseCase(container.get(StatisticsRepository))
    )
