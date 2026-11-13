"""Statistics data source over the app database."""

from example_app.core.data.data_sources.database_data_source import DatabaseDataSource
from example_app.features.statistics.data.data_sources.statistics_data_source import (
    StatisticsDataSource,
)
from example_app.features.statistics.data.models.note_facts_model import NoteFactsModel


class DatabaseStatisticsDataSource(StatisticsDataSource):
    """Reads the ``notes`` table; the notes feature owns writing it."""

    _TABLE = "notes"

    def __init__(self, *, database: DatabaseDataSource) -> None:
        self._database = database

    async def note_facts(self) -> list[NoteFactsModel]:
        """Map every ``notes`` row to its facts."""
        return [
            NoteFactsModel.from_row(row) for row in await self._database.rows(table=self._TABLE)
        ]
