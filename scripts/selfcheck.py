#!/usr/bin/env python3
"""
Self-check of the skill: for every template, its rules, scaffold, linter and example must agree.

Steps:
  1. linter unit tests            python3 -m unittest discover -s tests
  For each template version (or --template):
  2. template                     templates.py validate (files, keys, sizes, lint rules and params)
  3. code in the rules vs example every ```python block labelled with a path under `[example] same_as_example`
                                  must equal the example's file; every `example/…` path in the rules exists
  4. example                      copy of example/ → uv sync, ruff check, ruff format --check, mypy, pytest,
                                  linter --strict
  5. feature from the rules       every ```python block under `[example] doc_paths` is written into the copy
                                  and must pass ruff, mypy and the linter (di_naming off: it is not wired)
  6. scaffold                     init_project + init_feature for every adapter → ruff, mypy, pytest, linter

Usage:
  python3 scripts/selfcheck.py                                   # every template
  python3 scripts/selfcheck.py --template revoockv-original@1.0.0
  python3 scripts/selfcheck.py --no-uv                           # without the steps that need uv
  python3 scripts/selfcheck.py --keep                            # keep the temp projects
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
LINTER = SCRIPTS / "py_clean_arch_linter.py"
sys.path.insert(0, str(SCRIPTS))
import templates  # noqa: E402

# A file block: a line `src/....py` (or tests/…), a blank line, then ```python
DOC_FILE_BLOCK = re.compile(r"^`((?:src|tests)/[^`]+\.py)`[^\n]*\n\n```python\n(.*?)```", re.M | re.S)
# A path of the example named in the rules: `example/…`
EXAMPLE_LINK = re.compile(r"`example/([^`\s]+)`")
GATE = (
    ["uv", "run", "ruff", "check", "."],
    ["uv", "run", "ruff", "format", "--check", "."],
    ["uv", "run", "mypy"],
)

_failures: list[str] = []


def step(title: str) -> None:
    print(f"\n── {title}")


def check(ok: bool, label: str, details: str = "") -> bool:
    print(f"  {'✓' if ok else '✗'} {label}")
    if not ok:
        _failures.append(label)
        if details:
            print("    " + details.strip().replace("\n", "\n    ")[-3000:])
    return ok


def run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    env = {**os.environ, "VIRTUAL_ENV": ""}
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    return proc.returncode == 0, proc.stdout + proc.stderr


def doc_blocks(template: templates.Template) -> dict[str, str]:
    """{path: code} of the rules' file blocks under `[example] doc_paths`, renamed to the example package."""
    example = template.data["example"]
    docs_package = example.get("docs_package", "my_app")
    prefixes = tuple(example.get("doc_paths", ()))
    blocks: dict[str, str] = {}
    for doc in template.doc_files():
        for path, code in DOC_FILE_BLOCK.findall(doc.read_text(encoding="utf-8")):
            if not path.startswith(prefixes):
                continue
            path = path.replace(f"src/{docs_package}/", f"src/{template.example_package}/")
            code = re.sub(rf"\b{docs_package}\.", f"{template.example_package}.", code)
            if path in blocks and blocks[path] != code:
                check(False, f"{path} is defined twice in the rules with different code ({doc.name})")
            blocks[path] = code
    return blocks


def compare_with_example(template: templates.Template, blocks: dict[str, str]) -> None:
    docs_package = template.data["example"].get("docs_package", "my_app")
    prefixes = tuple(
        p.replace(f"src/{docs_package}/", f"src/{template.example_package}/")
        for p in template.data["example"].get("same_as_example", ())
    )
    for path, code in sorted(blocks.items()):
        if not path.startswith(prefixes):
            continue
        example_file = template.example_dir / path
        same = example_file.is_file() and example_file.read_text(encoding="utf-8") == code
        check(same, f"rules {path} == example", "" if same else "the rules and example/ differ — update one of them")


def quality_gate(project: Path, label: str, *, lint_args: tuple[str, ...] = ()) -> None:
    ok, out = run(["uv", "sync", "--quiet"], project)
    if not check(ok, f"{label}: uv sync", out):
        return
    for cmd in GATE:
        ok, out = run(cmd, project)
        check(ok, f"{label}: {' '.join(cmd[2:])}", out)
    if (project / "tests").is_dir():
        ok, out = run(["uv", "run", "pytest", "-q"], project)
        check(ok, f"{label}: pytest", out)
    ok, out = run([sys.executable, str(LINTER), *lint_args, "--strict"], project)
    check(ok, f"{label}: linter --strict {' '.join(lint_args)}".rstrip(), out)


