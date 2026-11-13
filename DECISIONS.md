# Decision Table — "You need X → use pattern Y"

Use this table to find the right reference file or pattern without reading all references.

---

## Architecture & Layers

| You need to... | Read / use |
|---|---|
| Start a new project | `scripts/init_project.py` + `references/project_setup.md` |
| Understand the overall folder structure | `references/folder_structure.md` |
| Create a new feature from scratch | `scripts/init_feature.py` + `references/feature_template_auth.md` |
| Refactor an existing project/feature | `SKILL.md` → Workflow C + run the linter |
| Know which layer may import what | `references/imports.md` (dependency matrix) |
| Define a domain entity | frozen dataclass in `domain/entities/` — `feature_template_auth.md` |
| Define a repository interface | `ABC` in `domain/repositories/`, methods return `Result` |
| Decide whether something is a use case (= one user ↔ app interaction) | `references/use_case_naming.md` → What a use case is |
| Define / name a use case | `references/use_case_naming.md` |
| Combine several services in one operation | the repository implementation orchestrates them — not extra use cases |
| Share code between features | depend on the other feature's **domain** interface via the container |
| Put something used by every feature | `core/` (same layer layout as a feature) |

---

## Errors & Results

| You need to... | Read / use |
|---|---|
| Return success/failure | `references/result.md` |
| Consume a Result | `match` with `case Success(x)` / `case Failure(error)` |
| Narrow `Success[T \| None]` for mypy | `case Success(Entity() as x)` then `case Success()` — `result.md` |
| Decide where try/except goes | repository implementation only (data sources raise, use cases never catch) |
| Represent "not found" | `Success(None)` with `Result[T \| None]` when it is a normal outcome |

---

## Dependency Injection

| You need to... | Read / use |
|---|---|
| Register a feature's dependencies | `references/di_patterns.md` → `register_<feature>` |
| Run one-time startup work (DB pool, cache warmup) | `async init_<feature>(container)` + call it in `di.py` |
| Choose singleton vs lazy vs factory | `di_patterns.md` → Container API |
| Name an instance key | `feature.subfeature.name`, declared in `<Feature>Di` constants class |
| Expose use cases to presentation | `<feature>_getters.py` — one getter per use case |
| Wire the app entry point | `di.py` → `register_and_init()`; entry points call only that |
| Read settings / env vars | `di_patterns.md` → Settings (built in `register_core`) |
| Inject a logger | `references/logging_conventions.md` |

---

## Data Layer

| You need to... | Read / use |
|---|---|
| Call an HTTP API / DB / SDK | data source in `data/data_sources/` (ABC + impl) |
| Wrap a library / CLI tool (converter, ffmpeg, model) | service in `data/services/<name>_service.py` |
| Create a DTO / data model | `references/models_mapping.md` |
| Map DTO ↔ Entity | `to_entity()` / `from_entity()` in the model |
| Validate external payloads | Pydantic allowed in `data/models/` — never in domain |
| Convert exceptions to Failure + log | repository impl — `feature_template_auth.md` → Data — repository |
| Swap a backend (in-memory → HTTP) | new data source impl, change one line in `<feature>_di.py` |

---

## Presentation

| You need to... | Read / use |
|---|---|
| Add HTTP endpoints | `references/presentation_patterns.md` → FastAPI; `init_feature.py --adapter fastapi` |
| Add CLI commands | `presentation_patterns.md` → Typer; `init_feature.py --adapter typer` |
| Add a worker/bot/other adapter | `presentation_patterns.md` → Other adapters |
| Request/response schemas | Pydantic in `presentation/api/schemas/`, `from_entity` for responses |
| Map Failure to HTTP status | in the router with `http.HTTPStatus` |
| Avoid magic strings/numbers | `SKILL.md` → "Constants — inside the owning class" |

---

## Testing

| You need to... | Read / use |
|---|---|
| Test a use case | fake repository implementing the domain ABC — `references/testing.md` |
| Test a repository | fake / in-memory data source |
| Test an endpoint/command with fakes | register fakes in the container, drive the router — `testing.md` |
| Test the whole wiring | `with TestClient(create_app())` / `asyncio.run(register_and_init())` |

---

## Conventions & Quality

| You need to... | Read / use |
|---|---|
| Write docstrings | `references/docstring_standard.md` |
| Set up / write logs | `references/logging_conventions.md` |
| Organize imports | `references/imports.md` (absolute only) |
| Name files / classes | linter rules `naming_file`, `naming_class`; `folder_structure.md` → Rules |
| Run all checks | `SKILL.md` → "Automated checks" |
| Check if a rule can be ignored | only on explicit user request (`--ignore`) |
| Commit / branch / tag | `references/git_rules.md` |

---

## Workflows (Quick Reference)

### A) New project

```
1. init_project.py --name <n> --adapter <a>   → skeleton + core + di.py + main.py
2. uv add ... (printed by the script)        → dependencies
3. quality gate                              → must pass on the empty skeleton
```

### B) New feature

```
1. init_feature.py --feature <f> [--adapter]  → skeleton + DI stubs + wiring
2. use_case_naming.md                         → name use cases
3. domain: entities → repository ABC → use cases
4. models_mapping.md                          → DTOs + mapping
5. data: data sources → repository impl (Result + logging)
6. di_patterns.md                             → register_<feature> + getters
7. presentation_patterns.md                   → adapter
8. testing.md                                 → tests per layer
9. ruff + mypy + pytest + linter              → verify
```

### C) Refactor existing code

```
1. run linter                                 → baseline
2. feature_template_auth.md                   → target shape
3. refactor layer by layer, feature by feature
4. quality gate + linter --strict             → verify
```

---

## When in Doubt

> Copy the pattern from `references/feature_template_auth.md` and adapt naming only.
