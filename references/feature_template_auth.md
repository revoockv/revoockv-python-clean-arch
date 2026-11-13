# Auth feature template (golden path)

Every file below is copied from a project that passes `ruff check`, `ruff format --check`,
`mypy --strict`, `pytest` and `py_clean_arch_linter.py --strict`. When unsure, copy it and
rename only. Replace `my_app` with your package name.

It enforces:

- Domain is pure Python (stdlib + domain modules only).
- Data sources may raise; repositories convert exceptions to `Failure` and log.
- Use cases: one class, async `__call__`, no try/except, `Result` passed through.
- Models (DTOs) map to/from entities in the model class.
- Presentation reaches use cases only through `<feature>_getters.py`.
- Adapters (`api/`, `cli/`) are thin: input → use case → `match Result` → output.

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

Core `Result`, `Container` and `register_core` are in `references/result.md` and
`references/di_patterns.md`.

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

## Data — model (DTO)

Technology-shaped representation. Maps both ways: `to_entity()` and `from_entity()` (classmethod). Wire (de)serialization (`from_dict`/`to_dict`) lives here too. JSON keys are exempt from the magic-strings rule because the data layer is not checked for it.

`src/my_app/features/auth/data/models/auth_user_model.py`

```python
"""Auth user DTO."""

from dataclasses import dataclass
from typing import Any, Self

from my_app.features.auth.domain.entities.auth_user import AuthUser


@dataclass(frozen=True, slots=True)
class AuthUserModel:
    """Wire/storage representation of a user, mapped to and from ``AuthUser``."""

    id: str
    email: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build the model from a JSON-like dict returned by a data source."""
        return cls(id=str(data["id"]), email=str(data["email"]))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the model to a JSON-like dict."""
        return {"id": self.id, "email": self.email}

    @classmethod
    def from_entity(cls, entity: AuthUser) -> Self:
        """Build the model from a domain entity."""
        return cls(id=entity.id, email=entity.email)

    def to_entity(self) -> AuthUser:
        """Map the model to a domain entity."""
        return AuthUser(id=self.id, email=self.email)
```

---

## Data — data source (interface + implementation)

Talks to the outside world (HTTP, DB, SDK, files) and returns models. Data sources MAY raise — that is their contract. Swap `InMemoryAuthDataSource` for an `HttpAuthDataSource` / `SqlAuthDataSource` without touching domain or presentation.

`src/my_app/features/auth/data/data_sources/auth_data_source.py`

```python
"""Auth data source contract."""

from abc import ABC, abstractmethod

from my_app.features.auth.data.models.auth_user_model import AuthUserModel


class AuthDataSourceError(Exception):
    """Raised by auth data sources when an operation fails."""


class AuthDataSource(ABC):
    """Talks to the auth backend. May raise; the repository converts errors to ``Failure``."""

    @abstractmethod
    async def sign_in(self, *, email: str, password: str) -> AuthUserModel:
        """Authenticate and return the user.

        Raises:
            AuthDataSourceError: If the credentials are rejected.
        """

    @abstractmethod
    async def sign_out(self) -> None:
        """End the backend session."""

    @abstractmethod
    async def current_user(self) -> AuthUserModel | None:
        """Return the user of the active session, if any."""
```

`src/my_app/features/auth/data/data_sources/in_memory_auth_data_source.py`

```python
"""In-memory auth data source (development and tests)."""

from my_app.features.auth.data.data_sources.auth_data_source import (
    AuthDataSource,
    AuthDataSourceError,
)
from my_app.features.auth.data.models.auth_user_model import AuthUserModel


class InMemoryAuthDataSource(AuthDataSource):
    """Keeps users and the active session in memory."""

    def __init__(self, users: dict[str, tuple[str, str]]) -> None:
        """Create the data source from ``{email: (user_id, password)}``."""
        self._users = users
        self._session: AuthUserModel | None = None

    async def sign_in(self, *, email: str, password: str) -> AuthUserModel:
        """Authenticate against the in-memory users."""
        stored = self._users.get(email)
        if stored is None or stored[1] != password:
            raise AuthDataSourceError("invalid email or password")
        self._session = AuthUserModel.from_dict({"id": stored[0], "email": email})
        return self._session

    async def sign_out(self) -> None:
        """Clear the in-memory session."""
        self._session = None

    async def current_user(self) -> AuthUserModel | None:
        """Return the in-memory session user."""
        return self._session
```

