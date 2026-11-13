"""In-memory database data source (development and tests)."""

import asyncio

from example_app.core.data.data_sources.database_data_source import (
    DatabaseDataSource,
    DatabaseDataSourceError,
    Row,
)


class InMemoryDatabaseDataSource(DatabaseDataSource):
    """Keeps tables in memory and waits ``latency`` seconds per call, like real I/O."""

    _ID = "id"
    _DUPLICATE_ID = "{table}: row {row_id} already exists"
    _UNKNOWN_ID = "{table}: no row {row_id}"

    def __init__(self, *, latency: float = 0.0) -> None:
        self._latency = latency
        self._tables: dict[str, dict[str, Row]] = {}

    async def rows(self, *, table: str) -> list[Row]:
        """Return copies of the rows of ``table``."""
        await asyncio.sleep(self._latency)
        return [dict(row) for row in self._tables.get(table, {}).values()]

    async def insert(self, *, table: str, row: Row) -> None:
        """Add ``row`` under its id."""
        await asyncio.sleep(self._latency)
        rows = self._tables.setdefault(table, {})
        row_id = str(row[self._ID])
        if row_id in rows:
            raise DatabaseDataSourceError(self._DUPLICATE_ID.format(table=table, row_id=row_id))
        rows[row_id] = dict(row)

    async def update(self, *, table: str, row: Row) -> None:
        """Replace the row with the same id."""
        await asyncio.sleep(self._latency)
        rows = self._existing(table=table, row_id=str(row[self._ID]))
        rows[str(row[self._ID])] = dict(row)

    async def delete(self, *, table: str, row_id: str) -> None:
        """Remove the row ``row_id``."""
        await asyncio.sleep(self._latency)
        del self._existing(table=table, row_id=row_id)[row_id]

    def _existing(self, *, table: str, row_id: str) -> dict[str, Row]:
        rows = self._tables.get(table, {})
        if row_id not in rows:
            raise DatabaseDataSourceError(self._UNKNOWN_ID.format(table=table, row_id=row_id))
        return rows
