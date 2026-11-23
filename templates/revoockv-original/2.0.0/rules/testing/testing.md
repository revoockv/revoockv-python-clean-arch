# Testing (pytest + pytest-asyncio)

`tests/` mirrors `src/<package>/`:

```
tests/
  conftest.py                                   autouse fixture: container.reset() before/after each test
  features/<feature>/domain/use_cases/test_<action>_use_case.py
  features/<feature>/data/repositories/test_<name>_repository_impl.py
  features/<feature>/presentation/test_<feature>_router.py | test_<feature>_commands.py
```

`asyncio_mode = "auto"` is set in `pyproject.toml`, so `async def test_...` just works.
Tests are excluded from docstring/annotation ruff rules and from the architecture linter.

## What to test at each layer

| Layer | Subject | Replace with a fake |
|---|---|---|
| domain/use_cases | business rules, pass-through of `Result` | the domain repository ABC (hand-written fake) |
| data/repositories | exception → `Failure(<member>)`, model → entity mapping, logging | the data source ABC (fake or in-memory impl) |
| data/data_sources | real I/O against a local server/DB, or a stubbed transport (`httpx.MockTransport`) | the network |
| data/models | `from_dict` / `to_dict` / `to_entity` / `from_entity` round-trips | nothing |
| presentation | status codes / exit codes / output for Success and Failure | container registrations |

## Fakes over mocks

Implement the domain ABC in the test. The ABC forces the fake to stay in sync with the interface,
and mypy checks it.

```python
class FakeAuthRepository(AuthRepository):
    def __init__(self, sign_in_result: Result[AuthUser, AuthFailure]) -> None:
        self.sign_in_result = sign_in_result
        self.sign_in_calls: list[tuple[str, str]] = []

    async def sign_in(self, *, email: str, password: str) -> Result[AuthUser, AuthFailure]:
        self.sign_in_calls.append((email, password))
        return self.sign_in_result

    async def sign_out(self) -> Result[None, AuthFailure]:
        return Success(None)

    async def get_current_user(self) -> Result[AuthUser | None, AuthFailure]:
        return Success(None)


async def test_rejects_invalid_email_without_calling_repository() -> None:
    repository = FakeAuthRepository(Success(AuthUser(id="1", email="a@b.c")))

    result = await SignInUseCase(repository)(email="not-an-email", password="pw")

    assert result == Failure(AuthFailure.INVALID_EMAIL)
    assert repository.sign_in_calls == []
```

## Presentation tests with substituted dependencies

Getters resolve at call time, so register fakes in the container and drive the adapter:

```python
def test_sign_in_failure_returns_401() -> None:
    container.reset()
    register_core(container)
    container.register_singleton(SignInUseCase, SignInUseCase(FakeAuthRepository(Failure(AuthFailure.WRONG_CREDENTIALS))))
    app = FastAPI()
    app.include_router(router)               # no lifespan → register_and_init() is not called

    response = TestClient(app).post("/auth/sign-in", json={"email": "a@b.c", "password": "x"})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
```

For full end-to-end wiring use `with TestClient(create_app()) as client:` (runs the lifespan) or
`asyncio.run(register_and_init())` before invoking a Typer `CliRunner`.

Typer: mount the feature's `commands` under a parent `typer.Typer()` in tests — a Typer app with a
single command collapses it and ignores the command name.

## Commands

```bash
uv run pytest                     # all
uv run pytest tests/features/auth # one feature
uv run pytest -k sign_in -x       # by name, stop at first failure
```
