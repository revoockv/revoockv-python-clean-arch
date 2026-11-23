# Architecture linter

`scripts/py_clean_arch_linter.py` parses the project with `ast` (nothing is imported or executed; no third-party
packages needed). It complements ruff and mypy: those check generic Python quality, this checks layering, naming and
the template's conventions.

It follows the project's template (`.clean_arch.toml` next to `pyproject.toml`, else the default; `--template REF`
for one run): `folder_structure` checks its `[structure]`, the rules of `[lint] off` do not run, the opt-in rules run
only when `[lint] on` names them, those of
`[lint] warn` are shown as warnings that `--strict` does not fail on, and `[lint.params]` sets `allowed_numbers`,
`max_file_lines` and `constant_layers`.

**Default target = the whole project.** Run it with no path from the project root; it finds `src/<package>/`. Narrow
it to one feature only when the user names it.

```bash
python3 <skill_base>/scripts/py_clean_arch_linter.py                              # whole project
python3 <skill_base>/scripts/py_clean_arch_linter.py src/<package>/features/<f>   # one feature
python3 <skill_base>/scripts/py_clean_arch_linter.py --strict                     # exit 1 on errors (CI)
python3 <skill_base>/scripts/py_clean_arch_linter.py --rules import_violation,naming_file
python3 <skill_base>/scripts/py_clean_arch_linter.py --json
python3 <skill_base>/scripts/py_clean_arch_linter.py --ignore magic_strings        # only when the user asks
python3 <skill_base>/scripts/py_clean_arch_linter.py --list-rules
```

**23 rules:** `folder_structure`, `naming_file`, `naming_class`, `use_case_shape`, `use_case_no_try`,
`import_violation`, `relative_import`, `domain_repository`, `repository_impl`, `repository_result`,
`repository_logging`, `model_mapping`, `entity_frozen`, `logger_injection`, `no_print`, `container_access`,
`docstring_public`, `type_hints`, `magic_numbers`, `magic_strings`, `module_constants`, `di_naming`, `file_size`.

**Opt-in** (`[lint] on`; templates made before them keep passing): `typed_failures` — `Result[T]` without its
failure type, and `Failure(<text>)` (a string, an f-string, `str(e)`, `.format()`, a string constant). On in
`revoockv-original@2.0.0`.

`file_size` fails a file with more than `max_file_lines` non-blank lines: such a file does several jobs. Split it by
the template's data design (`rules/data/data_design.md` of `revoockv-original`) instead of raising the limit.

All rules the template does not turn off run. Disable a rule with `--ignore` only when the user explicitly asks; to
drop it for good, put it in the template's `[lint] off` (a new template version). Tests of the linter:
`tests/test_linter.py` (`python3 -m unittest discover -s tests`).
