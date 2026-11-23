# Auth feature — domain

The worked feature of this template, part 1 of 4 (`auth_domain.md`, `auth_data.md`, `auth_presentation.md`, `auth_api.md`). It lives only in the rules: `selfcheck.py` writes every block whose label is a `src/my_app/…` path into a copy of `example/` and runs ruff, mypy and the linter on it. When unsure, copy it and rename only (`my_app` → your package).

It enforces:

- Domain is pure Python (stdlib + domain modules only).
- Use cases: one class, async `__call__`, no try/except, `Result` passed through.
- Every failure is a member of `AuthFailure`; no text in domain or data (its text: `presentation/text/`).

## Layout

```
src/my_app/features/auth/
  data/
    data_sources/auth_data_source.py            AuthDataSource (ABC), AuthDataSourceError
    data_sources/in_memory_auth_data_source.py  InMemoryAuthDataSource
    models/auth_user_model.py                   AuthUserModel
    repositories/auth_repository_impl.py        AuthRepositoryImpl
  domain/
    entities/auth_user.py                       AuthUser
    entities/auth_failure.py                    AuthFailure (Enum)
    repositories/auth_repository.py             AuthRepository (ABC)
    use_cases/sign_in_use_case.py               SignInUseCase
    use_cases/sign_out_use_case.py              SignOutUseCase
    use_cases/get_current_user_use_case.py      GetCurrentUserUseCase
  presentation/
    di/auth_di.py                               register_auth(container)
    di/auth_getters.py                          sign_in_use_case(), ...
    api/auth_router.py                          FastAPI router
    api/schemas/sign_in_request.py              SignInRequest
    api/schemas/auth_user_response.py           AuthUserResponse
    cli/auth_commands.py                        Typer commands
    text/auth_failure_text.py                   AuthFailureText
```

Core `Result`, `FailureKind`, `FailureStatus`, `Container` and `register_core`: `example/src/example_app/core/`.

---

## Domain — entity

Frozen, slotted dataclass. Pure Python: no framework, no I/O, no data/presentation imports.

`src/my_app/features/auth/domain/entities/auth_user.py`

```python
"""Authenticated user entity."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthUser:
    """A user that has successfully signed in."""

    id: str
    email: str
```

---

## Domain — failure type

An `Enum` of everything that can go wrong in the feature, each member with its `FailureKind`. It says *what* went
wrong, never how to say it.

`src/my_app/features/auth/domain/entities/auth_failure.py`

```python
"""Failures of the auth feature."""

from enum import Enum, auto

from my_app.core.domain.entities.failure_kind import FailureKind


class AuthFailure(Enum):
    """Why an auth operation failed; the text for the user lives in presentation."""

    INVALID_EMAIL = auto()
    EMPTY_PASSWORD = auto()
    WRONG_CREDENTIALS = auto()
    BACKEND = auto()

    @property
    def kind(self) -> FailureKind:
        """The kind of this failure, for the adapters."""
        match self:
            case AuthFailure.INVALID_EMAIL | AuthFailure.EMPTY_PASSWORD:
                return FailureKind.INVALID_INPUT
            case AuthFailure.WRONG_CREDENTIALS:
                return FailureKind.UNAUTHORIZED
            case AuthFailure.BACKEND:
                return FailureKind.UNEXPECTED
```

---

## Domain — repository interface

An `ABC` with abstract methods only. Every method that can fail returns `Result[T, AuthFailure]`. Keyword-only parameters (`*`) keep call sites explicit.

`src/my_app/features/auth/domain/repositories/auth_repository.py`

```python
"""Auth repository contract."""

from abc import ABC, abstractmethod

from my_app.core.domain.entities.result import Result
from my_app.features.auth.domain.entities.auth_failure import AuthFailure
from my_app.features.auth.domain.entities.auth_user import AuthUser


class AuthRepository(ABC):
    """Signs users in and out and tracks the current session."""

    @abstractmethod
    async def sign_in(self, *, email: str, password: str) -> Result[AuthUser, AuthFailure]:
        """Authenticate with email and password and start a session."""

    @abstractmethod
    async def sign_out(self) -> Result[None, AuthFailure]:
        """End the current session."""

    @abstractmethod
    async def get_current_user(self) -> Result[AuthUser | None, AuthFailure]:
        """Return the signed-in user, or ``None`` when nobody is signed in."""
```

---

## Domain — use cases

One class per file, a single async `__call__`, no try/except. Business validation returns `Failure(AuthFailure.…)` directly; otherwise the repository `Result` is passed through unchanged.

`src/my_app/features/auth/domain/use_cases/sign_in_use_case.py`

```python
"""Sign in use case."""

from my_app.core.domain.entities.result import Failure, Result
from my_app.features.auth.domain.entities.auth_failure import AuthFailure
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class SignInUseCase:
    """Validates credentials and signs the user in."""

    _EMAIL_SEPARATOR = "@"

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def __call__(self, *, email: str, password: str) -> Result[AuthUser, AuthFailure]:
        """Sign in with email and password.

        Business validation returns ``Failure`` directly; everything else is the repository's
        ``Result`` passed through unchanged (no try/except here).
        """
        if self._EMAIL_SEPARATOR not in email:
            return Failure(AuthFailure.INVALID_EMAIL)
        if not password:
            return Failure(AuthFailure.EMPTY_PASSWORD)
        return await self._repository.sign_in(email=email, password=password)
```

`src/my_app/features/auth/domain/use_cases/sign_out_use_case.py`

```python
"""Sign out use case."""

from my_app.core.domain.entities.result import Result
from my_app.features.auth.domain.entities.auth_failure import AuthFailure
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class SignOutUseCase:
    """Ends the current session."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def __call__(self) -> Result[None, AuthFailure]:
        """Sign the current user out."""
        return await self._repository.sign_out()
```

`src/my_app/features/auth/domain/use_cases/get_current_user_use_case.py`

```python
"""Get current user use case."""

from my_app.core.domain.entities.result import Result
from my_app.features.auth.domain.entities.auth_failure import AuthFailure
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class GetCurrentUserUseCase:
    """Reads the signed-in user."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def __call__(self) -> Result[AuthUser | None, AuthFailure]:
        """Return the signed-in user, or ``None`` when nobody is signed in."""
        return await self._repository.get_current_user()
```

---

## Tests — use case with a hand-written fake repository

A fake that inherits `AuthRepository` and records its calls: `rules/testing/testing.md` (`FakeAuthRepository`), the
same shape as `example/tests/features/notes/fakes.py`.
