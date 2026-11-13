#!/usr/bin/env python3
"""
Create a feature skeleton following revoockv Python clean architecture.

Creates (inside src/<package>/features/<feature>/):

  data/
    data_sources/
    models/
    repositories/
  domain/
    entities/
    repositories/
    use_cases/
  presentation/
    di/
      <feature>_di.py       — register_<feature>(container)
      <feature>_getters.py  — top-level getters for use cases
    api/<feature>_router.py      (with --adapter fastapi)
    cli/<feature>_commands.py    (with --adapter typer)

and wires the feature into the project:
  - di.py       → import + register_<feature>(container) inside the # <features> block
  - main.py     → router / command group (when an adapter is given)
  - tests/features/<feature>/... mirror packages

Existing files are never overwritten. Run `uv run ruff check --fix . && uv run ruff format .`
afterwards to sort the inserted imports.

Usage:
  python3 scripts/init_feature.py --feature auth
  python3 scripts/init_feature.py --feature auth --adapter fastapi
  python3 scripts/init_feature.py --feature auth --subfeature session
  python3 scripts/init_feature.py --feature auth --package-dir src/my_app
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path

ADAPTERS = ("none", "fastapi", "typer")
SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class Args:
    feature: str
    subfeature: str | None
    package_dir: Path
    adapter: str


def _detect_package_dir() -> Path:
    src = Path("src")
    candidates = [p for p in src.glob("*") if (p / "di.py").is_file()] if src.is_dir() else []
    if len(candidates) == 1:
        return candidates[0]
    raise SystemExit("Cannot detect the package. Run from the project root or pass --package-dir src/<package>.")


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feature", required=True, help="Feature name in snake_case (e.g. auth, song_library).")
    parser.add_argument("--subfeature", default=None, help="Optional subfeature DI module (snake_case).")
    parser.add_argument("--package-dir", default=None, help="Path to src/<package> (auto-detected by default).")
    parser.add_argument("--adapter", choices=ADAPTERS, default="none", help="Create a router / command stub.")
    ns = parser.parse_args()
    for value in (ns.feature, ns.subfeature):
        if value is not None and not SNAKE.match(value):
            raise SystemExit(f"{value!r} must be snake_case.")
    package_dir = Path(ns.package_dir) if ns.package_dir else _detect_package_dir()
    return Args(feature=ns.feature, subfeature=ns.subfeature, package_dir=package_dir, adapter=ns.adapter)


def _title(name: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in name.split("_"))


def _write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(contents, encoding="utf-8")


def _insert_import(path: Path, import_line: str) -> str:
    """Insert ``import_line`` after the last top-level import of ``path``'s source."""
    source = path.read_text(encoding="utf-8")
    if import_line in source:
        return source
    tree = ast.parse(source)
    last = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last = node.end_lineno or node.lineno
    lines = source.splitlines(keepends=True)
    lines.insert(last, import_line + "\n")
    return "".join(lines)


def _insert_in_block(source: str, marker: str, line: str) -> str:
    """Insert ``line`` right before ``# </marker>``, keeping the marker's indentation."""
    if line.strip() in source:
        return source
    match = re.search(rf"^([ \t]*)# </{marker}>", source, flags=re.MULTILINE)
    if match is None:
        print(f"  warning: '# </{marker}>' marker not found — add `{line.strip()}` manually.")
        return source
    indent = match.group(1)
    return source[: match.start()] + f"{indent}{line.strip()}\n" + source[match.start() :]


def _wire(path: Path, import_line: str, marker: str, call_line: str) -> None:
    if not path.is_file():
        print(f"  warning: {path} not found — wire the feature manually.")
        return
    source = _insert_import(path, import_line)
    source = _insert_in_block(source, marker, call_line)
    path.write_text(source, encoding="utf-8")


def main() -> None:
    args = _parse_args()
    pkg_dir = args.package_dir
    pkg = pkg_dir.name
    feature = args.feature
    title = _title(feature)
    root = pkg_dir / "features" / feature
    module = f"{pkg}.features.{feature}"

    for rel in (
        "",
        "data",
        "data/data_sources",
        "data/models",
        "data/repositories",
        "domain",
        "domain/entities",
        "domain/repositories",
        "domain/use_cases",
        "presentation",
        "presentation/di",
    ):
        _write(root / rel / "__init__.py", "")

    _write(
        root / "presentation/di" / f"{feature}_di.py",
        f'''"""DI registration for the {feature} feature."""

from {pkg}.core.presentation.di.container import Container


def register_{feature}(container: Container) -> None:
    """Register data sources, repositories and use cases of the {feature} feature.

    Order: data sources → repositories (by domain interface) → use cases.
    """
''',
    )
    _write(
        root / "presentation/di" / f"{feature}_getters.py",
        f'''"""Getters through which the {feature} presentation layer reaches its use cases.

Presentation code imports these functions instead of touching the container or the domain
use case modules directly.
"""
''',
    )

    if args.subfeature:
        sub = args.subfeature
        _write(
            root / "presentation/di" / f"{sub}_di.py",
            f'''"""DI registration for the {feature}.{sub} subfeature."""

from {pkg}.core.presentation.di.container import Container


def register_{feature}_{sub}(container: Container) -> None:
    """Register dependencies of the {feature}.{sub} subfeature.

    Called from ``register_{feature}``; prefer feature-level DI unless asked otherwise.
    """
''',
        )

    if args.adapter == "fastapi":
        _write(root / "presentation/api/__init__.py", "")
        _write(root / "presentation/api/schemas/__init__.py", "")
        _write(
            root / "presentation/api" / f"{feature}_router.py",
            f'''"""HTTP routes of the {feature} feature."""

from fastapi import APIRouter

router = APIRouter(prefix="/{feature.replace("_", "-")}", tags=["{feature}"])
''',
        )
    elif args.adapter == "typer":
        _write(root / "presentation/cli/__init__.py", "")
        _write(
            root / "presentation/cli" / f"{feature}_commands.py",
            f'''"""CLI commands of the {feature} feature."""

import typer

commands = typer.Typer(help="{title} commands.", no_args_is_help=True)
''',
        )

    # Tests mirror the feature layout.
    tests_root = pkg_dir.parent.parent / "tests" / "features" / feature
    for rel in ("", "data", "data/repositories", "domain", "domain/use_cases", "presentation"):
        _write(tests_root / rel / "__init__.py", "")

    _wire(
        pkg_dir / "di.py",
        f"from {module}.presentation.di.{feature}_di import register_{feature}",
        "features",
        f"register_{feature}(container)",
    )
    if args.adapter == "fastapi":
        _wire(
            pkg_dir / "main.py",
            f"from {module}.presentation.api.{feature}_router import router as {feature}_router",
            "routers",
            f"app.include_router({feature}_router)",
        )
    elif args.adapter == "typer":
        _wire(
            pkg_dir / "main.py",
            f"from {module}.presentation.cli.{feature}_commands import commands as {feature}_commands",
            "commands",
            f'app.add_typer({feature}_commands, name="{feature.replace("_", "-")}")',
        )

    print(f"Initialized feature skeleton at: {root}")
    print("Next: implement domain → data → presentation/di → adapter, then run:")
    print("  uv run ruff check --fix . && uv run ruff format . && uv run mypy && uv run pytest")


if __name__ == "__main__":
    main()
