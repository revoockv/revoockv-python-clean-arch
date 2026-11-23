"""Database data source contract shared by every feature."""

from abc import ABC, abstractmethod

type Row = dict[str, object]
"""One row of a table: column name → value."""


class DatabaseDataSourceError(Exception):
    """Raised by database data sources when an operation fails."""


class RowNotFoundError(DatabaseDataSourceError):
    """Raised when there is no row with the given id."""


class DatabaseDataSource(ABC):
    """A tiny table store keyed by ``id``. May raise; repositories convert errors to ``Failure``."""

    @abstractmethod
    async def rows(self, *, table: str) -> list[Row]:
        """Return every row of ``table`` (empty when the table does not exist yet)."""

    @abstractmethod
    async def insert(self, *, table: str, row: Row) -> None:
        """Add ``row``; its ``id`` must be new.

        Raises:
            DatabaseDataSourceError: If a row with the same id exists.
        """

    @abstractmethod
    async def update(self, *, table: str, row: Row) -> None:
        """Replace the row with the same ``id``.

        Raises:
            RowNotFoundError: If there is no row with that id.
        """

    @abstractmethod
    async def delete(self, *, table: str, row_id: str) -> None:
        """Remove the row ``row_id``.

        Raises:
            RowNotFoundError: If there is no row with that id.
        """
