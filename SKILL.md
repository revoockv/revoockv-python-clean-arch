---
name: revoockv-python-clean-arch
description: Create and enforce revoockv's Python clean architecture (data / domain / presentation per feature, mandatory use cases, Result[T], manual typed DI container, uv + ruff + mypy --strict + pytest). Use when the user asks to create a new Python project or feature, add use cases / repositories / data sources / DTO models, wire DI (register_<feature>, getters, register_and_init), add a FastAPI or Typer (or other) presentation adapter, refactor an existing Python codebase into clean architecture, or check a Python project against these rules.
metadata:
  version: 0.3.0
  author: revoockv
---

# revoockv Python Clean Architecture (Result + typed Container + use cases)

This skill is strict. If any architectural decision is unclear, copy the patterns from
`references/feature_template_auth.md` (verified code) and adapt naming only.

## Default stack

- Python **3.12+**, `src` layout, managed with **uv**
- `ruff` (lint + format), `mypy --strict`, `pytest` + `pytest-asyncio`
- stdlib `logging`, no DI framework (own typed `Container`)
- Presentation is framework-agnostic: FastAPI (`presentation/api/`), Typer (`presentation/cli/`)
  or any other adapter folder

## Must-read references (load these when implementing)

- Folder structure: `references/folder_structure.md`
- Golden template (domain → data → DI → FastAPI/Typer → tests): `references/feature_template_auth.md`
- Result: `references/result.md`
- Use cases: `references/use_case_naming.md`
- Models mapping (DTO ↔ entity): `references/models_mapping.md`
- DI patterns (Container, register/init, getters, `di.py`): `references/di_patterns.md`
- Presentation adapters: `references/presentation_patterns.md`
- Imports / layer dependency matrix: `references/imports.md`
- Logging conventions: `references/logging_conventions.md`
- Docstring standard: `references/docstring_standard.md`
- Testing: `references/testing.md`
- Project setup / tooling: `references/project_setup.md`
- Git rules: `references/git_rules.md` — branch strategy, commit message format, tagging

## Quick navigation

Use `DECISIONS.md` to find the right reference without reading all of them. It maps
"you need X → use pattern Y" across architecture, DI, data, presentation, testing and conventions.

## Scripts (never copy them into the project — run them from the skill folder)

```bash
# New project (writes files only; then run the `uv add` commands it prints)
python3 <skill_base>/scripts/init_project.py --name my-app [--path <dir>] [--adapter none|fastapi|typer] [--here]

# New feature (run from the project root): skeleton + DI stubs + wiring into di.py / main.py
python3 <skill_base>/scripts/init_feature.py --feature <name> [--adapter fastapi|typer] [--subfeature <name>]
```

After `init_feature.py`, run `uv run ruff check --fix . && uv run ruff format .` to sort the
inserted imports.

## Automated checks (always run after changes)

**Default target = the whole project.** Run the linter without a path from the project root; it
finds `src/<package>/`. Narrow to one feature only when the user names it.

```bash
uv run ruff check --fix . && uv run ruff format .
uv run mypy
uv run pytest
python3 <skill_base>/scripts/py_clean_arch_linter.py                              # whole project
python3 <skill_base>/scripts/py_clean_arch_linter.py src/<package>/features/<f>   # one feature
python3 <skill_base>/scripts/py_clean_arch_linter.py --strict                     # exit 1 on violations (CI)
python3 <skill_base>/scripts/py_clean_arch_linter.py --rules import_violation,naming_file
python3 <skill_base>/scripts/py_clean_arch_linter.py --json
python3 <skill_base>/scripts/py_clean_arch_linter.py --ignore magic_strings        # only when the user asks
python3 <skill_base>/scripts/py_clean_arch_linter.py --list-rules
```

**22 rules:** `folder_structure`, `naming_file`, `naming_class`, `use_case_shape`,
`use_case_no_try`, `import_violation`, `relative_import`, `domain_repository`, `repository_impl`,
`repository_result`, `repository_logging`, `model_mapping`, `entity_frozen`, `logger_injection`,
`no_print`, `container_access`, `docstring_public`, `type_hints`, `magic_numbers`, `magic_strings`,
`module_constants`, `di_naming`.

All rules are enabled by default. Only disable a rule with `--ignore` when the user explicitly
requests it. A task is not done until ruff, mypy, pytest and the linter are all clean.

## Layer responsibilities

- **Domain** — entities (frozen dataclasses), repository interfaces (`ABC`), use cases. Stdlib only;
  no frameworks, no I/O, no imports from data or presentation.
- **Data** — data sources (talk to HTTP/DB/SDK/files; may raise), optional services
  (`data/services/<name>_service.py`: technology adapters such as file converters or CLI tools), models/DTOs with
  `to_entity()`/`from_entity()`, repository implementations that catch exceptions, log, and return
  `Result[...]`.
- **Presentation** — `di/` (registration + getters) and adapter folders (`api/`, `cli/`, ...).
  Adapters call use cases through getters and map `Result` to output. No business logic.

