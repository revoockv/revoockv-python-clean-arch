# example-app

The example of the `revoockv-original` template: notes (add, list, edit, delete) and their
statistics over one placeholder database in `core`, with a Typer CLI and a FastAPI adapter.
See `docs/example_app.md` of the skill.

```bash
uv sync
uv run example-app notes add "Buy milk"
uv run example-app notes list
uv run example-app statistics show
uv run uvicorn example_app.api:app --reload

uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```
