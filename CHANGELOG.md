# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.5.0] - 2026-11-23

### Changed
- README is short: what the skill is for, install, use, templates, scripts, CI/CD. What a template enforces
  lives only in the template.

### Added
- Template `revoockv-original@2.0.0`, the new default: **typed failures**. `Result[T, F]`, a failure `Enum` per
  feature with a `FailureKind`, the text in `presentation/text/`, `FailureKind` → HTTP status in
  `core/presentation/api/failure_status.py` (template changelog). 1.0.0 stays for the projects that use it.
- Opt-in lint rules, turned on by a template's `[lint] on` (templates made before them keep passing):
  `typed_failures` — `Result[T]` without its failure type, and `Failure(<text>)`. `templates.py validate` checks
  `[lint] on`.
- `scripts/check_versions.py`: the `>=` bounds of a template's `example/pyproject.toml` vs PyPI (`[packages] tracked`
  narrows them); `--strict`, `--update`. revoockv-original@2.0.0 is on the latest versions.
- CI/CD of the skill: `.github/workflows/test.yml` (templates validate + selfcheck on every push and pull request) and
  `release.yml` (a pushed tag `vX.Y.Z` → selfcheck → the GitHub release from the `## [X.Y.Z]` section of this file).
- revoockv-original@2.0.0 topic `ci`: projects get `.github/workflows/ci.yml` from the scaffold.

---

## [0.4.0] - 2026-11-13

### Changed
- The rules live in versioned templates (`templates/<name>/<version>/`), like revoockv-flutter-clean-arch:
  `template.toml` (choices, topics, folders, scaffold, example, lint), `rules/<topic>/*.md`, `scaffold/` and a runnable
  `example/`. The rules up to 0.3.0 are template `revoockv-original@1.0.0`, the default (`templates/index.toml`).
  `references/` and `DECISIONS.md` moved into it.
- `SKILL.md` is a router: find the project's template, read only the topics of the task.
- `init_project.py` / `init_feature.py` build from the template's `scaffold/` and `[scaffold]` (adapters, wiring,
  core files) instead of code inside the scripts; `init_project.py` writes `.clean_arch.toml`; `--template` on both.
- The linter follows the project's template: `[structure]`, `[lint] off`, `[lint] warn` (warnings do not fail
  `--strict`), `[lint.params]` `allowed_numbers`, `max_file_lines`, `constant_layers`; `--template`; JSON output has
  `severity`.

### Added
- Lint rule `file_size` (23 rules): a file over `max_file_lines` non-blank lines must be split into data sources,
  services and models that the repository orchestrates (`rules/data/data_design.md`).
- `scripts/templates.py` (list, show, rules, use, set-default, new, bump, validate), `scripts/scaffold.py`,
  `scripts/selfcheck.py`, `tests/test_linter.py`.
- `README.md`, `LICENSE` (MIT), `docs/constructor.md`, `docs/linter.md`, `docs/example_app.md`.

---

## [0.3.0] - 2026-10-13

### Changed
- Use case definition: a use case is one interaction between the user and the app interface.
  Internal steps (detection, routing, splitting, retries, merging) belong in repositories/services;
  no use case per repository method and no chained helper use cases (`use_case_naming.md`,
  `SKILL.md`, `DECISIONS.md`).

---

## [0.2.0] - 2026-10-13

### Added
- Optional `data/services/` folder for technology adapters (converters, CLI tools, model runners):
  files `*_service.py`, classes `*Service`. Linter `folder_structure`, `naming_file`, `naming_class`
  accept it; `folder_structure.md` and `di_patterns.md` document data sources vs services.

---

## [0.1.0] - 2026-10-13

### Added
- Initial skill definition (`SKILL.md`), ported from `revoockv-flutter-clean-arch` 0.4.0 to Python.
- `DECISIONS.md` — "you need X → use pattern Y" table.
- Stack: Python 3.12+, uv, ruff, mypy --strict, pytest + pytest-asyncio, stdlib logging,
  own typed DI `Container`, framework-agnostic presentation (FastAPI / Typer / other).
- References:
    - `folder_structure.md`
    - `feature_template_auth.md` (generated from a project passing ruff, mypy --strict, pytest and the linter)
    - `result.md`
    - `use_case_naming.md`
    - `models_mapping.md`
    - `di_patterns.md`
    - `presentation_patterns.md`
    - `imports.md`
    - `logging_conventions.md`
    - `docstring_standard.md`
    - `testing.md`
    - `project_setup.md`
    - `git_rules.md`
- Scripts:
    - `scripts/init_project.py` — project skeleton (core, Result, Container, core DI, di.py, main.py, tests, pyproject)
    - `scripts/init_feature.py` — feature skeleton, DI stubs, adapter stubs, wiring into di.py / main.py
    - `scripts/py_clean_arch_linter.py` — 22 AST-based rules: `folder_structure`, `naming_file`,
      `naming_class`, `use_case_shape`, `use_case_no_try`, `import_violation`, `relative_import`,
      `domain_repository`, `repository_impl`, `repository_result`, `repository_logging`,
      `model_mapping`, `entity_frozen`, `logger_injection`, `no_print`, `container_access`,
      `docstring_public`, `type_hints`, `magic_numbers`, `magic_strings`, `module_constants`, `di_naming`

---

## Versioning Policy

This skill follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** — Breaking changes to rules, architecture patterns, or required packages.
  Existing projects may fail linting after upgrade.
- **MINOR** — New rules, new references, new scripts, new templates.
  Existing projects should still pass. May require opting into new rules.
- **PATCH** — Bug fixes in scripts, typo corrections, clarifications in references.
  No behavior change for conforming projects.

The linter version is tracked in `scripts/py_clean_arch_linter.py` (`__version__`).
