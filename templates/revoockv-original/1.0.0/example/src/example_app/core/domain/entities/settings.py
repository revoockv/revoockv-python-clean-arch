"""Application settings entity."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Settings read from the environment once, in ``register_core``."""

    database_path: str
