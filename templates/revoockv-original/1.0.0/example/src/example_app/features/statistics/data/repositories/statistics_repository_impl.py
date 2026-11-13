"""Statistics repository implementation."""

import logging

from example_app.core.data.services.clock_service import ClockService
from example_app.core.domain.entities.result import Failure, Result, Success
from example_app.features.statistics.data.data_sources.statistics_data_source import (
    StatisticsDataSource,
)
from example_app.features.statistics.domain.entities.notes_statistics import NotesStatistics
from example_app.features.statistics.domain.repositories.statistics_repository import (
    StatisticsRepository,
)


class StatisticsRepositoryImpl(StatisticsRepository):
    """Orchestrates the data source (the facts) and the clock service (now)."""

    def __init__(
        self, *, data_source: StatisticsDataSource, clock: ClockService, logger: logging.Logger
    ) -> None:
        self._data_source = data_source
        self._clock = clock
        self._logger = logger

    async def get_notes_statistics(self) -> Result[NotesStatistics]:
        """Read the facts and count them as of the clock's now."""
        try:
            models = await self._data_source.note_facts()
        except Exception as e:
            self._logger.error("GetNotesStatistics: failure — %s", e)
            return Failure(str(e))
        statistics = NotesStatistics.of(
            (model.to_entity() for model in models), now=self._clock.now()
        )
        self._logger.info("GetNotesStatistics: success — %d note(s)", statistics.notes)
        return Success(statistics)
