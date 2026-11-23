"""Failures of the statistics feature."""

from enum import Enum, auto

from example_app.core.domain.entities.failure_kind import FailureKind


class StatisticsFailure(Enum):
    """Why the statistics could not be counted; the text for the user lives in presentation."""

    STORAGE = auto()

    @property
    def kind(self) -> FailureKind:
        """The kind of this failure, for the adapters."""
        match self:
            case StatisticsFailure.STORAGE:
                return FailureKind.UNEXPECTED
