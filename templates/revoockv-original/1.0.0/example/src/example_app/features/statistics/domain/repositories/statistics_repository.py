"""Statistics repository contract."""

from abc import ABC, abstractmethod

from example_app.core.domain.entities.result import Result
from example_app.features.statistics.domain.entities.notes_statistics import NotesStatistics


class StatisticsRepository(ABC):
    """Counts the statistics of the user's notes."""

    @abstractmethod
    async def get_notes_statistics(self) -> Result[NotesStatistics]:
        """Return the statistics of every note as of now."""
