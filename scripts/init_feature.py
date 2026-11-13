#!/usr/bin/env python3
"""
Create a feature skeleton by the project's clean-architecture template and wire it in.

From the template (`.clean_arch.toml` of the project, else the default, or `--template`):
  [structure]                         the folders of src/<package>/features/<feature>/ (all packages)
  scaffold/feature/**.tmpl            DI stubs: <feature>_di.py, <feature>_getters.py
  scaffold/subfeature/**.tmpl         with --subfeature
  scaffold/adapters/<adapter>/**.tmpl with --adapter (router / command group)
  scaffold/feature_tests/**.tmpl      under tests/features/<feature>/
  [scaffold.wiring]                   the lines added to di.py and main.py

Existing files are never overwritten, so it is safe to run again (e.g. to add an adapter later).
Afterwards run `uv run ruff check --fix . && uv run ruff format .` to sort the inserted imports.

Usage:
  python3 scripts/init_feature.py --feature auth
  python3 scripts/init_feature.py --feature auth --adapter fastapi
  python3 scripts/init_feature.py --feature auth --subfeature session
  python3 scripts/init_feature.py --feature auth --package-dir src/my_app
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

SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


def _detect_package_dir() -> Path:
    src = Path("src")
    candidates = [p for p in src.glob("*") if (p / "di.py").is_file()] if src.is_dir() else []
    if len(candidates) == 1:
        return candidates[0]
    raise SystemExit("Cannot detect the package. Run from the project root or pass --package-dir src/<package>.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feature", required=True, help="Feature name in snake_case (e.g. auth, song_library).")
    parser.add_argument("--subfeature", default=None, help="Optional subfeature DI module (snake_case).")
    parser.add_argument("--package-dir", default=None, help="Path to src/<package> (auto-detected by default).")
    parser.add_argument("--adapter", default="none", help="Adapter stub to add (the template's [scaffold.adapters]).")
    parser.add_argument("--template", help="Template (name@version); default: the project's .clean_arch.toml, else the skill's default.")
    args = parser.parse_args()
    for flag, value in (("--feature", args.feature), ("--subfeature", args.subfeature)):
        if value is not None and not SNAKE.match(value):
            raise SystemExit(f"{flag} {value!r} must be snake_case (a-z, 0-9, _).")

    package_dir = (Path(args.package_dir) if args.package_dir else _detect_package_dir()).resolve()
    project_root = package_dir.parent.parent
    try:
        template = templates.resolve(args.template, project_root)
    except templates.TemplateError as e:
        raise SystemExit(str(e)) from e
    data = template.data["scaffold"]
    if args.adapter not in data.get("adapters", {"none": {}}):
        raise SystemExit(f"--adapter must be one of: {', '.join(data.get('adapters', {}))}")
    print(f"Template {template.ref}")

    feature = args.feature
    values = {
        "package": package_dir.name,
        "feature": feature,
        "Feature": scaffold.title(feature),
        "feature_slug": feature.replace("_", "-"),
    }
    stubs = template.folder / "scaffold"
    root = package_dir / "features" / feature
    scaffold.make_packages(root, template.layout)
    scaffold.copy_stubs(stubs / "feature", root, values)
    if args.subfeature:
        sub_values = {**values, "subfeature": args.subfeature, "Subfeature": scaffold.title(args.subfeature)}
        scaffold.copy_stubs(stubs / "subfeature", root, sub_values)
    if args.adapter != "none":
        scaffold.copy_stubs(stubs / "adapters" / args.adapter, root, values)
    scaffold.copy_stubs(stubs / "feature_tests", project_root / "tests" / "features" / feature, values)

    wiring: dict[str, dict[str, str]] = data.get("wiring", {})
    for key in ("feature", args.adapter):
        rule = wiring.get(key)
        if rule:
            scaffold.wire(
                package_dir / rule["file"],
                import_line=scaffold.fill(rule["import"], values),
                marker=rule["marker"],
                line=scaffold.fill(rule["line"], values),
            )

    print(f"\nInitialized feature at: {root}")
    if data.get("next_step"):
        print(f"Next: {scaffold.fill(str(data['next_step']), values)}")
    print("  uv run ruff check --fix . && uv run ruff format . && uv run mypy && uv run pytest")


if __name__ == "__main__":
    main()
