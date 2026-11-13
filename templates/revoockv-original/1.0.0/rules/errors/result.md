# Result (required)

Use `Result[T]` for expected success/failure instead of raising across layer boundaries.

Canonical location (copied into a new project by `init_project.py`, `[scaffold] core_files`):

`src/my_app/core/domain/entities/result.py`

```python
"""Result type for expected success/failure outcomes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Success[T]:
    """Successful outcome carrying a value (use ``Success(None)`` for commands)."""

    value: T


@dataclass(frozen=True, slots=True)
class Failure:
    """Failed outcome carrying a human-readable error message."""

    error: str


type Result[T] = Success[T] | Failure
"""Return type of every repository method and use case that can fail in an expected way."""
```

Import:

```python
from my_app.core.domain.entities.result import Failure, Result, Success
```

## Rules

- Commands return `Result[None]` and succeed with `Success(None)`.
- Queries return `Result[T]`; "not found" that is a normal outcome is `Success(None)` with
  `Result[T | None]`, not a `Failure`.
- Data sources may raise. Repository implementations catch and return `Failure(str(e))`
  (and log). Nothing above the repository raises for expected failures.
- Use cases never catch: they return `Failure(...)` for business-rule violations and otherwise
  pass the repository `Result` through.
- Unexpected bugs (programming errors) still raise — `Result` is for expected outcomes only.

## Consuming a Result — always `match`

```python
match await use_case(email=email, password=password):
    case Success(user):
        ...                                # user is AuthUser
    case Failure(error):
        ...                                # error is str
```

`mypy --strict` checks that both cases are handled when the function must return a value.

### Narrowing `Success[T | None]`

A value pattern (`case Success(None)`) does not narrow for mypy. Use a class pattern first:

```python
match await use_case():
    case Success(AuthUser() as user):
        return AuthUserResponse.from_entity(user)
    case Success():
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
    case Failure(error):
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error)
```

### Quick checks without `match`

```python
result = await repository.sign_out()
if isinstance(result, Failure):
    return result                          # propagate (types line up for Result[None])
```

Do not add `.is_success` / `.value` helpers that return `T | None`; pattern matching keeps
the type checker in charge.
