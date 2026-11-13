# Git rules

## Branch Strategy

```
main           ← stable, always runnable, tagged with releases
└── develop      ← integration branch, next release
       ├── feature/001-ai-chat
       ├── feature/002-media-gen
       ├── fix/004-state-leak
       └── refactor/002-extract-logic
```

### Branch types

| Prefix | Use for |
|---|---|
| `feature/<num>-<name>` | New capability |
| `fix/<num>-<name>` | Bug fix |
| `refactor/<num>-<name>` | Restructure, no behavior change |
| `docs/<num>-<name>` | Documentation changes |
| `test/<num>-<name>` | Add or fix tests |
| `style/<num>-<name>` | Formatting, linting, no logic change |

### Branch naming

- Number is zero-padded 3 digits: `001`, `002`, `003`...
- Name is kebab-case, short and descriptive.
- If a task exceeds 999, let it grow naturally: `1000`, `1001`...

### Branch flow

1. Create branch from `develop`: `git switch -c feature/001-ai-chat develop`
2. Work and commit on the branch.
3. When done, merge to `develop`: `git switch develop && git merge feature/001-ai-chat`
4. Keep the branch: do **not** delete it after the merge. Work often has to be finished or corrected later, and the branch is where that continues (merge it again with `--no-ff` when done). Delete a branch only when the user asks: `git branch -d feature/001-ai-chat`
5. When `develop` is ready for release, merge to `main` and tag.

### Release branches

Not used normally. Only create a `release/<version>` branch if you need to fix `main`
while `develop` is in progress with a new feature.

---

## Commit Messages

Format:

```
[TYPE-NUM] short description
```

### Types

| Type | Use for |
|---|---|
| `FEAT` | New capability |
| `FIX` | Bug fix |
| `REFACTOR` | Restructure, no behavior change |
| `DOCS` | README, comments, changelog |
| `TEST` | Add or fix tests |
| `STYLE` | Formatting, linting, no logic change |

### Rules

- One logical change per commit.
- Imperative mood: "add", "fix", "extract" — not "added", "fixes", "extracting".
- Max ~72 characters in the subject line.
- No messages like "fix", "wip", "stuff", "update".
- The task number in the bracket matches the branch number.
- **The commit type prefix MUST match the branch prefix.**
  The tag type (`FEAT`, `FIX`, `REFACTOR`, `DOCS`, `TEST`, `STYLE`) is
  determined by the **branch**, not by the nature of the individual commit.
  Even when fixing a bug or adding logging during feature development,
  the commit tag stays `FEAT` because we are on a `feature/` branch.
  Use `FIX` only on a `fix/` branch, `REFACTOR` only on a `refactor/` branch, etc.

### Examples

```
[FEAT-001] add core folder
[FEAT-001] add chat session model
[FEAT-001] add chat screen UI
[FEAT-001] wire up DI for chat
[FEAT-003] fix python process execution: resolve absolute paths, add logging, disable sandbox
[FIX-004] fix BLE connection leak
[REFACTOR-002] extract chat session logic
[DOCS-003] update README with voice section
[TEST-001] add chat repository tests
[STYLE-005] apply ruff format
```

### Common Mistake

```
// WRONG — on feature/003-tts branch, do NOT use FIX tag:
[FIX-003] fix python process execution    ← WRONG, we are on a feature branch

// CORRECT — the tag matches the branch prefix:
[FEAT-003] fix python process execution   ← RIGHT, "fix" in the description is fine,
                                           ← but the tag prefix must be FEAT
```

The word "fix" can appear in the **description** (imperative mood), but the **type
prefix** in the bracket must always match the branch prefix.

### Grep by task

```bash
git log --oneline --grep="FEAT-001"
```

---

## Tags

Tags mark permanent, named points in history. Unlike branches, they don't move.

### When to tag

Tag on `main` only, when a state is "good enough to call a version":

```bash
git switch main
git tag -a v0.1.0 -m "First runnable version — empty container, macOS only"
```

### Versioning

Semantic versioning: `v<major>.<minor>.<patch>`

| Change | Bump |
|---|---|
| Breaking change (rules, architecture) | MAJOR |
| New feature added | MINOR |
| Bug fix | PATCH |

### Common commands

```bash
# List all tags
git tag -l

# List tags matching a pattern
git tag -l "v0.*"

# See what a tag points to
git show v0.1.0

# Check out a tagged commit
git checkout v0.1.0

# Diff between two tags
git diff v0.1.0 v0.2.0
```

### Light vs annotated

Always use annotated tags (`-a`) for version tags. They store author, date, and message.

---

## Pre-commit Checklist

- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] `uv run mypy` passes
- [ ] `uv run pytest` passes
- [ ] `python3 <skill_base>/scripts/py_clean_arch_linter.py --strict` passes
- [ ] `uv.lock` is committed together with `pyproject.toml` changes
- [ ] No secrets or API keys in code
- [ ] No `.env`, `.venv/` or caches staged
- [ ] `.skills/` is not staged
