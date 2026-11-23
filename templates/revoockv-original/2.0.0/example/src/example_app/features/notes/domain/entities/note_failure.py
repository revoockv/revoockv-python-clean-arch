"""Failures of the notes feature."""

from enum import Enum, auto

from example_app.core.domain.entities.failure_kind import FailureKind


class NoteFailure(Enum):
    """Why a notes operation failed; the text for the user lives in presentation."""

    EMPTY_TEXT = auto()
    NOT_FOUND = auto()
    STORAGE = auto()

    @property
    def kind(self) -> FailureKind:
        """The kind of this failure, for the adapters."""
        match self:
            case NoteFailure.EMPTY_TEXT:
                return FailureKind.INVALID_INPUT
            case NoteFailure.NOT_FOUND:
                return FailureKind.NOT_FOUND
            case NoteFailure.STORAGE:
                return FailureKind.UNEXPECTED
