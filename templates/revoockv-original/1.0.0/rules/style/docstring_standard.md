# Docstring standard (required)

Google-style docstrings (ruff `D` rules with `convention = "google"`), checked by ruff and by the
`docstring_public` linter rule.

Required for:

- every public class;
- every public function and method;
- every use case `__call__`;
- DI functions (`register_<feature>`, `init_<feature>`, `register_and_init`, `register_core`);
- getters;
- any non-trivial private helper.

Not required: module docstrings (`D100`), package `__init__.py` (`D104`), magic methods other than
`__call__` (`D105`), `__init__` (`D107`) — document constructor parameters in the class docstring
when they are not obvious. Tests are exempt.

Keep them short:

- one-line summary in the imperative or descriptive mood;
- one sentence on when to use it, if not obvious;
- `Args:` / `Returns:` / `Raises:` only when they add information beyond the type hints;
- mention side effects (I/O, network, subscriptions, container registrations).

```python
async def init_song(container: Container) -> None:
    """Open the songs database pool.

    Called once from ``register_and_init``. Side effect: opens network connections.
    """
```

```python
class AuthDataSource(ABC):
    """Talks to the auth backend. May raise; the repository converts errors to ``Failure``."""

    @abstractmethod
    async def sign_in(self, *, email: str, password: str) -> AuthUserModel:
        """Authenticate and return the user.

        Raises:
            AuthDataSourceError: If the credentials are rejected.
        """
```
