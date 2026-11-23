# Folder structure

The required and optional folders are the template's `[structure]` (`template.toml`); `init_project.py` and
`init_feature.py` create them and the linter's `folder_structure` rule checks them. A working tree:
`example/src/example_app/`.

`src` layout, one app package. `core/` mirrors the feature layout: same layer folders
(`data/`, `domain/`, `presentation/`) with the same required subfolders.

## Root

```
<project>/
  pyproject.toml
  src/<package>/
    __init__.py
    py.typed
    di.py                      — register_and_init(): core DI, then every feature (# <features> block)
    main.py                    — entry point: asyncio / FastAPI app / Typer app
    core/
      data/
        data_sources/
        models/
        repositories/
      domain/
        entities/
          result.py            — Success / Failure / Result[T, F]  (NEVER directly in domain/)
          failure_kind.py      — FailureKind: what sort of failure, for the adapters
        repositories/
        use_cases/
      presentation/
        di/
          container.py         — Container + the `container` instance
          core_di.py           — register_core(): logging.Logger singleton
    features/
      <feature>/ ...
  tests/                       — mirrors src/<package>/ (tests/features/<feature>/domain/use_cases/...)
    conftest.py                — autouse fixture that resets the container
```

## Feature

```
src/<package>/features/<feature>/
  data/                        — technology-specific implementations
    data_sources/              — <name>_data_source.py: ABC + implementations (HTTP, DB, SDK, files). May raise.
    models/                    — <name>_model.py: DTOs with to_entity() / from_entity()
    repositories/              — <name>_repository_impl.py: <Name>RepositoryImpl(<Name>Repository)
    services/                  — optional: <name>_service.py: <Name>Service — technology adapters/converters
                                 (wrap one library or CLI tool, e.g. DoclingService, FfmpegService). May raise.
  domain/                      — business logic, stdlib only
    entities/                  — frozen dataclasses, enums, <feature>_failure.py (the failure type)
    repositories/              — <name>_repository.py: <Name>Repository(ABC)
    use_cases/                 — <action>_use_case.py: <Action>UseCase with async __call__
  presentation/                — delivery mechanisms + DI wiring
    di/                        — REQUIRED
      <feature>_di.py          — register_<feature>(container) [+ optional async init_<feature>(container)]
      <feature>_getters.py     — one getter function per use case
      <subfeature>_di.py       — optional subfeature DI
    api/                       — optional FastAPI adapter
      <feature>_router.py      — `router = APIRouter(prefix=..., tags=[...])`
      schemas/                 — Pydantic request/response models
    cli/                       — optional Typer adapter
      <feature>_commands.py    — `commands = typer.Typer(...)`
    text/                      — <feature>_failure_text.py: the text of every failure, for every adapter
    <other adapter>/           — any other delivery mechanism (worker/, bot/, grpc/...)
```

Every folder is a regular package (has `__init__.py`).

## Rules enforced by the linter (`folder_structure`, `naming_file`)

- Each feature and `core/` must have `data/{data_sources,models,repositories}`,
  `domain/{entities,repositories,use_cases}` and `presentation/di`.
- `data/` may additionally have the optional `services/` folder; otherwise `data/` and `domain/` accept no
  other subfolders (`usecases/`, `utils/`, `helpers/` are violations).
- No `.py` file directly in `data/`, `domain/` or the feature folder itself.
- `presentation/` may hold any adapter folders; files nested below an adapter folder are free-form.
- File suffixes: `_use_case.py`, `_repository.py` (domain), `_repository_impl.py`, `_model.py`,
  `_data_source.py`, `_service.py`, `_di.py` / `_getters.py` (`core/presentation/di/container.py` is the only exception).

## Naming

- Main DI: `src/<package>/di.py` → `async def register_and_init() -> None`
- Feature DI: `features/<feature>/presentation/di/<feature>_di.py` → `register_<feature>(container)`;
  optional `async def init_<feature>(container)` for one-time startup work.
- Feature getters: `features/<feature>/presentation/di/<feature>_getters.py`
- Subfeature DI: `features/<feature>/presentation/di/<subfeature>_di.py` → `register_<feature>_<subfeature>(container)`,
  called from `register_<feature>`.
