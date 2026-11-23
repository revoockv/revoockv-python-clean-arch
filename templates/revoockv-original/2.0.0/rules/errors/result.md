# Result and failures (required)

Expected failures are values, not exceptions: every repository method and use case returns `Result[T, F]` — `T` the
value, `F` the failure type of the feature.

`src/my_app/core/domain/entities/result.py` (copied into a new project by `init_project.py`)

```python
"""Result type for expected success/failure outcomes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Success[T]:
    """Successful outcome carrying a value (use ``Success(None)`` for commands)."""

    value: T


@dataclass(frozen=True, slots=True)
class Failure[F]:
    """Failed outcome carrying why it failed: a member of the feature's failure type, never text."""

    failure: F


type Result[T, F] = Success[T] | Failure[F]
"""Return type of every repository method and use case that can fail in an expected way."""
```

## The failure type of a feature

`domain/entities/<feature>_failure.py`: what went wrong, never how to say it.

- An `Enum` when a failure carries nothing: `example/src/example_app/features/notes/domain/entities/note_failure.py`.
- Frozen dataclasses joined by `type <Feature>Failure = A | B` when one carries data the text needs
  (`FileTooBig(megabytes)`).
- Each failure has a `kind` property → `FailureKind` (core): `INVALID_INPUT`, `NOT_FOUND`, `CONFLICT`,
  `UNAUTHORIZED`, `FORBIDDEN`, `UNEXPECTED` — `example/src/example_app/core/domain/entities/failure_kind.py`.
- No text in domain or data. Technical details (`e`, tracebacks) go to the logger, never into the failure.

## Where each part lives

| Part | Where |
|---|---|
| `Failure(NoteFailure.EMPTY_TEXT)` for a broken business rule | the use case |
| exception → `Failure(<member>)`: a known exception → its member, anything else → the `UNEXPECTED` one | the repository implementation, the only `try` |
| the text of every failure: `<Feature>FailureText.of(failure)` with an exhaustive `match` | `presentation/text/<feature>_failure_text.py` — `example/src/example_app/features/notes/presentation/text/note_failure_text.py` |
| `FailureKind` → HTTP status, once for every router | `example/src/example_app/core/presentation/api/failure_status.py` (FastAPI projects copy it) |

A use case that passes on another feature's failure turns it into its own member first.

## Rules

- Commands return `Result[None, F]` and succeed with `Success(None)`.
- "Not found" that is a normal outcome is `Success(None)` with `Result[T | None, F]`; when the caller asked for one
  record, it is a `NOT_FOUND` failure.
- Use cases never catch. Unexpected bugs still raise — `Result` is for expected outcomes only.
- The linter's `typed_failures` (on in this template) fails `Result[T]` without `F` and `Failure(<text>)`.

## Consuming a Result — always `match`

```python
match await use_case(text=text):
    case Success(note):
        ...                                     # note is Note
    case Failure(failure):
        raise _http_error(failure)              # FailureStatus.of(failure.kind), NoteFailureText.of(failure)
```

mypy (`--strict`) checks that both cases, and every member in `FailureText.of`, are handled. To narrow
`Success[T | None]`, use a class pattern first: `case Success(Note() as note):`, then `case Success():`.

Quick propagation without `match`: `if isinstance(result, Failure): return result`. No `.is_success` / `.value`
helpers: pattern matching keeps the type checker in charge.