---

## Data — repository implementation

Implements the domain interface. The ONLY place where data-source exceptions become `Failure`. Receives `logger` by constructor and logs every public method (`Method: status — description`). Maps models to entities before returning.

`src/my_app/features/auth/data/repositories/auth_repository_impl.py`

```python
"""Auth repository implementation."""

import logging

from my_app.core.domain.entities.result import Failure, Result, Success
from my_app.features.auth.data.data_sources.auth_data_source import AuthDataSource
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class AuthRepositoryImpl(AuthRepository):
    """``AuthRepository`` backed by an ``AuthDataSource``; converts exceptions to ``Failure``."""

    def __init__(self, *, data_source: AuthDataSource, logger: logging.Logger) -> None:
        self._data_source = data_source
        self._logger = logger

    async def sign_in(self, *, email: str, password: str) -> Result[AuthUser]:
        """Authenticate via the data source and map the model to an entity."""
        try:
            model = await self._data_source.sign_in(email=email, password=password)
        except Exception as e:
            self._logger.error("SignIn: failure — %s", e)
            return Failure(str(e))
        self._logger.info("SignIn: success — user %s signed in", model.email)
        return Success(model.to_entity())

    async def sign_out(self) -> Result[None]:
        """End the session via the data source."""
        try:
            await self._data_source.sign_out()
        except Exception as e:
            self._logger.error("SignOut: failure — %s", e)
            return Failure(str(e))
        self._logger.info("SignOut: success — session ended")
        return Success(None)

    async def get_current_user(self) -> Result[AuthUser | None]:
        """Read the session user from the data source."""
        try:
            model = await self._data_source.current_user()
        except Exception as e:
            self._logger.error("GetCurrentUser: failure — %s", e)
            return Failure(str(e))
        if model is None:
            self._logger.warning("GetCurrentUser: success — nobody is signed in")
            return Success(None)
        self._logger.info("GetCurrentUser: success — user %s", model.email)
        return Success(model.to_entity())
```

---

## Presentation — DI registration

Registers data sources → repository (keyed by the domain interface) → use cases. Config values live in a small `<Feature>Di` class. Wired into `di.py` by `init_feature.py`.

`src/my_app/features/auth/presentation/di/auth_di.py`

```python
"""DI registration for the auth feature."""

import logging
from typing import ClassVar

from my_app.core.presentation.di.container import Container
from my_app.features.auth.data.data_sources.auth_data_source import AuthDataSource
from my_app.features.auth.data.data_sources.in_memory_auth_data_source import (
    InMemoryAuthDataSource,
)
from my_app.features.auth.data.repositories.auth_repository_impl import AuthRepositoryImpl
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository
from my_app.features.auth.domain.use_cases.get_current_user_use_case import (
    GetCurrentUserUseCase,
)
from my_app.features.auth.domain.use_cases.sign_in_use_case import SignInUseCase
from my_app.features.auth.domain.use_cases.sign_out_use_case import SignOutUseCase


class AuthDi:
    """Configuration values used by ``register_auth``."""

    DEMO_USERS: ClassVar[dict[str, tuple[str, str]]] = {"demo@example.com": ("1", "secret")}


def register_auth(container: Container) -> None:
    """Register data sources, repositories and use cases of the auth feature.

    Order: data sources → repositories (by domain interface) → use cases.
    """
    container.register_singleton(AuthDataSource, InMemoryAuthDataSource(dict(AuthDi.DEMO_USERS)))
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
    container.register_singleton(GetCurrentUserUseCase, GetCurrentUserUseCase(repository))
```

---

## Presentation — getters

One function per use case. This is the only door from presentation code into the domain: adapters call `sign_in_use_case()` and never import the container or `domain/use_cases` themselves.

`src/my_app/features/auth/presentation/di/auth_getters.py`

