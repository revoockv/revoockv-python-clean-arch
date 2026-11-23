# revoockv-original — changelog

Versions of this template. The skill itself has its own versions (`CHANGELOG.md` in the skill root).

## [2.0.0] - 2026-11-23

- **Typed failures**: `Result[T, F]` and `Failure[F]` carry a member of the feature's failure type
  (`domain/entities/<feature>_failure.py`, an `Enum` with a `FailureKind`), never text. The text lives in
  `presentation/text/<feature>_failure_text.py` (exhaustive `match`), the HTTP status in
  `core/presentation/api/failure_status.py`. `failure_kind.py` is a core file of the scaffold.
- The example: `NoteFailure` (`NOT_FOUND` from the new `RowNotFoundError`), `StatisticsFailure`; the auth feature of
  the rules: `AuthFailure`, `InvalidCredentialsError`, `AuthFailureText`.
- `[lint] on = ["typed_failures"]`.

## [1.0.0] - 2026-11-13

- The rules of the skill up to 0.3.0, split by topic (`rules/<topic>/`), with `template.toml`, `scaffold/` and an
  `example/` project: notes + statistics over one database in core, a Typer CLI and a FastAPI adapter, tests on every
  layer.
- The auth feature of `feature_template_auth.md` lives on as `rules/examples/auth_{domain,data,presentation,api}.md`;
  `selfcheck.py` compiles it inside the example. Code equal to the example is a link to `example/<path>`.
- New topic `data` → `data_design.md`: one data source per external system, one service per library/tool, parsing in
  the model, the repository orchestrates them; the new lint rule `file_size` (`max_file_lines = 200`).
- `decisions.md` gives the answer itself; `workflow.md` and `style/constants.md` hold what `SKILL.md` used to.
- Tests: `httpx2` for the FastAPI `TestClient`; `asyncio_default_fixture_loop_scope = "function"`.
