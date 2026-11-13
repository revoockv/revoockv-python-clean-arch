from datetime import UTC, datetime, timedelta

from example_app.features.statistics.domain.entities.note_facts import NoteFacts
from example_app.features.statistics.domain.entities.notes_statistics import NotesStatistics


def test_counts_notes_words_today_and_edited() -> None:
    now = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)
    yesterday = now - timedelta(days=1)
    facts = [
        NoteFacts(words=2, created_at=now, updated_at=now),
        NoteFacts(words=3, created_at=yesterday, updated_at=now),
    ]

    assert NotesStatistics.of(facts, now=now) == NotesStatistics(
        notes=2, words=5, added_today=1, edited=1
    )


def test_no_notes() -> None:
    now = datetime(2026, 11, 13, tzinfo=UTC)

    assert NotesStatistics.of([], now=now) == NotesStatistics(
        notes=0, words=0, added_today=0, edited=0
    )
