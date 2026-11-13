# DI patterns (manual composition root + typed Container)

No DI framework. `core/presentation/di/container.py` provides a small typed `Container`
(the GetIt equivalent) and the app-wide `container` instance. Everything else uses
constructor injection.

## Container API

```python
container.register_singleton(AuthRepository, AuthRepositoryImpl(...))   # eager, shared
container.register_lazy_singleton(HttpClient, lambda: HttpClient(...))   # created on first get
container.register_factory(UnitOfWork, lambda: UnitOfWork(...))          # new instance per get
container.register_singleton(Settings, settings, name="auth.settings")   # named instance

container.get(AuthRepository)              # -> AuthRepository (typed)
container.get(Settings, name="auth.settings")
container.is_registered(AuthRepository)
container.reset()                          # register_and_init() and tests
```

- Keys are `(interface, name)`. Register implementations under their **domain interface**
  (`AuthRepository`, not `AuthRepositoryImpl`); data sources under their data-source ABC.
- Registering the same key twice raises `ValueError`; a missing key raises `LookupError`.
- mypy's `type-abstract` check is disabled in `pyproject.toml` because the container is keyed
  by ABCs on purpose.
- Instance names follow `feature.subfeature.name` (`auth.session.timeout`) and are declared as
  class constants in `<Feature>Di`, never inline strings.

## Data sources vs services

- **Data source** (`data/data_sources/`): where data lives — an API, a DB, a file store. Usually has an
  ABC so it can be swapped (in-memory ↔ HTTP).
- **Service** (`data/services/`, optional): a technology adapter that *does* something — converts a
  file with a library, runs a CLI tool, calls a model. One service per library/tool.
- Both may raise; both receive `logger` by constructor when they log; both are registered in
  `<feature>_di.py` and injected into repository implementations. Only repositories convert their
  exceptions into `Failure`.

## Rule: who may touch the container (`container_access`)

- `presentation/di/*` modules (any feature or core) and root modules (`di.py`, `main.py`).
- Nobody else. Domain and data receive dependencies through `__init__`; presentation adapters
  call getters.

## Rule: per-feature register (+ optional init)

`features/<feature>/presentation/di/<feature>_di.py` must define `register_<feature>(container)`.
Order inside: data sources → repositories → use cases.

```python
def register_auth(container: Container) -> None:
    """Register data sources, repositories and use cases of the auth feature."""
    container.register_singleton(AuthDataSource, HttpAuthDataSource(base_url=AuthDi.BASE_URL))
    container.register_singleton(
        AuthRepository,
        AuthRepositoryImpl(
            data_source=container.get(AuthDataSource),
            logger=container.get(logging.Logger),
        ),
    )
    repository = container.get(AuthRepository)
    container.register_singleton(SignInUseCase, SignInUseCase(repository))
    container.register_singleton(SignOutUseCase, SignOutUseCase(repository))
```

`async def init_<feature>(container)` is **optional** — only when the feature needs one-time
startup work: opening a DB pool, warming a cache, starting a background subscription.

```python
async def init_song(container: Container) -> None:
    """Open the songs database pool. Side effect: network connection."""
    await container.get(SongDataSource).connect()
```

If a feature needs shutdown work, add `async def close_<feature>(container)` and call it from
the adapter's shutdown hook (FastAPI lifespan after `yield`).

## Rule: getters are the presentation's only door

`features/<feature>/presentation/di/<feature>_getters.py`:

```python
def sign_in_use_case() -> SignInUseCase:
    """Return the registered ``SignInUseCase``."""
    return container.get(SignInUseCase)
```

- One getter per use case, named after it in snake_case.
- Getters resolve at **call time**, so tests can reset/re-register the container freely.
- Adapters import getters, never `domain/use_cases`, `domain/repositories`, `data/*` or the container.

## Rule: `di.py` orchestrates everything

```python
async def register_and_init() -> None:
    """Reset the container, register all dependencies and run feature initiations."""
    container.reset()
    register_core(container)
    # <features>
    register_auth(container)
    register_song(container)
    await init_song(container)
    # </features>
```

- `register_core` first (logger, settings, shared HTTP clients).
- Features in dependency order: a feature whose use cases need another feature's repository
  is registered after it.
- `init_project.py` creates the `# <features>` markers; `init_feature.py` inserts the import and the
  `register_<feature>(container)` call. Add `await init_<feature>(container)` by hand when needed.

## Rule: entry points call only `register_and_init()`

- Plain: `asyncio.run(main())` where `main()` awaits `register_and_init()`.
- FastAPI: `lifespan` awaits `register_and_init()` before `yield`.
- Typer: the `@app.callback()` runs `asyncio.run(register_and_init())`.

## Settings / environment

Configuration read from the environment is a core concern: create
`core/domain/entities/settings.py` (frozen dataclass), build it in `register_core` from
`os.environ` (or `pydantic-settings` inside `core/presentation/di/`), and register it as a
singleton. Repositories and data sources receive the values they need by constructor.
