# Auth feature — presentation

Part 3 of 4 of the worked feature (part 4, the FastAPI adapter: `auth_api.md`). DI registers data sources → repository (by its domain interface) → use cases; getters are the only door from adapters into the domain; adapters are thin: input → getter → use case → `match` Result → output.

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

## Presentation — failure text (`presentation/text/`)

The text of every failure lives in presentation, in one class per failure type. The exhaustive `match` makes mypy
fail when a new member has no text. Every adapter (CLI, HTTP) uses it.

`src/my_app/features/auth/presentation/text/auth_failure_text.py`

```python
"""User-facing text of the auth failures."""

from my_app.features.auth.domain.entities.auth_failure import AuthFailure


class AuthFailureText:
    """The text of every ``AuthFailure``; a new member without a text fails mypy."""

    _INVALID_EMAIL = "Email is not valid"
    _EMPTY_PASSWORD = "Password must not be empty"
    _WRONG_CREDENTIALS = "Wrong email or password"
    _BACKEND = "Signing in is not available now"

    @classmethod
    def of(cls, failure: AuthFailure) -> str:
        """Return the text that tells the user about ``failure``."""
        match failure:
            case AuthFailure.INVALID_EMAIL:
                return cls._INVALID_EMAIL
            case AuthFailure.EMPTY_PASSWORD:
                return cls._EMPTY_PASSWORD
            case AuthFailure.WRONG_CREDENTIALS:
                return cls._WRONG_CREDENTIALS
            case AuthFailure.BACKEND:
                return cls._BACKEND
```

---

## Presentation — Typer adapter (`presentation/cli/`)

Same shape as the router: getter → use case → `match` → `typer.echo` / `typer.Exit(code=1)` with the failure's text. Async use cases run with `asyncio.run`. User-facing text lives in a constants class.

`src/my_app/features/auth/presentation/cli/auth_commands.py`

```python
"""CLI commands of the auth feature."""

import asyncio
from typing import Annotated

import typer

from my_app.core.domain.entities.result import Failure, Success
from my_app.features.auth.presentation.di.auth_getters import sign_in_use_case
from my_app.features.auth.presentation.text.auth_failure_text import AuthFailureText

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
        case Failure(failure):
            typer.echo(AuthFailureText.of(failure), err=True)
            raise typer.Exit(code=1)
```

---

## Wiring — `di.py` and the entry point

`init_feature.py --feature auth --adapter fastapi` (or `typer`) inserts these lines between the markers; the whole
files are `example/src/example_app/di.py`, `example/src/example_app/api.py` (FastAPI) and
`example/src/example_app/main.py` (Typer).

```python
# di.py, inside register_and_init()
    # <features>
    register_auth(container)
    # </features>

# api.py / main.py (FastAPI), inside create_app()
    # <routers>
    app.include_router(auth_router)
    # </routers>

# main.py (Typer), module level
# <commands>
app.add_typer(auth_commands, name="auth")
# </commands>
```

---

## Tests — adapters

End-to-end adapter tests drive the wired app: `example/tests/features/notes/presentation/test_notes_router.py`
(`with TestClient(create_app())`, which runs the lifespan) and
`example/tests/features/notes/presentation/test_notes_commands.py` (`CliRunner` over the Typer `app`, whose
callback runs `register_and_init()`). Substituting fakes: `rules/testing/testing.md`.
