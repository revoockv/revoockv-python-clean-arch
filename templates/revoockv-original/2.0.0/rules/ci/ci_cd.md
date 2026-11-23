# CI/CD (GitHub Actions)

`init_project.py` writes `.github/workflows/ci.yml`. It runs on GitHub's machines: free and unlimited for public
repositories, 2000 minutes a month for private ones on the Free plan.

| When | What runs |
|---|---|
| push to `main` / `develop`, a pull request | the quality gate: `uv sync`, `ruff check`, `ruff format --check`, `mypy`, `pytest`, the architecture linter `--strict` |
| a pushed tag `vX.Y.Z` | the quality gate, then a GitHub release whose notes are the `## [X.Y.Z]` section of `CHANGELOG.md` (no section → notes generated from the commits) |

- CI gets the linter from the skill repo (`revoockv/revoockv-python-clean-arch`); the linter follows the project's
  `.clean_arch.toml`.
- A release: finish `develop`, write the `## [X.Y.Z] - <date>` section of `CHANGELOG.md`, merge into `main`
  (`--no-ff`), `git tag -a vX.Y.Z -m vX.Y.Z`, `git push origin main develop vX.Y.Z` (`rules/git/git_rules.md`). The
  tag starts the release; nothing is published by hand.
- Publishing a package (PyPI) is a job after `release`: `uv build` and `pypa/gh-action-pypi-publish` with trusted
  publishing (`permissions: id-token: write`, the repository registered on PyPI) — no tokens in the repository.
- Keep the workflow the same as the local gate: a check that runs only in CI surprises; one that runs only locally
  is skipped.
- See a run on the repository's **Actions** tab; a red step there is a failed gate, fixed like a local one.
