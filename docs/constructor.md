# Template constructor

How to make, change, version and choose an architecture template. Read this only when the task is about templates
themselves; building a project needs only the project's template (`SKILL.md`).

## 1. What a template is

```
templates/
  index.toml                    default = "name@version"
  <name>/
    CHANGELOG.md                the template's versions
    <version>/                  MAJOR.MINOR.PATCH; a released version is never changed
      template.toml             choices, topic → rule files, folders, scaffold, example, lint
      rules/<topic>/*.md        the rules, one subject per file
      scaffold/                 stub files of init_project / init_feature
      example/                  a project built with every rule; selfcheck verifies it
```

A project chooses its template in `.clean_arch.toml` next to `pyproject.toml` (`template = "name@version"`, or
`"name"` for its newest version); without it the default of `templates/index.toml` applies. `init_project.py` writes
that file.

## 2. What a template decides

Every subject below is the template's choice. Answer each in one line in `[choices]`, give the details in the rule
file of its topic. A subject the new template does the same way as its source stays as copied.

| Topic | Decide |
|---|---|
| `structure` | layers and their folders (`[structure]`); what `core/` holds; where features and subfeatures live |
| `use_cases` | use cases required or not; their shape (class with `__call__`, function); what they return |
| `errors` | the result type (own `Result`, `returns`, exceptions); failure kinds; where errors are caught |
| `data` | data sources, services, models; who orchestrates them; the file size limit |
| `di` | how dependencies are created and found: a container, a composition root, FastAPI `Depends`; startup work |
| `presentation` | adapters (FastAPI, Typer, workers…), how they reach use cases, schemas |
| `style` | constants and magic values; naming; imports; docstrings; logging |
| `testing` | what is tested on each layer; fakes or mocks; test DI |
| `git` | branch types and names, commit and merge messages, releases, tags |
| `packages` | Python version, pyproject, tooling |
| `workflow`, `decisions` | the order of work for a new project, feature, refactor; quick "you need X → do Y" answers |
| `example_feature` | optional: a worked feature that lives only in the rules |

## 3. template.toml

| Section | What it holds |
|---|---|
| `name`, `version`, `description`, `author` | The template; `name` and `version` equal its folders |
| `[choices]` | One short answer per subject; the agent reads them first |
| `[rules]` | Topic → rule files (relative to the version folder). Topics of section 2; a template may add its own |
| `[structure]` | `strict_layers`; `[structure.required]` and `[structure.optional]`: layer → folders of every feature and of `core/`. `init_*` create the required ones, the linter's `folder_structure` checks them |
| `[scaffold]` | `core_files` (copied from the example by `init_project`), `next_step`; `[scaffold.adapters]` adapter → `dependencies`, `dev`, `script`; `[scaffold.wiring]` → the import and the line `init_feature` adds before `# </marker>` of a root file; `[scaffold.dev_dependencies] packages` |
| `[example]` | `path`, `package`; `docs_package` (package name in the rules' code); `doc_paths` (rule code blocks compiled in the example), `same_as_example` (blocks that must equal the example's files), `doc_feature` (a feature that lives only in the rules) |
| `[lint]` | `off` — rules the template does not use; `on` — opt-in rules it uses (`typed_failures`); `warn` — rules shown as warnings (`--strict` does not fail on them) |
| `[lint.params]` | `allowed_numbers`, `max_file_lines`, `constant_layers` |

Stub files are `*.tmpl` under `scaffold/`: `project/` (written into the new project), `main/<adapter>.py.tmpl`,
`feature/`, `subfeature/`, `adapters/<adapter>/` (under the feature) and `feature_tests/` (under
`tests/features/<feature>/`). `{{package}}`, `{{dist}}`, `{{name}}`, `{{template}}`, `{{scripts}}`, `{{feature}}`,
`{{Feature}}`, `{{feature_slug}}`, `{{subfeature}}`, `{{Subfeature}}` are filled in, in names and text.

A rule code block is compiled when the line above it is its path in backticks, then a blank line:

````
`src/my_app/features/auth/domain/entities/auth_user.py`

```python
...
```
````

## 4. Make a template

1. `python3 scripts/templates.py new <name> --from <source>@<version>` — copies the source as `<name>/1.0.0`.
2. `[choices]` first: change the answers that differ, then `[structure]`, `[scaffold]`, `[lint]`.
3. Rewrite the rule files of the changed topics; delete files and topics the template does not use (and their entries
   in `[rules]`). Change the `scaffold/` stubs to the new style.
4. Rebuild `example/` by the new rules: the same program in every template (`docs/example_app.md`) so templates can be
   compared. Add its packages with `uv add` (they are pinned in its `uv.lock`).
5. Run the linter on the example; for each rule that fires decide: the example breaks the template's rules (fix the
   example) or the rule does not fit the template (put it in `[lint] off`, say why in a comment).
6. `python3 scripts/templates.py validate <name>` and `python3 scripts/selfcheck.py --template <name>@1.0.0`.
7. Optional: `templates.py set-default <name>@1.0.0`, or `templates.py use <name> --project <path>` per project.

## 5. Write rules that cost little context

- One subject per file, at most ~250 lines (`validate` warns above).
- State a rule once, in the file of its topic; other files link to it.
- Do not copy code that is in the example: write `example/<path>` and the reader opens it when needed
  (`selfcheck` checks that every such path exists). Code in the rules only for what the example does not show.
- Put the short answer first (`[choices]`, `decisions.md`), the reasons and edge cases after.

## 6. Change and version a template

- `python3 scripts/templates.py bump <name> --to X.Y.Z` copies the newest version; change the copy, describe it in
  `templates/<name>/CHANGELOG.md`, run the self-check. Projects pinned to the old version keep it.
- MAJOR: a rule change that makes existing code wrong; MINOR: a new rule or topic that old code still meets; PATCH:
  wording and fixes.
- The skill has its own versions (`CHANGELOG.md` in the skill root): a change of the scripts or of this constructor is
  a skill change; a change of rules is a template change.

## 7. Commands

| `scripts/templates.py …` | What it does |
|---|---|
| `list` | Every template version, the default marked |
| `show [REF] [--project P]` | Choices, folder and topics with their sizes |
| `rules [REF] --topic a,b` | Paths of the rule files of topics |
| `use REF --project P` | The project uses REF (writes `P/.clean_arch.toml`) |
| `set-default REF` | The template of projects that choose none |
| `new NAME --from REF` | A new template (1.0.0) copied from REF |
| `bump NAME --to X.Y.Z` | A new version from the newest one |
| `validate [REF \| --all]` | Keys, files, sizes, scaffold, lint rules and params |
