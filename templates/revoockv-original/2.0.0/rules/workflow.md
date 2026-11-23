# Workflow — layers and operations

This template is strict. When a decision is unclear, copy the patterns of `rules/examples/auth_*.md` or of
`example/` (notes + statistics over one database in core, a Typer CLI and a FastAPI adapter, tests on every layer)
and adapt the names only. Run the quality gate after every change.

## Layer responsibilities

- **Domain** — entities (frozen dataclasses), repository interfaces (`ABC`), use cases. Stdlib only; no frameworks,
  no I/O, no imports from data or presentation.
- **Data** — data sources (talk to HTTP/DB/SDK/files; may raise), optional services (`data/services/`: one library
  or tool each), models/DTOs with `to_entity()` / `from_entity()`, repository implementations that orchestrate them,
  catch exceptions, log, and return `Result[T, <Feature>Failure]` (`rules/data/data_design.md`).
- **Presentation** — `di/` (registration + getters) and adapter folders (`api/`, `cli/`, …). Adapters call use cases
  through getters and map `Result` to output; failure texts live in `presentation/text/`. No business logic.

Dependency direction: presentation → domain ← data. Wiring happens only in `presentation/di/` and `di.py`.

## Quality gate (a task is done only when all pass)

```bash
uv run ruff check --fix . && uv run ruff format .
uv run mypy
uv run pytest
python3 <skill_base>/scripts/py_clean_arch_linter.py            # --strict in CI
```

## A) Create a new project

1. `init_project.py --name <name> --adapter none|fastapi|typer` (ask for the adapter only when the user has not said
   and it matters; default `none`).
2. Run the `uv add` commands it prints, then the quality gate — it must pass on the empty skeleton.
3. Continue with B) for each feature.

## B) Create a new feature

1. `init_feature.py --feature <name> [--adapter fastapi|typer]` from the project root.
2. Domain first: entities and the failure type (`<feature>_failure.py`, `rules/errors/result.md`) in
   `domain/entities/`; the repository interface in
   `domain/repositories/<name>_repository.py` (`ABC`, methods return `Result[T, <Feature>Failure]`); use cases in
   `domain/use_cases/<action>_use_case.py` (`rules/use_cases/use_case_naming.md`).
3. Data (`rules/data/`): data source ABC + implementation(s), services for libraries/tools, models with mapping,
   `data/repositories/<name>_repository_impl.py` that inherits the domain interface, receives `logger`, wraps every
   data-source call in try/except → `Failure(<member>)` and logs every public method.
4. Presentation DI (`rules/di/di_patterns.md`): `register_<feature>(container)` — data sources → repository (keyed by
   the domain interface) → use cases; optional `async init_<feature>(container)` called from `di.py`;
   `<feature>_getters.py` with one getter per use case.
5. Adapter (`rules/presentation/presentation_patterns.md`): getter → use case → `match` Result → output, with
   `presentation/text/<feature>_failure_text.py` for the failures.
6. Tests mirroring the layers (`rules/testing/testing.md`), then the quality gate.

## C) Refactor an existing project into this template

1. Run the linter for a baseline; read `rules/examples/auth_*.md`.
2. Introduce `core/` and `di.py`: `init_project.py --here --force` in the repo root writes the missing files and keeps
   existing ones.
3. Move code feature by feature: entities and repository interfaces first, wrap existing DB/HTTP code as data sources
   (split big modules by `rules/data/data_design.md`), add repository implementations returning `Result`, then use
   cases, then point existing routes/commands at getters.
4. Replace module-level singletons / `Depends` factories / global clients with container registrations.
5. Run the quality gate after each feature, not only at the end.

## D) Add an adapter to an existing feature

`init_feature.py --feature <f> --adapter fastapi|typer` is idempotent: it adds the adapter files and wiring and keeps
existing files.