def make_packages(root: Path, files: list[Path]) -> None:
    """Add a missing __init__.py to every folder between [root] and [files]."""
    for file in files:
        for folder in file.parents:
            if folder == root or root not in folder.parents:
                break
            (folder / "__init__.py").touch()


def check_scaffold(template: templates.Template, tmp: Path) -> None:
    adapters: dict[str, dict[str, object]] = template.data["scaffold"].get("adapters", {"none": {}})
    dev_packages = template.data["scaffold"].get("dev_dependencies", {}).get("packages", [])
    for adapter, config in adapters.items():
        name = f"scaffold-{adapter}"
        ok, out = run([sys.executable, str(SCRIPTS / "init_project.py"), "--name", name, "--adapter", adapter,
                       "--template", template.ref, "--path", str(tmp)], tmp)
        if not check(ok, f"{adapter}: init_project", out):
            continue
        project = tmp / name
        ok, out = run([sys.executable, str(SCRIPTS / "init_feature.py"), "--feature", "song_library",
                       "--subfeature", "playlists", "--adapter", adapter], project)
        if not check(ok, f"{adapter}: init_feature", out):
            continue
        deps = [str(d) for d in config.get("dependencies", [])]  # type: ignore[union-attr]
        dev = [*dev_packages, *(str(d) for d in config.get("dev", []))]  # type: ignore[union-attr]
        if deps:
            ok, out = run(["uv", "add", "--quiet", *deps], project)
            check(ok, f"{adapter}: uv add {' '.join(deps)}", out)
        ok, out = run(["uv", "add", "--quiet", "--dev", *dev], project)
        check(ok, f"{adapter}: uv add --dev", out)
        run(["uv", "run", "ruff", "check", "--fix", "--quiet", "."], project)
        quality_gate(project, adapter)


def check_template(template: templates.Template, args: argparse.Namespace) -> None:
    print(f"\n══ {template.ref}")
    step("2. Template")
    errors, warnings = templates.problems(template)
    for warning in warnings:
        print(f"  ! {warning}")
    check(not errors, "templates.py validate", "\n".join(errors))

    step("3. Code in the rules vs the example")
    blocks = doc_blocks(template)
    print(f"  found {len(blocks)} file blocks in the rules")
    compare_with_example(template, blocks)
    missing = sorted(
        f"{doc.relative_to(template.folder)}: {path}"
        for doc in template.doc_files()
        for path in EXAMPLE_LINK.findall(doc.read_text(encoding="utf-8"))
        if "*" not in path and "<" not in path and not (template.example_dir / path).exists()
    )
    check(not missing, "every `example/…` path in the rules exists", "\n".join(missing))

    if args.no_uv:
        return
    tmp = Path(tempfile.mkdtemp(prefix="py_clean_arch_selfcheck_"))
    project = tmp / "example"
    shutil.copytree(template.example_dir, project, ignore=templates.COPY_IGNORE)
    (project / templates.PROJECT_FILE).write_text(f'template = "{template.ref}"\n', encoding="utf-8")

    step("4. Example")
    quality_gate(project, "example")

    feature = template.data["example"].get("doc_feature")
    docs_package = template.data["example"].get("docs_package", "my_app")
    if blocks and feature:
        step("5. Feature from the rules, compiled inside the example")
        written = []
        for path, code in blocks.items():
            target = project / path
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code, encoding="utf-8")
            written.append(target)
        make_packages(project / "src", written)
        feature_dir = feature.replace(f"src/{docs_package}/", f"src/{template.example_package}/")
        for cmd in (["uv", "run", "ruff", "check", feature_dir], ["uv", "run", "mypy"]):
            ok, out = run(cmd, project)
            check(ok, f"rules: {' '.join(cmd[2:])}", out)
        ok, out = run([sys.executable, str(LINTER), feature_dir, "--strict", "--ignore", "di_naming"], project)
        check(ok, f"rules: linter --strict ({feature_dir})", out)

    step("6. Scaffold: init_project + init_feature for every adapter")
    check_scaffold(template, tmp)

    if args.keep:
        print(f"\n  temp projects: {tmp}")
    else:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-uv", action="store_true", help="skip the steps that need uv (and the network)")
    parser.add_argument("--keep", action="store_true", help="keep the temp projects")
    parser.add_argument("--template", help="check only this template (name@version)")
    args = parser.parse_args()

    step("1. Linter unit tests")
    ok, out = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], SKILL_ROOT)
    check(ok, "tests/", out)

    refs = (
        [templates.load(args.template).ref]
        if args.template
        else [f"{n}{templates.SEPARATOR}{v}" for n in templates.names() for v in templates.versions(n)]
    )
    for ref in refs:
        check_template(templates.load(ref), args)

    print()
    if _failures:
        print(f"✗ {len(_failures)} check(s) failed")
        return 1
    print("✓ all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
