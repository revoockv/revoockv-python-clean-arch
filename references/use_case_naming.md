# Use cases (required)

## What a use case is

**A use case is one interaction between the user and the application interface** — something the
user asks the app to do: *sign in*, *convert these files to Markdown*, *add a song*. It is NOT a step
of an implementation and NOT a mirror of every repository method.

- Name use cases after what the user wants, not after how it is done.
- Internal steps (detecting a format, choosing a pipeline, splitting a PDF, calling a model, retrying,
  merging) belong in the repository implementation and its services, never in extra use cases.
- Do not create a use case per repository method. One user interaction usually maps to one use case
  that calls one repository method (or a few, when the interaction spans repositories).
- Do not split one user interaction into several "helper" use cases chained together; if a use case
  needs another use case to do its job, the logic belongs in the repository.
- A small app may have a single use case (e.g. `ConvertToMdUseCase` in an "anything to Markdown"
  tool): one CLI command → one use case → one repository that orchestrates many services.

Litmus test: *would a user describe this as something they asked the app to do?* If not, it is not a
use case.

## Naming

- Class: `<Action>UseCase` — `SignInUseCase`, `AddSongUseCase`, `GetCurrentUserUseCase`.
- File: `<snake_case_action>_use_case.py` — `sign_in_use_case.py`, `add_song_use_case.py`.
- Location: `src/<package>/features/<feature>/domain/use_cases/`.
- Getter: `<snake_case_action>_use_case()` in `<feature>_getters.py`.
- Query use cases start with `get_` / `list_` / `find_`; commands use a verb (`add_`, `delete_`, `sign_in_`).

The linter derives the expected class name from the file name (`naming_class`).

## Shape

```python
class AddSongUseCase:
    """Adds a song to the current user's library."""

    _EMPTY_TITLE_ERROR = "Title must not be empty"

    def __init__(self, repository: SongRepository) -> None:
        self._repository = repository

    async def __call__(self, *, title: str, author: str) -> Result[Song]:
        """Add a song; fails when the title is empty."""
        if not title.strip():
            return Failure(self._EMPTY_TITLE_ERROR)
        return await self._repository.add_song(title=title, author=author)
```

Rules (`use_case_shape`, `use_case_no_try`, `import_violation`):

- Exactly one class per file; the only public method is `__call__` (async when the repository is async).
- Dependencies (domain repository interfaces, other use cases) come in through `__init__`.
- No try/except — repositories already convert errors to `Failure`.
- Business rules live here (validation, combining repositories, policies). Mapping, I/O and
  framework code never do.
- Imports: stdlib, `core.domain`, own/other features' `domain` only.
- Keyword-only parameters (`*`) for anything beyond one obvious argument.
- Registered as singletons in `<feature>_di.py`; reached from presentation via getters.
- `__call__` must have a docstring.

## Using several repositories

When one user interaction genuinely spans features, the use case may depend on another feature's
domain repository (by its interface). Pass it in through the constructor in `<feature>_di.py`.
Prefer repositories over chaining other use cases:

```python
container.register_singleton(
    BackupLibraryUseCase,
    BackupLibraryUseCase(
        songs=container.get(SongRepository),      # from the song feature
        backups=container.get(BackupRepository),
    ),
)
```

Register the providing feature first in `di.py`.
