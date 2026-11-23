from pathlib import Path

from typer.testing import CliRunner

from example_app.main import app

runner = CliRunner()


def test_show(database_file: Path) -> None:
    runner.invoke(app, ["notes", "add", "one two"])
    runner.invoke(app, ["notes", "add", "three"])

    result = runner.invoke(app, ["statistics", "show"])

    assert result.exit_code == 0
    assert "Notes: 2" in result.output
    assert "Words: 3" in result.output
    assert "Added today: 2" in result.output
    assert "Edited: 0" in result.output
