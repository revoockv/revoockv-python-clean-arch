# Logging conventions (stdlib `logging`)

- One application `logging.Logger`, configured and registered in
  `core/presentation/di/core_di.py` by `register_core(container)` — the first call in
  `register_and_init()`.
- That is the **only** place allowed to call `logging.basicConfig` / `logging.getLogger`
  (`logger_injection` rule).
- The logger is injected via **constructor parameter** into every repository implementation
  (and any data source that needs it) — never fetched from the container inside the class.

```python
class SongRepositoryImpl(SongRepository):
    """``SongRepository`` backed by the songs API."""

    def __init__(self, *, data_source: SongDataSource, logger: logging.Logger) -> None:
        self._data_source = data_source
        self._logger = logger
```

```python
container.register_singleton(
    SongRepository,
    SongRepositoryImpl(data_source=container.get(SongDataSource), logger=container.get(logging.Logger)),
)
```

## What to log (`repository_logging` rule)

Log **every public method** of a repository implementation, on both paths:

- Success: a human-readable description, not the repr of the result.
  `self._logger.info("AddSong: success — song %s by %s added", title, author)`
- Failure: the error — its details go here, never into the `Failure`.
  `self._logger.error("AddSong: failure — %s", e)`
- Early returns / expected empties: warning with the reason.
  `self._logger.warning("GetCurrentUser: success — nobody is signed in")`
- Init / startup: when subscriptions or connections begin.
  `self._logger.info("SongRepository init: connected to %s", url)`

Format: `MethodName: <status> — <description>`

- Status: `starting`, `success`, `failure`, `failed`.
- Include relevant identifiers (IDs, names, sizes). Never log secrets, passwords or tokens.
- Use %-style arguments (`logger.info("x %s", value)`), not f-strings — ruff rule `G004`
  enforces this and formatting stays lazy.
- Use `self._logger.exception(...)` inside `except` when the traceback matters (unexpected errors).

Use cases and presentation adapters do not log by default; the repository already has.
