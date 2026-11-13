# Auth feature — domain

The worked feature of this template, part 1 of 4 (`auth_domain.md`, `auth_data.md`, `auth_presentation.md`, `auth_api.md`). It lives only in the rules: `selfcheck.py` writes every block whose label is a `src/my_app/…` path into a copy of `example/` and runs ruff, mypy and the linter on it. When unsure, copy it and rename only (`my_app` → your package).

It enforces:

- Domain is pure Python (stdlib + domain modules only).
- Use cases: one class, async `__call__`, no try/except, `Result` passed through.
- Business validation returns `Failure(...)`; messages are class constants.

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
```

Core `Result`, `Container` and `register_core`: `example/src/example_app/core/`.

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

## Domain — repository interface

An `ABC` with abstract methods only. Every method that can fail returns `Result[...]`. Keyword-only parameters (`*`) keep call sites explicit.

`src/my_app/features/auth/domain/repositories/auth_repository.py`

```python
"""Auth repository contract."""

from abc import ABC, abstractmethod

from my_app.core.domain.entities.result import Result
from my_app.features.auth.domain.entities.auth_user import AuthUser


class AuthRepository(ABC):
    """Signs users in and out and tracks the current session."""

    @abstractmethod
    async def sign_in(self, *, email: str, password: str) -> Result[AuthUser]:
        """Authenticate with email and password and start a session."""

    @abstractmethod
    async def sign_out(self) -> Result[None]:
        """End the current session."""

    @abstractmethod
    async def get_current_user(self) -> Result[AuthUser | None]:
        """Return the signed-in user, or ``None`` when nobody is signed in."""
```

---

## Domain — use cases

One class per file, a single async `__call__`, no try/except. Business validation returns `Failure(...)` directly (messages are class constants); otherwise the repository `Result` is passed through unchanged.

`src/my_app/features/auth/domain/use_cases/sign_in_use_case.py`

```python
"""Sign in use case."""

from my_app.core.domain.entities.result import Failure, Result
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class SignInUseCase:
    """Validates credentials and signs the user in."""

    _EMAIL_SEPARATOR = "@"
    _INVALID_EMAIL_ERROR = "Email is not valid"
    _EMPTY_PASSWORD_ERROR = "Password must not be empty"

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def __call__(self, *, email: str, password: str) -> Result[AuthUser]:
        """Sign in with email and password.

        Business validation returns ``Failure`` directly; everything else is the repository's
        ``Result`` passed through unchanged (no try/except here).
        """
        if self._EMAIL_SEPARATOR not in email:
            return Failure(self._INVALID_EMAIL_ERROR)
        if not password:
            return Failure(self._EMPTY_PASSWORD_ERROR)
        return await self._repository.sign_in(email=email, password=password)
```

`src/my_app/features/auth/domain/use_cases/sign_out_use_case.py`

```python
"""Sign out use case."""

from my_app.core.domain.entities.result import Result
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class SignOutUseCase:
    """Ends the current session."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def __call__(self) -> Result[None]:
        """Sign the current user out."""
        return await self._repository.sign_out()
```

`src/my_app/features/auth/domain/use_cases/get_current_user_use_case.py`

```python
"""Get current user use case."""

from my_app.core.domain.entities.result import Result
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class GetCurrentUserUseCase:
    """Reads the signed-in user."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def __call__(self) -> Result[AuthUser | None]:
        """Return the signed-in user, or ``None`` when nobody is signed in."""
        return await self._repository.get_current_user()
```

---

## Tests — use case with a hand-written fake repository

Prefer fakes implementing the domain ABC over mocks — the ABC guarantees the fake stays in sync.

`tests/features/auth/domain/use_cases/test_sign_in_use_case.py`

```python
from my_app.core.domain.entities.result import Failure, Result, Success
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository
from my_app.features.auth.domain.use_cases.sign_in_use_case import SignInUseCase


class FakeAuthRepository(AuthRepository):
    def __init__(self, sign_in_result: Result[AuthUser]) -> None:
        self.sign_in_result = sign_in_result
        self.sign_in_calls: list[tuple[str, str]] = []

    async def sign_in(self, *, email: str, password: str) -> Result[AuthUser]:
        self.sign_in_calls.append((email, password))
        return self.sign_in_result

    async def sign_out(self) -> Result[None]:
        return Success(None)

    async def get_current_user(self) -> Result[AuthUser | None]:
        return Success(None)


async def test_returns_repository_result_for_valid_credentials() -> None:
    user = AuthUser(id="1", email="a@b.c")
    repository = FakeAuthRepository(Success(user))

    result = await SignInUseCase(repository)(email="a@b.c", password="pw")

    assert result == Success(user)
    assert repository.sign_in_calls == [("a@b.c", "pw")]


async def test_rejects_invalid_email_without_calling_repository() -> None:
    repository = FakeAuthRepository(Success(AuthUser(id="1", email="a@b.c")))

    result = await SignInUseCase(repository)(email="not-an-email", password="pw")

    assert isinstance(result, Failure)
    assert repository.sign_in_calls == []
```
