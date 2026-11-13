"""Result type for expected success/failure outcomes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Success[T]:
    """Successful outcome carrying a value (use ``Success(None)`` for commands)."""

    value: T


@dataclass(frozen=True, slots=True)
class Failure:
    """Failed outcome carrying a human-readable error message."""

    error: str


type Result[T] = Success[T] | Failure
"""Return type of every repository method and use case that can fail in an expected way."""
