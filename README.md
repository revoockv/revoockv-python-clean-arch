# revoockv-python-clean-arch

An agent skill (Claude Code, Cursor, Codex and other agents that read `SKILL.md`) for building Python projects with clean architecture by **templates**. A template holds every choice of the architecture and code style — folders, use cases, errors, data design, DI, presentation, style, tests, git — split into small rule files, plus an example project built with all of it. The default template, `revoockv-original`, is data / domain / presentation per feature with mandatory use cases, `Result[T]` consumed with `match`, `ABC` interfaces and an own typed DI container. Make your own template from it (`docs/constructor.md`); templates have their own versions, the skill has its own.

The agent uses it to create projects and features, refactor existing code into the architecture, split big modules into data sources and services, wire DI per feature and add FastAPI / Typer adapters. A linter checks the result.

> **About this skill.** This is my own attempt at understanding clean architecture in Python, not an official or final standard. It started as a port of my Flutter skill ([revoockv-flutter-clean-arch](https://github.com/revoockv/revoockv-flutter-clean-arch)), and the rules here are how I see it today. I keep learning, so I will keep updating the skill: rules can change, including breaking ones, every time I understand something better. Each change is listed in [CHANGELOG.md](CHANGELOG.md). Issues and suggestions are welcome.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills):

```bash
# for every project (user level)
npx skills add revoockv/revoockv-python-clean-arch -g

# only for the current project
npx skills add revoockv/revoockv-python-clean-arch

# for a specific agent
npx skills add revoockv/revoockv-python-clean-arch -g -a claude-code
```

Update later with `npx skills update`.

Manually: clone the repository into your agent's skills folder, e.g.

```bash
git clone https://github.com/revoockv/revoockv-python-clean-arch ~/.claude/skills/revoockv-python-clean-arch
```

## Use

Ask the agent in plain words, for example:

- "Create a Python CLI for my notes with Typer"
- "Add a songs feature with a FastAPI router"
- "Refactor `src/scraper` into the clean architecture"
- "This data source has 400 lines — split it"

The agent follows `SKILL.md` and the template's rules, then runs ruff, mypy, pytest and the linter.

## What it enforces (template `revoockv-original`)

- **Layers per feature:** `data` / `domain` / `presentation`; `core` mirrors the same layout.
- **Use cases:** one per user ↔ app interaction; one class, async `__call__`, no try/except.
- **Results:** `Result[T] = Success[T] | Failure`, consumed with `match`; repositories turn exceptions into `Failure` and log.
- **Data design:** one data source per external system, one service per library or tool, parsing in the model, the repository orchestrates them; no file over 200 lines.
- **Interfaces:** `ABC` base classes, so one family of classes shares one type.
- **DI:** an own typed `Container`; `register_<feature>(container)` per feature; adapters reach use cases only through `<feature>_getters.py`.
- **Constants:** inside the owning class, never at module level in domain or presentation.
- **Tooling:** Python 3.12+, uv, ruff, `mypy --strict`, pytest; Google docstrings on every public declaration; stdlib logging injected by constructor.

## Contents

```
SKILL.md                         how the agent finds the template and reads only what the task needs
templates/index.toml             the default template
templates/<name>/<version>/      template.toml (choices, topics, scaffold, lint), rules/<topic>/*.md,
                                 scaffold/ (stub files), example/ (runnable project)
docs/constructor.md              how templates are built, made, changed and versioned
docs/linter.md                   the architecture linter
docs/example_app.md              the program every template's example builds
scripts/                         templates, project/feature generators, linter, self-check
tests/                           linter unit tests
```

## Scripts

Run them from the skill folder with Python 3.12+ (no third-party packages needed).

```bash
# templates: list, show, choose, create, version, validate
python3 scripts/templates.py list
python3 scripts/templates.py show --project path/to/project
python3 scripts/templates.py use revoockv-original@1.0.0 --project path/to/project
python3 scripts/templates.py new my-arch --from revoockv-original@1.0.0
python3 scripts/templates.py bump my-arch --to 1.1.0
python3 scripts/templates.py validate --all

# a new project and a feature
python3 scripts/init_project.py --name my-app --adapter typer
python3 scripts/init_feature.py --feature notes --adapter typer

# architecture linter (23 rules)
python3 scripts/py_clean_arch_linter.py path/to/project --strict

# self-check of every template: rules vs example, example quality gate, scaffold for every adapter
python3 scripts/selfcheck.py
```

`selfcheck.py` needs [uv](https://docs.astral.sh/uv/) and network access to PyPI; `--no-uv` skips those steps.

## Versioning

[Semantic Versioning](https://semver.org/) for the skill ([CHANGELOG.md](CHANGELOG.md)) and, separately, for every template (`templates/<name>/CHANGELOG.md`).

## License

[MIT](LICENSE)
