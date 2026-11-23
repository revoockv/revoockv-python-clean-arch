---
name: revoockv-python-clean-arch
description: Build Python projects by a chosen clean-architecture template (default revoockv-original - data / domain / presentation per feature, mandatory use cases, Result[T, F] with typed failures, ABC interfaces, own typed DI container with getters, uv + ruff + mypy --strict + pytest) and manage those templates. Use when the user asks to create a new Python project or feature, add use cases / repositories / data sources / services / DTO models, wire DI, add a FastAPI or Typer (or other) adapter, refactor an existing Python codebase into clean architecture, split a big module, check a project against the rules (linter), or to create, change, version, choose or validate an architecture template (folders, DI, use cases, errors, code style, tests, git rules).
metadata:
  version: 0.4.0
  author: revoockv
---

# Python clean architecture by templates

The rules live in **templates**: `templates/<name>/<version>/`. A template says how the project is built (folders, use cases, errors, data design, DI, presentation, code style, tests, git) and has an `example/` project built with all of it. The skill has its own versions (`CHANGELOG.md`); every template has its versions too (`templates/<name>/CHANGELOG.md`).

## 1. Find the template — always first

```bash
python3 <skill_base>/scripts/templates.py show --project <project_path>
```

It prints the template of the project (`<project>/.clean_arch.toml` next to `pyproject.toml`, else the default of `templates/index.toml` — now `revoockv-original@2.0.0`), its choices and its topics with their sizes. **Follow that template only.** When its rules and your memory disagree, the template's `example/` wins.

## 2. Read only the topics of the task

```bash
python3 <skill_base>/scripts/templates.py rules --project <project_path> --topic workflow,structure
```

prints the files to read. Topics (`[rules]` of `template.toml`):

| Task | Topics |
|---|---|
| New project / feature / refactor | `workflow`, `structure`, then `use_cases`, `errors`, `data`, `di`, `presentation` as you reach them; `example_feature` for a full worked feature |
| A big file, several sources, scrapers, converters | `data` |
| "Which pattern for X?" | `decisions` |
| Constants, imports, docstrings, logging | `style` |
| Tests | `testing` |
| Commits, branches, merges, releases | `git` |
| pyproject, uv, tooling | `packages` |

Do not read every topic up front: each costs context. A rule that names `example/<path>` points to working code in the template folder: open that file when you need the code.

## 3. Tools

| Command | What it does |
|---|---|
| `scripts/init_project.py --name <n> [--adapter none\|fastapi\|typer]` | A new project from the template's scaffold; writes `.clean_arch.toml` |
| `scripts/init_feature.py --feature <f> [--adapter …] [--subfeature <s>]` | Feature folders, DI stubs, adapter stubs, test packages; wires `di.py` / `main.py` |
| `scripts/py_clean_arch_linter.py [path] [--strict]` | Architecture linter (23 rules + opt-in `typed_failures`) — run it after every change; it follows the template. Details: `docs/linter.md` |
| `scripts/selfcheck.py [--template REF]` | Every template: rules vs example, example quality gate, scaffold for every adapter. Run it after changing the skill or a template |

The quality gate of a project — a task is done only when all pass:

```bash
uv run ruff check --fix . && uv run ruff format . && uv run mypy && uv run pytest
python3 <skill_base>/scripts/py_clean_arch_linter.py
```

Never copy the scripts into a project; run them from the skill folder. Disable a lint rule only when the user asks.

## 4. Making or changing a template

Only for tasks about templates themselves (create, change, version, choose, validate): read `docs/constructor.md`.
