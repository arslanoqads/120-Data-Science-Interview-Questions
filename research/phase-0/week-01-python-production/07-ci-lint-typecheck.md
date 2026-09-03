# 07 — CI: lint + type-check on every push (Week 1 build gate)

> Week 1 augment — syllabus build requires CI running lint + type-check. Legal sources only.

---

## Fundamentals

Continuous Integration runs automated checks on every push/PR so main stays releasable. For Week 1, the minimum bar is:

1. **Lint** — style/bugbear rules (increasingly **Ruff**, which replaces flake8/isort/many pylint rules; can format too).  
2. **Type-check** — mypy (or chosen checker) on `src/`.  
3. Later weeks add tests, but skeleton pytest should at least *collect*.

CI is the enforcement mechanism that makes typing/layout/deps real—not optional local habits.

---

## Alternatives & Tradeoffs

| Lint stack | Pros | Cons |
|------------|------|------|
| Ruff | Extremely fast; one tool for lint+format; Astral ecosystem with uv | Some pylint deep checks absent |
| flake8 + plugins + black + isort | Familiar | Slower; many configs |
| pylint alone | Deep | Noisy; slow |

| CI host | Notes |
|---------|-------|
| GitHub Actions | Default for public portfolio repos |
| Cloud Build / GitLab CI | Enterprise |

**Tradeoff:** Fail PR on mypy errors from day one (strict learning) vs warn-only until coverage exists (mypy docs still say get CI running ASAP even with ignores).

---

## Necessity

Without CI:
- Typed code regresses on the next feature branch.  
- Interviewers clone repo and find no green checks.  
- “It passed on my laptop” with different Ruff/mypy versions.

---

## Industry Practice

### Common
No CI; or CI only runs `pytest` without lint/types.

### Senior
```yaml
# sketch — research aide, not copy-paste gospel
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - install uv
      - uv sync --frozen --group dev
      - uv run ruff check .
      - uv run ruff format --check .
      - uv run mypy src
      - uv run pytest -q
```
- Pin tool versions via lockfile.  
- Cache uv download cache.  
- Required status checks on `main`.  
- Pre-commit optional mirror of the same hooks for local speed; CI remains source of truth.

### Ruff + mypy complementarity (research consensus 2025–26)
- Ruff = lint/format (file-local); mypy = cross-module types. **You need both.**  
- Disable Ruff `ANN*` when mypy strict/`disallow_untyped_defs` is on — duplicate diagnostics.  
- Isolate caches: `RUFF_CACHE_DIR` vs `MYPY_CACHE_DIR`; don’t share across Python versions.  
- Pre-commit: for mypy set `pass_filenames: false` so full import graph is checked.  
- Prefer `uv run ruff` / `uv run mypy` so CI and local use lockfile versions.  
- GitHub: `ruff check --output-format=github` for inline annotations; official `astral-sh/ruff-action` available.

Ruff docs: https://docs.astral.sh/ruff/  
mypy in CI: https://mypy.readthedocs.io/en/stable/existing_code.html  
Ruff+mypy CI integration: https://python-type-hints.com/static-analysis-tools-ci-integration/ruff-linter-integration/integrating-ruff-check-with-mypy-in-ci/  
Quality stack writeup: https://blog.marcosalonso.dev/the-complete-python-code-quality-stack-in-2026-ruff-mypy  

---

## Concrete Scenario

Syllabus: “CI running lint + type-check on every push.” A PR that adds an untyped FastAPI route fails mypy in CI → author adds annotations before merge. That ratchet is how Spring/Dropbox kept coverage from decaying.

Second scenario: team enables both Ruff `ANN` and mypy strict → noisy duplicate PR comments; seniors disable `ANN*` and keep mypy as annotation authority.

---

## Open Questions

- Ruff’s growing type-awareness vs keeping mypy forever?  
- Should format check be blocking or bot-autofix?  
- basedpyright in CI instead of mypy for greenfield uv+ruff stacks?

---

## Sources

- https://docs.astral.sh/ruff/  
- https://docs.astral.sh/ruff/configuration/  
- https://mypy.readthedocs.io/en/stable/existing_code.html  
- https://docs.github.com/en/actions  
- https://pre-commit.com/  
- https://python-type-hints.com/static-analysis-tools-ci-integration/ruff-linter-integration/integrating-ruff-check-with-mypy-in-ci/  
- https://python-type-hints.com/static-analysis-tools-ci-integration/pre-commit-hooks-setup/  
- https://blog.marcosalonso.dev/the-complete-python-code-quality-stack-in-2026-ruff-mypy  
- https://helpmetest.com/blog/ruff-python-linting-testing-ci/  
