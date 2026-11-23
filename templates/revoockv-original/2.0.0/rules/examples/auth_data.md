# Auth feature — data

Part 2 of 4 of the worked feature (`auth_domain.md` first). Data sources may raise; the repository is the only place where their exceptions become `Failure(AuthFailure.…)` (the details go to the log, never into the failure), and it logs every public method. How to split a big data layer: `rules/data/data_design.md`.

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


class InvalidCredentialsError(AuthDataSourceError):
    """Raised when the backend rejects the email or the password."""


class AuthDataSource(ABC):
    """Talks to the auth backend. May raise; the repository converts errors to ``Failure``."""

    @abstractmethod
    async def sign_in(self, *, email: str, password: str) -> AuthUserModel:
        """Authenticate and return the user.

        Raises:
            InvalidCredentialsError: If the credentials are rejected.
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
    InvalidCredentialsError,
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
            raise InvalidCredentialsError(email)
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

Implements the domain interface. The ONLY place where data-source exceptions become `Failure`: a known exception → its member, anything else → `BACKEND`. Receives `logger` by constructor and logs every public method (`Method: status — description`). Maps models to entities before returning.

`src/my_app/features/auth/data/repositories/auth_repository_impl.py`

```python
"""Auth repository implementation."""

import logging

from my_app.core.domain.entities.result import Failure, Result, Success
from my_app.features.auth.data.data_sources.auth_data_source import (
    AuthDataSource,
    InvalidCredentialsError,
)
from my_app.features.auth.domain.entities.auth_failure import AuthFailure
from my_app.features.auth.domain.entities.auth_user import AuthUser
from my_app.features.auth.domain.repositories.auth_repository import AuthRepository


class AuthRepositoryImpl(AuthRepository):
    """``AuthRepository`` over an ``AuthDataSource``; turns exceptions into ``AuthFailure``."""

    def __init__(self, *, data_source: AuthDataSource, logger: logging.Logger) -> None:
        self._data_source = data_source
        self._logger = logger

    async def sign_in(self, *, email: str, password: str) -> Result[AuthUser, AuthFailure]:
        """Authenticate via the data source and map the model to an entity."""
        try:
            model = await self._data_source.sign_in(email=email, password=password)
        except InvalidCredentialsError:
            self._logger.warning("SignIn: failure — wrong credentials for %s", email)
            return Failure(AuthFailure.WRONG_CREDENTIALS)
        except Exception as e:
            self._logger.error("SignIn: failure — %s", e)
            return Failure(AuthFailure.BACKEND)
        self._logger.info("SignIn: success — user %s signed in", model.email)
        return Success(model.to_entity())

    async def sign_out(self) -> Result[None, AuthFailure]:
        """End the session via the data source."""
        try:
            await self._data_source.sign_out()
        except Exception as e:
            self._logger.error("SignOut: failure — %s", e)
            return Failure(AuthFailure.BACKEND)
        self._logger.info("SignOut: success — session ended")
        return Success(None)

    async def get_current_user(self) -> Result[AuthUser | None, AuthFailure]:
        """Read the session user from the data source."""
        try:
            model = await self._data_source.current_user()
        except Exception as e:
            self._logger.error("GetCurrentUser: failure — %s", e)
            return Failure(AuthFailure.BACKEND)
        if model is None:
            self._logger.warning("GetCurrentUser: success — nobody is signed in")
            return Success(None)
        self._logger.info("GetCurrentUser: success — user %s", model.email)
        return Success(model.to_entity())
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
from my_app.features.auth.domain.entities.auth_failure import AuthFailure
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

    assert result == Failure(AuthFailure.WRONG_CREDENTIALS)
```
