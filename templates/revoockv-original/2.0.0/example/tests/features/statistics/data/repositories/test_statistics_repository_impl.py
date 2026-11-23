import logging

from example_app.core.data.data_sources.in_memory_database_data_source import (
    InMemoryDatabaseDataSource,
)
from example_app.core.domain.entities.result import Failure, Success
from example_app.features.statistics.data.data_sources.database_statistics_data_source import (
    DatabaseStatisticsDataSource,
)
from example_app.features.statistics.data.data_sources.statistics_data_source import (
    StatisticsDataSource,
)
from example_app.features.statistics.data.models.note_facts_model import NoteFactsModel
from example_app.features.statistics.data.repositories.statistics_repository_impl import (
    StatisticsRepositoryImpl,
)
from example_app.features.statistics.domain.entities.notes_statistics import NotesStatistics
from example_app.features.statistics.domain.entities.statistics_failure import StatisticsFailure
from tests.conftest import FixedClockService


class BrokenStatisticsDataSource(StatisticsDataSource):
    async def note_facts(self) -> list[NoteFactsModel]:
        raise OSError("disk is gone")


async def test_counts_the_notes_table(clock: FixedClockService) -> None:
    database = InMemoryDatabaseDataSource()
    now = clock.now().isoformat()
    await database.insert(
        table="notes", row={"id": "1", "text": "a b c", "created_at": now, "updated_at": now}
    )
    repository = StatisticsRepositoryImpl(
        data_source=DatabaseStatisticsDataSource(database=database),
        clock=clock,
        logger=logging.getLogger("test"),
    )

    assert await repository.get_notes_statistics() == Success(
        NotesStatistics(notes=1, words=3, added_today=1, edited=0)
    )


async def test_data_source_error_becomes_failure(clock: FixedClockService) -> None:
    repository = StatisticsRepositoryImpl(
        data_source=BrokenStatisticsDataSource(), clock=clock, logger=logging.getLogger("test")
    )

    assert await repository.get_notes_statistics() == Failure(StatisticsFailure.STORAGE)
