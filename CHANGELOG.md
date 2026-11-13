# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
