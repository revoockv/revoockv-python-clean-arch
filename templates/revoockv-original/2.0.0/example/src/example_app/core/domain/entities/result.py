"""Result type for expected success/failure outcomes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Success[T]:
    """Successful outcome carrying a value (use ``Success(None)`` for commands)."""

    value: T


@dataclass(frozen=True, slots=True)
class Failure[F]:
    """Failed outcome carrying why it failed: a member of the feature's failure type, never text."""

    failure: F


type Result[T, F] = Success[T] | Failure[F]
"""Return type of every repository method and use case that can fail in an expected way."""
