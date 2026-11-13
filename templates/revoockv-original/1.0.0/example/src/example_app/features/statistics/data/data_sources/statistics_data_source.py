"""Statistics data source contract."""

from abc import ABC, abstractmethod

from example_app.features.statistics.data.models.note_facts_model import NoteFactsModel


class StatisticsDataSource(ABC):
    """Reads the facts of the stored notes. May raise."""

    @abstractmethod
    async def note_facts(self) -> list[NoteFactsModel]:
        """Return the facts of every stored note."""
