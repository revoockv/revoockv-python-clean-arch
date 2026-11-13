from pathlib import Path

import pytest

from example_app.core.data.data_sources.database_data_source import (
    DatabaseDataSource,
    DatabaseDataSourceError,
)
from example_app.core.data.data_sources.in_memory_database_data_source import (
    InMemoryDatabaseDataSource,
)
from example_app.core.data.data_sources.json_file_database_data_source import (
    JsonFileDatabaseDataSource,
)


@pytest.fixture(params=["memory", "json"])
def database(request: pytest.FixtureRequest, tmp_path: Path) -> DatabaseDataSource:
    if request.param == "memory":
        return InMemoryDatabaseDataSource()
    return JsonFileDatabaseDataSource(path=tmp_path / "db.json")


async def test_insert_update_delete(database: DatabaseDataSource) -> None:
    await database.insert(table="t", row={"id": "1", "v": "a"})
    await database.update(table="t", row={"id": "1", "v": "b"})

    assert await database.rows(table="t") == [{"id": "1", "v": "b"}]

    await database.delete(table="t", row_id="1")
    assert await database.rows(table="t") == []


async def test_unknown_id_raises(database: DatabaseDataSource) -> None:
    with pytest.raises(DatabaseDataSourceError):
        await database.delete(table="t", row_id="missing")
    with pytest.raises(DatabaseDataSourceError):
        await database.update(table="t", row={"id": "missing"})


async def test_duplicate_id_raises(database: DatabaseDataSource) -> None:
    await database.insert(table="t", row={"id": "1"})
    with pytest.raises(DatabaseDataSourceError):
        await database.insert(table="t", row={"id": "1"})


async def test_json_file_keeps_rows_between_instances(tmp_path: Path) -> None:
    path = tmp_path / "db.json"
    await JsonFileDatabaseDataSource(path=path).insert(table="t", row={"id": "1"})

    assert await JsonFileDatabaseDataSource(path=path).rows(table="t") == [{"id": "1"}]
