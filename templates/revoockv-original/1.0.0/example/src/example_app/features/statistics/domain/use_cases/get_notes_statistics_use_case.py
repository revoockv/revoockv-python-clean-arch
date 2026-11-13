"""Get notes statistics use case."""

from example_app.core.domain.entities.result import Result
from example_app.features.statistics.domain.entities.notes_statistics import NotesStatistics
from example_app.features.statistics.domain.repositories.statistics_repository import (
    StatisticsRepository,
)


class GetNotesStatisticsUseCase:
    """Shows the statistics of the user's notes."""

    def __init__(self, repository: StatisticsRepository) -> None:
        self._repository = repository

    async def __call__(self) -> Result[NotesStatistics]:
        """Return the statistics of every note as of now."""
        return await self._repository.get_notes_statistics()
