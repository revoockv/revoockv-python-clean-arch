# Project setup and tooling

Python **3.12+** (PEP 695 generics: `class Success[T]`, `type Result[T] = ...`). Managed with **uv**.

## Create

```bash
python3 <skill_base>/scripts/init_project.py --name my-app [--path ~/projects] [--adapter none|fastapi|typer]
cd my-app
uv add fastapi uvicorn                                # --adapter fastapi
uv add typer                                          # --adapter typer
uv add --dev ruff mypy pytest pytest-asyncio          # always (+ httpx2 for FastAPI TestClient)
uv run pytest && uv run mypy && uv run ruff check .
```

The files come from the template: `scaffold/project/` (pyproject, README, `di.py`, core DI, tests),
`scaffold/main/<adapter>.py.tmpl` and the `[scaffold] core_files` of `example/`. The new project gets
`.clean_arch.toml` with this template's ref, so the linter and `init_feature.py` follow it.

Options: `--here` writes into `--path` itself (e.g. an existing empty repo), `--force` writes into a
non-empty directory without overwriting existing files.

Always add dependencies with `uv add` (latest compatible versions, pinned in `uv.lock`); never
hand-edit versions into `pyproject.toml`.

## Generated `pyproject.toml` (key parts)

```toml
requires-python = ">=3.12"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "B", "UP", "SIM", "RUF", "D", "TID", "ANN", "T20", "PT", "ASYNC", "G"]
ignore = ["D100", "D104", "D105", "D107"]
pydocstyle.convention = "google"
flake8-tidy-imports.ban-relative-imports = "all"
per-file-ignores."tests/**" = ["D", "ANN"]

[tool.mypy]
strict = true
mypy_path = "src"
packages = ["<package>"]
disable_error_code = ["type-abstract"]   # the container is keyed by ABCs

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

Line length is 100. Formatting is `ruff format` (no black/isort).

## Quality gate (run after every change)

```bash
uv run ruff check --fix . && uv run ruff format .
uv run mypy
uv run pytest
python3 <skill_base>/scripts/py_clean_arch_linter.py
```

All four must be clean before a task is done.

## Common additions (put them in the right layer)

| Need | Package | Where it may be imported |
|---|---|---|
| HTTP client | `httpx` | `data/data_sources/` |
| SQL | `sqlalchemy` (+ `asyncpg` / `aiosqlite`) | `data/data_sources/`, `data/models/` (ORM rows) |
| Payload validation | `pydantic` | `data/models/`, `presentation/api/schemas/` — never domain |
| Settings from env | `pydantic-settings` | `core/presentation/di/` (build a frozen domain `Settings`) |
| Rich CLI output | `rich` | `presentation/cli/` |
