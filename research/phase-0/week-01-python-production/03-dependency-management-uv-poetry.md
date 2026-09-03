# 03 — Dependency management (uv / Poetry)

> Week 1 concept research (deep). Legal sources only.

---

## Fundamentals

### Problem
Python apps depend on a graph of packages. Without a **lockfile**, two machines resolve different transitive versions → “works on my machine,” broken CI, and **eval baseline drift** when `httpx`/`openai`/`numpy` shift under you.

### Modern unit of config
`pyproject.toml` (PEP 518/621) declares project metadata and dependencies. A tool-specific **lockfile** pins the full resolved graph with hashes where supported.

### Tool landscape
| Tool | Role |
|------|------|
| **pip + requirements.txt** | Historic; weak unless fully pinned (`pip-tools` compile) |
| **pip-tools** (`pip-compile`) | Lock from `.in` files; still common in enterprises |
| **Poetry** | Project+lock+venv; popularized the workflow; historically `[tool.poetry]` tables |
| **PDM / Hatch / Rye** | Alternative project managers |
| **uv** (Astral, Rust) | Fast all-in-one: resolve/lock, venv, Python install, `uvx` tools, pip-compatible CLI, workspaces |

Astral positions uv as replacing pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv—with claimed **10–100×** speedups vs pip (see BENCHMARKS.md).

### uv project workflow (research summary)
```
uv init → uv add <pkg> → uv lock → uv sync → uv run <cmd>
```
- Creates `.venv`  
- Writes/updates `uv.lock` (universal lockfile)  
- PEP 621 `[project]` metadata  
- `.python-version` via `uv python pin`  
- Scripts with inline dependency metadata (`uv add --script`)  
- `uvx` / `uv tool` for isolated CLIs  

### Dependency groups (PEP 735)
Standard `[dependency-groups]` for **non-published** deps (dev, test, lint)—distinct from `[project.optional-dependencies]` extras (user-facing optional features). uv/poetry/pip evolving support. Prevents tool-specific `[tool.poetry.group.dev]` lock-in when migrating.

### Workspaces
uv workspaces: multiple members, **one lockfile**, typically one root `.venv`. Cross-member deps: `{ workspace = true }` in `[tool.uv.sources]`. `uv sync --all-packages` installs members’ groups as needed. Intersection of `requires-python` across members.

---

## Alternatives & Tradeoffs

| Choice | Pros | Cons |
|--------|------|------|
| uv greenfield | Speed, Python mgmt, PEP 621, workspaces | Newer; lockfile uv-specific; org policy lag |
| Stay on Poetry | Mature DX, plugins, known to enterprises | Slower resolve; historically non-standard metadata; need pyenv/pipx alongside |
| pip-tools | Simple mental model; wide CI support | Split tooling; easy to forget compile |
| requirements.txt unpinned | Zero ceremony | Non-reproducible; security blind |
| Conda env.yml | Binary-heavy science stacks | Different ecosystem; awkward with pure app services |

**Docker:** `uv sync --frozen --no-dev` in builder; copy venv or install into runtime stage. Never resolve unlocked on the build server without review.

**LLM stack churn:** LangChain/LlamaIndex/openai release often. Lock + renovate/dependabot PRs with eval suite as gate—not blind upgrades.

---

## Necessity

Without locks:
- Silent major bumps break tool-calling JSON parsing.  
- Security audits cannot name installed versions.  
- Golden evals disagree across laptops.  
- Onboarding: hours of “install these somehow.”

Without a single tool:
- Poetry locally + pip in Docker → drift.  
- CI installs different extras than prod.

---

## Industry Practice

### Common
`pip freeze > requirements.txt` once; never re-compile; mix Poetry and pip.

### Senior
- One toolchain (uv strongly trending for new AI services 2025–26).  
- Commit lockfile.  
- `[dependency-groups]` for pytest/mypy/ruff.  
- Optional extras for `gpu`, `evals` if needed.  
- `uv sync --frozen` in CI and Docker.  
- Pin Python (`.python-version` + `requires-python`).  
- Document bootstrap: only `uv sync` supported.  
- Dependabot/renovate + eval CI for upgrades.

### Migration notes
Poetry → uv converters exist (`migrate-to-uv` via uvx in community docs). Prefer rewriting to PEP 621 when touching the project.

---

## Concrete Scenario

Official uv overview & project flow: https://docs.astral.sh/uv/  
Benchmarks: https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md  
Workspaces: https://docs.astral.sh/uv/concepts/projects/workspaces/  
PEP 735 explainer: https://pydevtools.com/handbook/explanation/what-is-pep-735/  
uv vs Poetry handbook: https://pydevtools.com/handbook/explanation/how-do-uv-and-poetry-compare/  
Poetry docs: https://python-poetry.org/docs/

**FDE interview line:** “We pin the full graph with uv.lock so retrieval eval scores are comparable week-over-week; upgrades go through a PR that re-runs the golden set.”

---

## Open Questions

1. Corporate risk of Astral/OpenAI ownership narratives for uv—does it change enterprise adoption?  
2. Universal lock vs platform-specific wheels for CUDA extras—best pattern for mixed CPU CI / GPU workers?  
3. Should eval dependencies be a separate dependency-group so prod images never see pytest/RAGAS? (Lean: yes.)  
4. When is conda still justified for an AI Engineer service role vs app-only uv?

---

## Sources

- https://docs.astral.sh/uv/  
- https://docs.astral.sh/uv/concepts/projects/  
- https://docs.astral.sh/uv/concepts/projects/workspaces/  
- https://github.com/astral-sh/uv/  
- https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md  
- https://python-poetry.org/docs/  
- https://peps.python.org/pep-0621/  
- https://peps.python.org/pep-0735/  
- https://pydevtools.com/handbook/explanation/what-is-pep-735/  
- https://pydevtools.com/handbook/explanation/how-do-uv-and-poetry-compare/  
- https://pip.pypa.io/en/stable/user_guide/#requirements-files  
- https://pip-tools.readthedocs.io/  
