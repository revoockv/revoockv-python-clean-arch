# Decisions — "you need X → do Y"

The short answer first; the rule file in brackets has the details.

## Architecture

| You need to… | Do |
|---|---|
| Start a project | `init_project.py --name <n> --adapter none\|fastapi\|typer`, run the printed `uv add`, then the quality gate (`workflow.md`) |
| Add a feature | `init_feature.py --feature <f> [--adapter …]`, then domain → data → DI → adapter → tests (`workflow.md`) |
| Know what a layer may import | domain: stdlib + domain only; presentation adapters: getters + entities + `Result` (`style/imports.md`) |
| Define an entity | `@dataclass(frozen=True, slots=True)` in `domain/entities/` (`examples/auth_domain.md`) |
| Define a repository interface | `ABC` in `domain/repositories/`, every method returns `Result[...]`, keyword-only params |
| Decide if something is a use case | would the user say they asked the app to do it? yes → use case; no → repository/service (`use_cases/use_case_naming.md`) |
| Share code between features | depend on the other feature's **domain** interface, resolved in your `<feature>_di.py` |
| Put something every feature uses | `core/`, same layer folders as a feature |

## Data

| You need to… | Do |
|---|---|
| Call an API / DB / site / files | a data source in `data/data_sources/` (ABC + implementation) |
| Wrap a library or tool (browser, ffmpeg, converter, model, clock) | a service in `data/services/<name>_service.py` |
| Combine several sources/services, merge, retry, fall back | the repository implementation orchestrates them (`data/data_design.md`) |
| A file grew past 200 lines (`file_size`) | split it by job: I/O → data source, library → service, parsing → model (`data/data_design.md`) |
| A DTO | `<Name>Model` in `data/models/` with `to_entity` / `from_entity` and `from_dict` / `from_row` (`data/models_mapping.md`) |
| Validate external payloads | Pydantic in `data/models/` — never in domain |
| Swap a backend | a new data source implementation; change one line in `<feature>_di.py` |

## Errors

| You need to… | Do |
|---|---|
| Return success/failure | `Success(value)` / `Failure(message)`; commands `Success(None)` (`errors/result.md`) |
| Consume a `Result` | `match`: `case Success(x)` / `case Failure(error)`; never `.is_success` helpers |
| Narrow `Success[T \| None]` | `case Success(Entity() as x):` then `case Success():` |
| Place try/except | only in the repository implementation; data sources raise, use cases never catch |
| "Not found" as a normal outcome | `Success(None)` with `Result[T \| None]` |

## DI

| You need to… | Do |
|---|---|
| Register a feature | `register_<feature>(container)`: data sources → repositories (by interface) → use cases (`di/di_patterns.md`) |
| Startup work (pool, cache, subscription) | `async init_<feature>(container)`, awaited in `di.py` |
| Singleton / lazy / factory | `register_singleton` / `register_lazy_singleton` / `register_factory` |
| Reach a use case from an adapter | its getter in `<feature>_getters.py` — never the container |
| Settings / env vars | a frozen `Settings` entity built in `register_core` (`example/src/example_app/core/presentation/di/core_di.py`) |
| A logger | registered in core DI, injected by constructor (`style/logging_conventions.md`) |

## Presentation

| You need to… | Do |
|---|---|
| HTTP endpoints | FastAPI router in `presentation/api/`, Pydantic schemas in `api/schemas/` (`presentation/presentation_patterns.md`) |
| CLI commands | Typer group in `presentation/cli/`, `asyncio.run(use_case(...))` |
| Map `Failure` to HTTP | in the router, with `http.HTTPStatus` |
| Several adapters | each in its folder; a second root module (`api.py` next to `main.py`) |

## Style, tests, git

| You need to… | Do |
|---|---|
| A constant | in the owning class, or a `<Name>Text` / `<Feature>Di` class for module functions (`style/constants.md`) |
| Docstrings | Google style on every public class, function, method and `__call__` (`style/docstring_standard.md`) |
| Test a use case | a hand-written fake that inherits the domain ABC (`testing/testing.md`) |
| Test a repository | an in-memory or fake data source |
| Test an adapter | `TestClient(create_app())` / `CliRunner` over the app, or fakes registered in the container |
| Commit, branch, release | `git/git_rules.md` |
| Ignore a lint rule | only when the user asks (`--ignore`); for good: a new template version with it in `[lint] off` |
