"""Shared helpers of init_project.py and init_feature.py: fill and write the template's stub files."""

from __future__ import annotations

import ast
import re
from pathlib import Path

TEMPLATE_SUFFIX = ".tmpl"


def title(name: str) -> str:
    """snake_case → TitleCase (``song_library`` → ``SongLibrary``)."""
    return "".join(part[:1].upper() + part[1:] for part in name.split("_"))


def fill(text: str, values: dict[str, str]) -> str:
    """Replace every ``{{key}}`` of [values] in [text]."""
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def write_if_missing(path: Path, contents: str) -> None:
    """Write [path] unless it exists (existing files are always kept)."""
    if path.exists():
        print(f"  kept     {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    print(f"  created  {path}")


def copy_stubs(source: Path, target: Path, values: dict[str, str]) -> None:
    """Write every ``*.tmpl`` below [source] under [target], names and text filled with [values]."""
    if not source.is_dir():
        return
    for stub in sorted(source.rglob("*" + TEMPLATE_SUFFIX)):
        relative = fill(str(stub.relative_to(source))[: -len(TEMPLATE_SUFFIX)], values)
        write_if_missing(target / relative, fill(stub.read_text(encoding="utf-8"), values))


def make_packages(root: Path, layout: dict[str, tuple[str, ...]]) -> None:
    """Create ``root/<layer>/<sub>/`` for [layout], every folder a package (``__init__.py``)."""
    folders = [root] + [root / layer for layer in layout] + [root / layer / sub for layer, subs in layout.items() for sub in subs]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        init = folder / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")


def _insert_import(source: str, import_line: str) -> str:
    if import_line in source:
        return source
    last = 0
    for node in ast.parse(source).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last = node.end_lineno or node.lineno
    lines = source.splitlines(keepends=True)
    lines.insert(last, import_line + "\n")
    return "".join(lines)


def _insert_in_block(source: str, marker: str, line: str) -> str:
    if line.strip() in source:
        return source
    match = re.search(rf"^([ \t]*)# </{marker}>", source, flags=re.MULTILINE)
    if match is None:
        print(f"  warning: '# </{marker}>' marker not found — add `{line.strip()}` by hand.")
        return source
    return source[: match.start()] + f"{match.group(1)}{line.strip()}\n" + source[match.start() :]


def wire(path: Path, *, import_line: str, marker: str, line: str) -> None:
    """Add [import_line] after the last import of [path] and [line] before its ``# </marker>``."""
    if not path.is_file():
        print(f"  warning: {path} not found — wire it by hand: {line}")
        return
    source = _insert_in_block(_insert_import(path.read_text(encoding="utf-8"), import_line), marker, line)
    path.write_text(source, encoding="utf-8")
    print(f"  wired    {path}: {line.strip()}")
