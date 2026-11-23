from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from example_app.core.data.services.clock_service import ClockService
from example_app.core.presentation.di.container import container


class FixedClockService(ClockService):
    """A clock that always returns ``moment``."""

    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def now(self) -> datetime:
        return self.moment


@pytest.fixture(autouse=True)
def _reset_container() -> Iterator[None]:
    container.reset()
    yield
    container.reset()


@pytest.fixture
def clock() -> FixedClockService:
    return FixedClockService(datetime(2026, 11, 13, 9, 0, tzinfo=UTC))


@pytest.fixture
def database_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the app database at a temp JSON file (used by the adapter tests)."""
    path = tmp_path / "notes.json"
    monkeypatch.setenv("EXAMPLE_APP_DATABASE", str(path))
    return path
