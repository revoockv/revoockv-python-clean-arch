# Constants — inside the owning class

Never declare constants at module level in domain or presentation code (`[lint.params] constant_layers`). A constant
belongs to the class that uses it, so a reader always sees where a value comes from and what it is for:

```python
class SignInUseCase:
    """Validates credentials and signs the user in."""

    _EMAIL_SEPARATOR = "@"
    _INVALID_EMAIL_ERROR = "Email is not valid"
```

- Private class attributes (`_NAME`) for values used only inside the class; public (`NAME`) for values another module
  needs.
- Mutable class constants must be `ClassVar[...]` (ruff `RUF012`).
- Module-level functions (DI, getters, CLI commands, routes) put their constants in a small constants class in the
  same module: `<Feature>Di` (`example/src/example_app/core/presentation/di/core_di.py`), `<Feature>CommandsText`
  (`example/src/example_app/features/notes/presentation/cli/notes_commands.py`).
- Text with values is a template constant filled with `.format(...)`; an f-string with words in it is a
  `magic_strings` violation.
- HTTP status codes: `http.HTTPStatus`, never numbers.

## What the linter checks (`magic_strings`, `magic_numbers`, `module_constants`)

They check function bodies and module-level assignments in the layers of `constant_layers` (domain and presentation).
Numbers in `allowed_numbers` (-1, 0, 1, 2) are free.

Exempt: docstrings, logger messages, annotations and `Literal[...]`, decorator arguments, module-level adapter
objects (`APIRouter(prefix=...)`, `typer.Typer(help=...)`), and the whole data layer (JSON keys, SQL, headers,
selectors) — data classes still keep repeated values as class constants (`_TABLE = "notes"`).
