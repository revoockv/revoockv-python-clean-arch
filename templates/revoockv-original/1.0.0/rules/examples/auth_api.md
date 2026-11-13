# Auth feature — FastAPI adapter

Part 4 of 4: the HTTP adapter of the worked feature (`auth_presentation.md` has its DI, getters and Typer commands).

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
