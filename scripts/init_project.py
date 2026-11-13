#!/usr/bin/env python3
"""
Create a new Python project by the chosen clean-architecture template.

Everything comes from the template (`templates/<name>/<version>/`):
  scaffold/project/**.tmpl          pyproject.toml, README, .gitignore, di.py, core DI, tests
  scaffold/main/<adapter>.py.tmpl   src/<package>/main.py for the adapter
  [scaffold] core_files             copied from the template's example (Result, Container, …)
  [structure]                       the folders of src/<package>/core/
and the project gets `.clean_arch.toml` with the template's ref.

The script only writes files; afterwards run the `uv add` commands it prints.

Usage:
  python3 scripts/init_project.py --name my-app [--path ~/projects] [--adapter none|fastapi|typer]
  python3 scripts/init_project.py --name my-app --template revoockv-original@1.0.0
  python3 scripts/init_project.py --name my-app --path . --here --force    # into an existing repo
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
import scaffold  # noqa: E402
import templates  # noqa: E402


def _package_name(name: str) -> str:
    package = re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()
    if not package or package[0].isdigit():
        raise SystemExit(f"Cannot derive a valid package name from {name!r}.")
    return package


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="Project / package name (kebab or snake case).")
    parser.add_argument("--path", default=".", help="Parent directory for the project (default: cwd).")
    parser.add_argument("--adapter", default="none", help="Presentation adapter of main.py (the template's [scaffold.adapters]).")
    parser.add_argument("--template", help="Template (name@version); default: the skill's default.")
    parser.add_argument("--here", action="store_true", help="Create the project directly in --path (no subfolder).")
    parser.add_argument("--force", action="store_true", help="Allow writing into a non-empty directory (existing files are kept).")
    args = parser.parse_args()

    try:
        template = templates.resolve(args.template)
    except templates.TemplateError as e:
        raise SystemExit(str(e)) from e
    adapters: dict[str, dict[str, object]] = template.data["scaffold"].get("adapters", {"none": {}})
    if args.adapter not in adapters:
        raise SystemExit(f"--adapter must be one of: {', '.join(adapters)}")
    base = Path(args.path).expanduser().resolve()
    root = base if args.here else base / args.name
    if root.exists() and any(p for p in root.iterdir() if p.name != ".git") and not args.force:
        raise SystemExit(f"{root} is not empty. Use --force to write into it (existing files are kept).")

    package = _package_name(args.name)
    dist = package.replace("_", "-")
    values = {"package": package, "dist": dist, "name": args.name, "template": template.ref}
    adapter = adapters[args.adapter]
    script = str(adapter.get("script", ""))
    values["scripts"] = f'[project.scripts]\n{dist} = "{scaffold.fill(script, values)}"\n\n' if script else ""
    print(f"Template {template.ref}")

    scaffold.copy_stubs(template.folder / "scaffold" / "project", root, values)
    src = root / "src" / package
    scaffold.make_packages(src / "core", template.layout)
    scaffold.make_packages(src / "features", {})
    main_stub = template.folder / "scaffold" / "main" / f"{args.adapter}.py.tmpl"
    if main_stub.is_file():
        scaffold.write_if_missing(src / "main.py", scaffold.fill(main_stub.read_text(encoding="utf-8"), values))
    example_src = template.example_dir / "src" / template.example_package
    for rel in template.core_files:
        code = (example_src / rel).read_text(encoding="utf-8").replace(f"{template.example_package}.", f"{package}.")
        scaffold.write_if_missing(src / rel, code)
    scaffold.write_if_missing(
        root / templates.PROJECT_FILE,
        f'# Architecture template of this project (revoockv-python-clean-arch).\ntemplate = "{template.ref}"\n',
    )

    deps = " ".join(map(str, adapter.get("dependencies", [])))
    dev = " ".join([*template.data["scaffold"].get("dev_dependencies", {}).get("packages", []), *map(str, adapter.get("dev", []))])
    print(f"\nInitialized project '{package}' at: {root}\nNext steps:\n  cd {root}")
    if deps:
        print(f"  uv add {deps}")
    print(f"  uv add --dev {dev}")
    print("  uv run ruff check --fix . && uv run ruff format . && uv run mypy && uv run pytest")


if __name__ == "__main__":
    main()
