#!/usr/bin/env python3
"""
Compare the package versions pinned by a template with the latest ones on PyPI.

The pinned versions are the `"name>=X.Y.Z"` lower bounds of the template's example/pyproject.toml
(`[project] dependencies` and `[dependency-groups]`); a template's `[packages] tracked` limits the check
to those names. `--update` raises the outdated bounds there and in every rule file that shows them,
then `uv lock` and `scripts/selfcheck.py` verify the example with the new versions.

Usage:
  python3 scripts/check_versions.py                                  # report; exit 0
  python3 scripts/check_versions.py --strict                         # exit 1 when something is outdated
  python3 scripts/check_versions.py --update                         # raise the bounds to the latest versions
  python3 scripts/check_versions.py --template revoockv-original@1.0.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
import templates  # noqa: E402

PYPI_API = "https://pypi.org/pypi/{name}/json"
# A quoted requirement with a lower bound: "fastapi>=0.162.5"
PINNED = re.compile(r'"([A-Za-z0-9][A-Za-z0-9._-]*)>=(\d+(?:\.\d+)*)"')
CONSTRAINT = r'("{name}>=)(\d+(?:\.\d+)*)(")'


def pinned_versions(pyproject: Path, tracked: tuple[str, ...]) -> dict[str, str]:
    """Return {package: lower bound} of the pyproject, only [tracked] when given."""
    found = dict(PINNED.findall(pyproject.read_text(encoding="utf-8")))
    return {name: found[name] for name in tracked if name in found} if tracked else found


def latest_version(name: str) -> str | None:
    """Return the latest release on PyPI, or None when offline."""
    try:
        with urllib.request.urlopen(PYPI_API.format(name=name), timeout=15) as resp:
            return str(json.load(resp)["info"]["version"])
    except Exception as e:  # network errors must not break offline work
        print(f"  ! {name}: cannot reach PyPI ({e})", file=sys.stderr)
        return None


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", version)[:3])


def update(files: list[Path], outdated: dict[str, str]) -> list[Path]:
    """Rewrite `"name>=old"` to `"name>=new"` in [files]; return the changed ones."""
    changed: list[Path] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        new = text
        for name, version in outdated.items():
            new = re.sub(CONSTRAINT.format(name=re.escape(name)), rf"\g<1>{version}\g<3>", new)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="exit 1 when a package is outdated")
    parser.add_argument("--update", action="store_true", help="raise outdated bounds in the pyproject and rules")
    parser.add_argument("--template", help="template (name@version) to check; default: the skill's default")
    args = parser.parse_args()

    template = templates.resolve(args.template)
    pyproject = template.example_dir / "pyproject.toml"
    tracked = tuple(template.data.get("packages", {}).get("tracked", ()))
    print(f"Template {template.ref}")

    pinned = pinned_versions(pyproject, tracked)
    for name in tracked:
        if name not in pinned:
            print(f"  ? {name}: not pinned in {pyproject.relative_to(SKILL_ROOT)}")
    outdated: dict[str, str] = {}
    print("Package versions (pinned → latest on PyPI):")
    for name, current in sorted(pinned.items()):
        latest = latest_version(name)
        if latest is None:
            continue
        if _key(latest) > _key(current):
            outdated[name] = latest
            print(f"  ↑ {name}: >={current} → {latest} available")
        else:
            print(f"  ✓ {name}: >={current}")

    if outdated and args.update:
        for path in update([pyproject, *template.doc_files()], outdated):
            print(f"  updated {path.relative_to(SKILL_ROOT)}")
        print(f"Next: (cd {template.example_dir.relative_to(SKILL_ROOT)} && uv lock), then scripts/selfcheck.py")
        return 0

    return 1 if (outdated and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