```python
"""Getters through which the auth presentation layer reaches its use cases.

Presentation code imports these functions instead of touching the container or the domain
use case modules directly.
"""

from my_app.core.presentation.di.container import container
from my_app.features.auth.domain.use_cases.get_current_user_use_case import (
    GetCurrentUserUseCase,
)
from my_app.features.auth.domain.use_cases.sign_in_use_case import SignInUseCase
from my_app.features.auth.domain.use_cases.sign_out_use_case import SignOutUseCase


def sign_in_use_case() -> SignInUseCase:
    """Return the registered ``SignInUseCase``."""
    return container.get(SignInUseCase)


def sign_out_use_case() -> SignOutUseCase:
    """Return the registered ``SignOutUseCase``."""
    return container.get(SignOutUseCase)


def get_current_user_use_case() -> GetCurrentUserUseCase:
    """Return the registered ``GetCurrentUserUseCase``."""
    return container.get(GetCurrentUserUseCase)
```

---

## Presentation — FastAPI adapter (`presentation/api/`)

Thin: parse input (Pydantic schema) → call the use case via its getter → `match` the `Result` → map to an HTTP response. Response schemas map from entities with `from_entity`. Status codes come from `http.HTTPStatus` (no magic numbers). Note `case Success(AuthUser() as user)` — a class pattern is needed for mypy to narrow `AuthUser | None`.

`src/my_app/features/auth/presentation/api/schemas/sign_in_request.py`

```python
"""Sign in request body."""

from pydantic import BaseModel


class SignInRequest(BaseModel):
    """Credentials posted to ``POST /auth/sign-in``."""

    email: str
    password: str
```

`src/my_app/features/auth/presentation/api/schemas/auth_user_response.py`

```python
"""Auth user response body."""

from typing import Self

from pydantic import BaseModel

from my_app.features.auth.domain.entities.auth_user import AuthUser


class AuthUserResponse(BaseModel):
    """Public representation of a signed-in user."""

    id: str
    email: str

    @classmethod
    def from_entity(cls, entity: AuthUser) -> Self:
        """Build the response from a domain entity."""
        return cls(id=entity.id, email=entity.email)
```

`src/my_app/features/auth/presentation/api/auth_router.py`

```python
"""HTTP routes of the auth feature."""

from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from my_app.core.domain.entities.result import Failure, Success
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.presentation.api.schemas.auth_user_response import AuthUserResponse
from my_app.features.auth.presentation.api.schemas.sign_in_request import SignInRequest
from my_app.features.auth.presentation.di.auth_getters import (
    get_current_user_use_case,
    sign_in_use_case,
    sign_out_use_case,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-in")
async def sign_in(body: SignInRequest) -> AuthUserResponse:
    """Sign in and return the user; 401 with the error message on failure."""
    use_case = sign_in_use_case()
    match await use_case(email=body.email, password=body.password):
        case Success(user):
            return AuthUserResponse.from_entity(user)
        case Failure(error):
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=error)


@router.post("/sign-out", status_code=HTTPStatus.NO_CONTENT)
async def sign_out() -> None:
    """End the current session; 500 with the error message on failure."""
    use_case = sign_out_use_case()
    match await use_case():
        case Success():
            return
        case Failure(error):
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error)


@router.get("/me")
async def me() -> AuthUserResponse:
    """Return the signed-in user; 401 when nobody is signed in."""
    use_case = get_current_user_use_case()
    match await use_case():
        case Success(AuthUser() as user):
            return AuthUserResponse.from_entity(user)
        case Success():
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
        case Failure(error):
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error)
```

---

## Presentation — Typer adapter (`presentation/cli/`)

Same shape as the router: getter → use case → `match` → `typer.echo` / `typer.Exit(code=1)`. Async use cases run with `asyncio.run`. User-facing text lives in a constants class.

`src/my_app/features/auth/presentation/cli/auth_commands.py`

```python
"""CLI commands of the auth feature."""

import asyncio
from typing import Annotated

import typer

from my_app.core.domain.entities.result import Failure, Success
from my_app.features.auth.presentation.di.auth_getters import sign_in_use_case

commands = typer.Typer(help="Auth commands.", no_args_is_help=True)


class AuthCommandsText:
    """User-facing CLI text of the auth commands."""

    SIGNED_IN = "Signed in as {email}"


@commands.command("sign-in")
def sign_in(
    email: Annotated[str, typer.Option(help="Account email.")],
    password: Annotated[str, typer.Option(prompt=True, hide_input=True)],
) -> None:
    """Sign in with email and password; exits with code 1 on failure."""
    use_case = sign_in_use_case()
    match asyncio.run(use_case(email=email, password=password)):
        case Success(user):
            typer.echo(AuthCommandsText.SIGNED_IN.format(email=user.email))
        case Failure(error):
            typer.echo(error, err=True)
            raise typer.Exit(code=1)
```

