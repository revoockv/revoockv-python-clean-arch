#!/usr/bin/env python3
"""
Create a new Python project following revoockv clean architecture.

Creates (src layout, uv-managed):

<project>/
  pyproject.toml            — uv + ruff + mypy --strict + pytest config
  README.md
  .gitignore
  src/<package>/
    __init__.py
    di.py                   — register_and_init(): core DI + every feature
    main.py                 — entry point (plain asyncio / FastAPI / Typer)
    core/
      data/{data_sources,models,repositories}/
      domain/{entities,repositories,use_cases}/
        entities/result.py  — Success / Failure / Result[T]
      presentation/di/
        container.py        — typed DI container (GetIt equivalent)
        core_di.py          — register_core(): Logger singleton
    features/
  tests/

The script only writes files. Afterwards run the `uv add` commands it prints.

Usage:
  python3 scripts/init_project.py --name my_app
  python3 scripts/init_project.py --name my_app --path ~/projects --adapter fastapi
  python3 scripts/init_project.py --name my_app --adapter typer
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ADAPTERS = ("none", "fastapi", "typer")


@dataclass(frozen=True)
class Args:
    name: str
    path: Path
    adapter: str
    force: bool


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="Project / package name (kebab or snake case).")
    parser.add_argument("--path", default=".", help="Parent directory for the project (default: cwd).")
    parser.add_argument("--adapter", choices=ADAPTERS, default="none", help="Presentation adapter for main.py.")
    parser.add_argument("--here", action="store_true", help="Create the project directly in --path (no subfolder).")
    parser.add_argument("--force", action="store_true", help="Allow writing into a non-empty directory.")
    ns = parser.parse_args()
    base = Path(ns.path).expanduser().resolve()
    root = base if ns.here else base / ns.name
    return Args(name=ns.name, path=root, adapter=ns.adapter, force=ns.force)


def _package_name(name: str) -> str:
    pkg = re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()
    if not pkg or pkg[0].isdigit():
        raise SystemExit(f"Cannot derive a valid package name from {name!r}.")
    return pkg


def _write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"  skip (exists): {path}")
        return
    path.write_text(contents, encoding="utf-8")


# ── Templates ───────────────────────────────────────────────────────

PYPROJECT = """\
[project]
name = "{dist}"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.12"
dependencies = []
{scripts}
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{pkg}"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
  "E", "W", "F", "I", "N", "B", "UP", "SIM", "RUF", "D", "TID", "ANN", "T20", "PT", "ASYNC", "G",
]
ignore = ["D100", "D104", "D105", "D107"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D", "ANN"]

[tool.mypy]
strict = true
python_version = "3.12"
mypy_path = "src"
packages = ["{pkg}"]
# The container is keyed by abstract interfaces (ABCs) on purpose.
disable_error_code = ["type-abstract"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
"""

GITIGNORE = """\
__pycache__/
*.py[cod]
.venv/
.mypy_cache/
.ruff_cache/
.pytest_cache/
dist/
build/
*.egg-info/
.env
"""

README = """\
# {name}

Python clean architecture project (revoockv style): `data` / `domain` / `presentation`
per feature, use cases, `Result[T]`, manual DI container.

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
```
"""

RESULT = '''\
"""Result type for expected success/failure outcomes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Success[T]:
    """Successful outcome carrying a value (use ``Success(None)`` for commands)."""

    value: T


@dataclass(frozen=True, slots=True)
class Failure:
    """Failed outcome carrying a human-readable error message."""

    error: str


type Result[T] = Success[T] | Failure
"""Return type of every repository method and use case that can fail in an expected way."""
'''

CONTAINER = '''\
"""Typed dependency injection container (GetIt equivalent)."""

from collections.abc import Callable
from typing import cast

type _Key = tuple[type[object], str | None]


class Container:
    """Service locator keyed by interface type and optional instance name.

    Use ``register_*`` only from ``presentation/di`` modules and ``di.py``; everything else
    receives dependencies through constructors or reads them via ``<feature>_getters.py``.
    """

    _NOT_REGISTERED = "{key} is not registered"
    _ALREADY_REGISTERED = "{key} is already registered"
    _NAMED_KEY = "{interface} (name={name!r})"

    def __init__(self) -> None:
        self._singletons: dict[_Key, object] = {}
        self._lazy: dict[_Key, Callable[[], object]] = {}
        self._factories: dict[_Key, Callable[[], object]] = {}

    def register_singleton[T](
        self, interface: type[T], instance: T, *, name: str | None = None
    ) -> None:
        """Register an eagerly created instance shared by every ``get`` call."""
        key = self._new_key(interface, name)
        self._singletons[key] = instance

    def register_lazy_singleton[T](
        self, interface: type[T], factory: Callable[[], T], *, name: str | None = None
    ) -> None:
        """Register a factory that runs once, on the first ``get`` call."""
        key = self._new_key(interface, name)
        self._lazy[key] = factory

    def register_factory[T](
        self, interface: type[T], factory: Callable[[], T], *, name: str | None = None
    ) -> None:
        """Register a factory that creates a new instance on every ``get`` call."""
        key = self._new_key(interface, name)
        self._factories[key] = factory

    def get[T](self, interface: type[T], *, name: str | None = None) -> T:
        """Return the registered instance for ``interface`` (and ``name``).

        Raises:
            LookupError: If nothing is registered under that key.
        """
        key: _Key = (interface, name)
        if key in self._singletons:
            return cast(T, self._singletons[key])
        if key in self._lazy:
            instance = self._lazy.pop(key)()
            self._singletons[key] = instance
            return cast(T, instance)
        if key in self._factories:
            return cast(T, self._factories[key]())
        raise LookupError(self._NOT_REGISTERED.format(key=self._describe(key)))

    def is_registered(self, interface: type[object], *, name: str | None = None) -> bool:
        """Return True when ``interface`` (and ``name``) has a registration."""
        key: _Key = (interface, name)
        return key in self._singletons or key in self._lazy or key in self._factories

    def reset(self) -> None:
        """Drop every registration (used by ``register_and_init`` and tests)."""
        self._singletons.clear()
        self._lazy.clear()
        self._factories.clear()

    def _new_key(self, interface: type[object], name: str | None) -> _Key:
        if self.is_registered(interface, name=name):
            raise ValueError(self._ALREADY_REGISTERED.format(key=self._describe((interface, name))))
        return (interface, name)

    @classmethod
    def _describe(cls, key: _Key) -> str:
        interface, name = key
        if name is None:
            return interface.__qualname__
        return cls._NAMED_KEY.format(interface=interface.__qualname__, name=name)


container = Container()
"""The application container. Import it only in ``presentation/di`` modules and ``di.py``."""
'''

CORE_DI = '''\
"""Core DI: dependencies shared by every feature."""

import logging

from {pkg}.core.presentation.di.container import Container


class CoreDi:
    """Configuration values used by ``register_core``."""

    LOGGER_NAME = "{pkg}"
    LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def register_core(container: Container) -> None:
    """Register core singletons (the application ``logging.Logger``).

    Must run first in ``register_and_init`` because every repository receives the logger.
    """
    logging.basicConfig(level=logging.INFO, format=CoreDi.LOG_FORMAT)
    container.register_singleton(logging.Logger, logging.getLogger(CoreDi.LOGGER_NAME))
'''

DI = '''\
"""Main DI: registers core and every feature, then runs one-time initiations."""

from {pkg}.core.presentation.di.container import container
from {pkg}.core.presentation.di.core_di import register_core


async def register_and_init() -> None:
    """Reset the container, register all dependencies and run feature initiations.

    The single DI entry point; ``main.py`` calls nothing else.
    """
    container.reset()
    register_core(container)
    # <features>
    # </features>
'''

MAIN_NONE = '''\
"""Application entry point."""

import asyncio

from {pkg}.di import register_and_init


async def main() -> None:
    """Register dependencies, run initiations and start the application."""
    await register_and_init()


if __name__ == "__main__":
    asyncio.run(main())
'''

MAIN_FASTAPI = '''\
"""Application entry point (FastAPI). Run: uv run uvicorn {pkg}.main:app --reload."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from {pkg}.di import register_and_init


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Register dependencies and run initiations before serving requests."""
    await register_and_init()
    yield


def create_app() -> FastAPI:
    """Build the FastAPI application and include every feature router."""
    app = FastAPI(lifespan=lifespan)
    # <routers>
    # </routers>
    return app


app = create_app()
'''

MAIN_TYPER = '''\
"""Application entry point (Typer CLI). Run: uv run {dist}."""

import asyncio

import typer

from {pkg}.di import register_and_init

app = typer.Typer(no_args_is_help=True)
# <commands>
# </commands>


@app.callback()
def bootstrap() -> None:
    """Register dependencies and run initiations before any command."""
    asyncio.run(register_and_init())


if __name__ == "__main__":
    app()
'''

CONFTEST = '''\
from collections.abc import Iterator

import pytest

from {pkg}.core.presentation.di.container import container


@pytest.fixture(autouse=True)
def _reset_container() -> Iterator[None]:
    container.reset()
    yield
    container.reset()
'''

TEST_RESULT = '''\
from {pkg}.core.domain.entities.result import Failure, Result, Success


def _describe(result: Result[int]) -> str:
    match result:
        case Success(value):
            return f"ok {{value}}"
        case Failure(error):
            return f"error {{error}}"


def test_result_pattern_matching() -> None:
    assert _describe(Success(1)) == "ok 1"
    assert _describe(Failure("boom")) == "error boom"
'''

ADAPTER_DEPS = {
    "none": ("", ""),
    "fastapi": ("fastapi uvicorn", "httpx2"),
    "typer": ("typer", ""),
}


def main() -> None:
    args = _parse_args()
    root = args.path
    pkg = _package_name(args.name)
    dist = pkg.replace("_", "-")

    if root.exists() and any(p for p in root.iterdir() if p.name != ".git") and not args.force:
        raise SystemExit(f"{root} is not empty. Use --force to write into it (existing files are kept).")

    src = root / "src" / pkg
    fmt = {"pkg": pkg, "dist": dist, "name": args.name}
    scripts = f'\n[project.scripts]\n{dist} = "{pkg}.main:app"\n' if args.adapter == "typer" else ""

    _write(root / "pyproject.toml", PYPROJECT.format(scripts=scripts, **fmt))
    _write(root / ".gitignore", GITIGNORE)
    _write(root / "README.md", README.format(**fmt))

    # Package + core mirror of the feature layout.
    _write(src / "__init__.py", "")
    _write(src / "py.typed", "")
    for rel in (
        "core",
        "core/data",
        "core/data/data_sources",
        "core/data/models",
        "core/data/repositories",
        "core/domain",
        "core/domain/entities",
        "core/domain/repositories",
        "core/domain/use_cases",
        "core/presentation",
        "core/presentation/di",
        "features",
    ):
        _write(src / rel / "__init__.py", "")

    _write(src / "core/domain/entities/result.py", RESULT)
    _write(src / "core/presentation/di/container.py", CONTAINER)
    _write(src / "core/presentation/di/core_di.py", CORE_DI.format(**fmt))
    _write(src / "di.py", DI.format(**fmt))
    main_tpl = {"none": MAIN_NONE, "fastapi": MAIN_FASTAPI, "typer": MAIN_TYPER}[args.adapter]
    _write(src / "main.py", main_tpl.format(**fmt))

    # Tests mirror src.
    _write(root / "tests/__init__.py", "")
    _write(root / "tests/conftest.py", CONFTEST.format(**fmt))
    _write(root / "tests/core/__init__.py", "")
    _write(root / "tests/core/domain/__init__.py", "")
    _write(root / "tests/core/domain/entities/__init__.py", "")
    _write(root / "tests/core/domain/entities/test_result.py", TEST_RESULT.format(**fmt))
    _write(root / "tests/features/__init__.py", "")

    deps, dev_extra = ADAPTER_DEPS[args.adapter]
    print(f"Initialized project '{pkg}' at: {root}")
    print("Next steps:")
    print(f"  cd {root}")
    if deps:
        print(f"  uv add {deps}")
    print(f"  uv add --dev ruff mypy pytest pytest-asyncio {dev_extra}".rstrip())
    print("  uv run pytest && uv run mypy && uv run ruff check .")


if __name__ == "__main__":
    main()
