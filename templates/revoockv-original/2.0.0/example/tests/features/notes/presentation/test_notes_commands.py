from pathlib import Path

from typer.testing import CliRunner

from example_app.main import app

runner = CliRunner()


def test_add_list_edit_delete(database_file: Path) -> None:
    assert runner.invoke(app, ["notes", "list"]).output.strip() == "No notes yet"

    added = runner.invoke(app, ["notes", "add", "Buy milk"])
    assert added.exit_code == 0
    note_id = added.output.split()[-1]

    assert "Buy milk" in runner.invoke(app, ["notes", "list"]).output
    assert runner.invoke(app, ["notes", "edit", note_id, "Buy bread"]).exit_code == 0
    assert "Buy bread" in runner.invoke(app, ["notes", "list"]).output
    assert runner.invoke(app, ["notes", "delete", note_id]).exit_code == 0
    assert database_file.is_file()


def test_blank_text_fails(database_file: Path) -> None:
    result = runner.invoke(app, ["notes", "add", "  "])

    assert result.exit_code == 1
    assert "Note text must not be empty" in result.output


def test_unknown_id_fails(database_file: Path) -> None:
    result = runner.invoke(app, ["notes", "delete", "missing"])

    assert result.exit_code == 1
    assert "There is no such note" in result.output