---

## Wiring — `di.py` and `main.py` (FastAPI)

Generated by `init_project.py`; `init_feature.py` inserts imports and calls between the `# <features>` / `# <routers>` markers.

`src/my_app/di.py`

```python
"""Main DI: registers core and every feature, then runs one-time initiations."""

from my_app.core.presentation.di.container import container
from my_app.core.presentation.di.core_di import register_core
from my_app.features.auth.presentation.di.auth_di import register_auth


async def register_and_init() -> None:
    """Reset the container, register all dependencies and run feature initiations.

    The single DI entry point; ``main.py`` calls nothing else.
    """
    container.reset()
    register_core(container)
    # <features>
    register_auth(container)
    # </features>
```

`src/my_app/main.py`

```python
"""Application entry point (FastAPI). Run: uv run uvicorn my_app.main:app --reload."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from my_app.di import register_and_init
from my_app.features.auth.presentation.api.auth_router import router as auth_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Register dependencies and run initiations before serving requests."""
    await register_and_init()
    yield


def create_app() -> FastAPI:
    """Build the FastAPI application and include every feature router."""
    app = FastAPI(lifespan=lifespan)
    # <routers>
    app.include_router(auth_router)
    # </routers>
    return app


app = create_app()
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

---

## Tests — repository with a real/fake data source

`tests/features/auth/data/repositories/test_auth_repository_impl.py`

```python
import logging

from my_app.core.domain.entities.result import Failure, Success
from my_app.features.auth.data.data_sources.in_memory_auth_data_source import (
    InMemoryAuthDataSource,
)
from my_app.features.auth.data.repositories.auth_repository_impl import AuthRepositoryImpl
from my_app.features.auth.domain.entities.auth_user import AuthUser


def _repository() -> AuthRepositoryImpl:
    return AuthRepositoryImpl(
        data_source=InMemoryAuthDataSource({"a@b.c": ("1", "pw")}),
        logger=logging.getLogger("test"),
    )


async def test_sign_in_maps_model_to_entity() -> None:
    result = await _repository().sign_in(email="a@b.c", password="pw")

    assert result == Success(AuthUser(id="1", email="a@b.c"))


async def test_sign_in_converts_data_source_error_to_failure() -> None:
    result = await _repository().sign_in(email="a@b.c", password="wrong")

    assert isinstance(result, Failure)
```

---

## Tests — adapters end-to-end

`TestClient(create_app())` runs the lifespan, so `register_and_init()` wires the real container. To replace a dependency, call `register_and_init()` first and then re-register in a fresh container, or register fakes after `container.reset()` (see `references/testing.md`).

`tests/features/auth/presentation/test_auth_router.py`

```python
from fastapi.testclient import TestClient

from my_app.main import create_app


def test_sign_in_then_me() -> None:
    with TestClient(create_app()) as client:
        assert client.get("/auth/me").status_code == 401

        response = client.post(
            "/auth/sign-in", json={"email": "demo@example.com", "password": "secret"}
        )
        assert response.status_code == 200
        assert response.json() == {"id": "1", "email": "demo@example.com"}

        assert client.get("/auth/me").json()["email"] == "demo@example.com"


def test_sign_in_failure_returns_401() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/auth/sign-in", json={"email": "x@y.z", "password": "bad"})

    assert response.status_code == 401
```

`tests/features/auth/presentation/test_auth_commands.py`

```python
import asyncio

import typer
from typer.testing import CliRunner

from my_app.di import register_and_init
from my_app.features.auth.presentation.cli.auth_commands import commands


def test_sign_in_command() -> None:
    asyncio.run(register_and_init())
    app = typer.Typer()
    app.add_typer(commands, name="auth")

    result = CliRunner().invoke(
        app, ["auth", "sign-in", "--email", "demo@example.com", "--password", "secret"]
    )

    assert result.exit_code == 0
    assert "demo@example.com" in result.output
```
