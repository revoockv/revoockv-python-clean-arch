"""Failure kind shared by every feature."""

from enum import Enum, auto


class FailureKind(Enum):
    """What sort of failure it is; adapters turn it into an HTTP status or an exit code."""

    INVALID_INPUT = auto()
    """The input breaks a rule: empty text, wrong format, too long."""
    NOT_FOUND = auto()
    """The requested record does not exist."""
    CONFLICT = auto()
    """The record exists already, or another write got there first."""
    UNAUTHORIZED = auto()
    """The caller is not signed in."""
    FORBIDDEN = auto()
    """The caller is signed in but may not do this."""
    UNEXPECTED = auto()
    """Anything the caller cannot fix: storage down, a timeout, a bug."""
