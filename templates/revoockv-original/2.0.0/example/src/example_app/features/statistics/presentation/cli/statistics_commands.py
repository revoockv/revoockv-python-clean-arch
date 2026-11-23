"""CLI commands of the statistics feature."""

import asyncio

import typer

from example_app.core.domain.entities.result import Failure, Success
from example_app.features.statistics.presentation.di.statistics_getters import (
    get_notes_statistics_use_case,
)
from example_app.features.statistics.presentation.text.statistics_failure_text import (
    StatisticsFailureText,
)

commands = typer.Typer(help="Statistics commands.", no_args_is_help=True)


class StatisticsCommandsText:
    """User-facing CLI text of the statistics commands."""

    REPORT = "Notes: {notes}\nWords: {words}\nAdded today: {added_today}\nEdited: {edited}"


@commands.command("show")
def show() -> None:
    """Print the statistics of every note; exits with code 1 on failure."""
    match asyncio.run(get_notes_statistics_use_case()()):
        case Success(statistics):
            typer.echo(
                StatisticsCommandsText.REPORT.format(
                    notes=statistics.notes,
                    words=statistics.words,
                    added_today=statistics.added_today,
                    edited=statistics.edited,
                )
            )
        case Failure(failure):
            typer.echo(StatisticsFailureText.of(failure), err=True)
            raise typer.Exit(code=1)