Dependency direction: presentation → domain ← data. Wiring happens only in `presentation/di/`
and `di.py`.

## Workflow: choose the operation

### A) Create a new project

1. `init_project.py --name <name> --adapter <adapter>` (ask which adapter only if the user has not
   said and it matters; default `none`).
2. Run the printed `uv add` commands, then the quality gate — it must pass on the empty skeleton.
3. Continue with B) for each feature.

### B) Create a new feature

1. `init_feature.py --feature <name> [--adapter ...]` from the project root.
2. Domain first:
   - entities in `domain/entities/` (frozen dataclasses)
   - repository interface in `domain/repositories/<name>_repository.py` (`ABC`, methods return `Result`)
   - use cases in `domain/use_cases/<action>_use_case.py` (one class, async `__call__`)
3. Data:
   - data source ABC + implementation(s) in `data/data_sources/<name>_data_source.py`
   - models in `data/models/<name>_model.py` with `to_entity` / `from_entity`
   - `data/repositories/<name>_repository_impl.py`: inherits the domain interface, receives
     `logger`, try/except around every data-source call → `Failure`, logs every public method
4. Presentation DI:
   - `register_<feature>(container)`: data sources → repository (keyed by domain interface) → use cases
   - optional `async init_<feature>(container)` for startup work; add `await init_<feature>(container)` to `di.py`
   - `<feature>_getters.py`: one getter per use case
5. Adapter (if any): thin handlers/commands — getter → use case → `match` Result → output.
   See `references/presentation_patterns.md`.
6. Tests mirroring the layers (`references/testing.md`): use cases with fake repositories,
   repository with fake/in-memory data source, adapter end-to-end.
7. Quality gate + linter.

Golden reference: `references/feature_template_auth.md`

### C) Refactor an existing Python project into this architecture

1. Run the linter to see the current state; read `references/feature_template_auth.md`.
2. Introduce `core/` (`init_project.py --here --force` in the repo root writes missing core files
   without overwriting existing ones) and `di.py`.
3. Move code feature by feature: extract entities and repository interfaces first, wrap existing
   DB/HTTP code as data sources, add repository implementations returning `Result`, then use cases,
   then point existing routes/commands at getters.
4. Replace module-level singletons / `Depends` factories / global clients with container registrations.
5. Run the full quality gate after each feature, not only at the end.

### D) Add a presentation adapter to an existing feature

`init_feature.py --feature <f> --adapter fastapi|typer` is idempotent: it adds the adapter files and
wiring and leaves existing files untouched. Then follow `references/presentation_patterns.md`.

## Critical Notes

### Result — match, don't inspect

`Result[T] = Success[T] | Failure`. Consume it with `match`; never add `.is_success` / `.value`
helpers. To narrow `Success[T | None]`, use a class pattern: `case Success(AuthUser() as user):`
then `case Success():`. Commands return `Success(None)`.

### Use case = one user ↔ app interaction

A use case is something the user asks the app to do (sign in, convert to Markdown), not an
implementation step and not one per repository method. Detection, routing, splitting, retries and
merging live in the repository and its services. See `references/use_case_naming.md`.

### Use cases — no try/except, only `__call__`

Repositories already convert exceptions into `Failure`. Use cases return `Failure(...)` for business
rule violations and otherwise `return await self._repository.<method>(...)`.

### Constants — inside the owning class

Never declare constants at module level in domain or presentation code. A constant belongs to the
class that uses it:

```python
class SignInUseCase:
    """Validates credentials and signs the user in."""

    _EMAIL_SEPARATOR = "@"
    _INVALID_EMAIL_ERROR = "Email is not valid"
```

- Private class attributes (`_NAME`) for values used only inside the class; public (`NAME`) for
  values another module needs.
- Mutable class constants must be `ClassVar[...]` (ruff `RUF012`).
- Module-level functions (DI, getters, CLI commands) put their constants in a small constants class
  in the same module: `AuthDi`, `AuthCommandsText`.
- HTTP status codes: `http.HTTPStatus`, never numbers.
- The `magic_strings`/`magic_numbers` rules check function bodies in domain and presentation.
  Exempt: docstrings, logger messages, annotations/`Literal[...]`, decorator arguments, module-level
  adapter objects (`APIRouter(prefix=...)`), and the whole data layer (JSON keys, SQL, headers).

### Async by default

Data sources, repositories and use cases are `async`. Typer commands bridge with `asyncio.run(...)`.
A purely CPU-bound feature may be sync end-to-end, but never mix sync and async within one
repository interface.

### Keyword-only parameters

Repository and use case methods with more than one parameter use `*` (keyword-only) so call sites
read `sign_in(email=..., password=...)`.

### mypy and the container

`disable_error_code = ["type-abstract"]` in `pyproject.toml` is intentional: the container is
keyed by abstract interfaces. Do not remove it and do not register implementations under concrete types.
