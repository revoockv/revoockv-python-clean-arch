"""Main DI: registers core and every feature, then runs one-time initiations."""

from example_app.core.presentation.di.container import container
from example_app.core.presentation.di.core_di import register_core
from example_app.features.notes.presentation.di.notes_di import register_notes
from example_app.features.statistics.presentation.di.statistics_di import register_statistics


async def register_and_init() -> None:
    """Reset the container, register all dependencies and run feature initiations.

    The single DI entry point; ``main.py`` and ``api.py`` call nothing else.
    """
    container.reset()
    register_core(container)
    # <features>
    register_notes(container)
    register_statistics(container)
    # </features>
