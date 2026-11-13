# Imports (required)

## Absolute imports only

```python
from my_app.features.auth.domain.entities.auth_user import AuthUser      # yes
from ..entities.auth_user import AuthUser                                # no (relative_import, ruff TID252)
```

Import the symbol from its defining module. Do not re-export from `__init__.py` files; keep them empty.

## Layer dependency matrix (`import_violation`)

| From \ To | stdlib | third-party | core.domain | own domain | other feature domain | own data | other feature data | presentation | container | di.py / main.py |
|---|---|---|---|---|---|---|---|---|---|---|
| domain | yes | **no** | yes | yes | yes | no | no | no | no | no |
| data | yes | yes | yes | yes | yes | yes | no | no | no | no |
| presentation (adapters) | yes | yes | yes | entities only | entities only | no | no | own feature only | no | no |
| presentation/di | yes | yes | yes | yes | yes | yes | no | own feature only | yes | no |
| core | yes | yes* | yes | — | no | — | no | core only | core/presentation/di | no |
| di.py, main.py | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |

\* `core/domain` follows the domain row: stdlib only.

Key consequences:

- Domain is framework-free: no `pydantic`, `fastapi`, `sqlalchemy`, `httpx` in `domain/`.
- Presentation adapters reach use cases only through `<feature>_getters.py`; they may import
  domain **entities** for typing and mapping, and `core.domain.entities.result`.
- Features talk to each other only through domain interfaces/entities. Need another feature's
  repository? Get it from the container by its domain interface inside your `<feature>_di.py`.
- `core` never imports from `features`.

## Common imports

```python
from my_app.core.domain.entities.result import Failure, Result, Success
from my_app.core.presentation.di.container import Container, container  # di modules only
```

`if TYPE_CHECKING:` imports are checked by the same rules.
