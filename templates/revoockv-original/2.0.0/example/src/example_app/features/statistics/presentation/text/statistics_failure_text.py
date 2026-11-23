"""User-facing text of the statistics failures."""

from example_app.features.statistics.domain.entities.statistics_failure import StatisticsFailure


class StatisticsFailureText:
    """The text of every ``StatisticsFailure``; a new member without a text fails mypy."""

    _STORAGE = "The notes could not be read"

    @classmethod
    def of(cls, failure: StatisticsFailure) -> str:
        """Return the text that tells the user about ``failure``."""
        match failure:
            case StatisticsFailure.STORAGE:
                return cls._STORAGE
