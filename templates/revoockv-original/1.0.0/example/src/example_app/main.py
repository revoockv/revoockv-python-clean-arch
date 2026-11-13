"""Application entry point (Typer CLI). Run: uv run example-app notes add "Buy milk"."""

import asyncio

import typer

from example_app.di import register_and_init
from example_app.features.notes.presentation.cli.notes_commands import commands as notes_commands
from example_app.features.statistics.presentation.cli.statistics_commands import (
    commands as statistics_commands,
)

app = typer.Typer(no_args_is_help=True)
# <commands>
app.add_typer(notes_commands, name="notes")
app.add_typer(statistics_commands, name="statistics")
# </commands>


@app.callback()
def bootstrap() -> None:
    """Register dependencies and run initiations before any command."""
    asyncio.run(register_and_init())


if __name__ == "__main__":
    app()
