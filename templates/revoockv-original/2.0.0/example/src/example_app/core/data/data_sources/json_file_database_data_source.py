"""Database data source stored in one JSON file (keeps CLI data between runs)."""

import asyncio
import json
from pathlib import Path
from typing import cast

from example_app.core.data.data_sources.database_data_source import (
    DatabaseDataSource,
    DatabaseDataSourceError,
    Row,
)


class JsonFileDatabaseDataSource(DatabaseDataSource):
    """Reads and writes ``{table: {id: row}}`` in a JSON file; file I/O runs in a thread."""

    _ID = "id"
    _ENCODING = "utf-8"
    _DUPLICATE_ID = "{table}: row {row_id} already exists"
    _UNKNOWN_ID = "{table}: no row {row_id}"

    def __init__(self, *, path: Path) -> None:
        self._path = path

    async def rows(self, *, table: str) -> list[Row]:
        """Return the rows of ``table``."""
        tables = await asyncio.to_thread(self._read)
        return list(tables.get(table, {}).values())

    async def insert(self, *, table: str, row: Row) -> None:
        """Add ``row`` under its id and save the file."""
        tables = await asyncio.to_thread(self._read)
        rows = tables.setdefault(table, {})
        row_id = str(row[self._ID])
        if row_id in rows:
            raise DatabaseDataSourceError(self._DUPLICATE_ID.format(table=table, row_id=row_id))
        rows[row_id] = row
        await asyncio.to_thread(self._write, tables)

    async def update(self, *, table: str, row: Row) -> None:
        """Replace the row with the same id and save the file."""
        tables = await asyncio.to_thread(self._read)
        row_id = str(row[self._ID])
        self._existing(tables, table=table, row_id=row_id)[row_id] = row
        await asyncio.to_thread(self._write, tables)

    async def delete(self, *, table: str, row_id: str) -> None:
        """Remove the row ``row_id`` and save the file."""
        tables = await asyncio.to_thread(self._read)
        del self._existing(tables, table=table, row_id=row_id)[row_id]
        await asyncio.to_thread(self._write, tables)

    def _existing(
        self, tables: dict[str, dict[str, Row]], *, table: str, row_id: str
    ) -> dict[str, Row]:
        rows = tables.get(table, {})
        if row_id not in rows:
            raise DatabaseDataSourceError(self._UNKNOWN_ID.format(table=table, row_id=row_id))
        return rows

    def _read(self) -> dict[str, dict[str, Row]]:
        if not self._path.is_file():
            return {}
        return cast(
            dict[str, dict[str, Row]], json.loads(self._path.read_text(encoding=self._ENCODING))
        )

    def _write(self, tables: dict[str, dict[str, Row]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(tables, ensure_ascii=False, indent=2), encoding=self._ENCODING
        )
