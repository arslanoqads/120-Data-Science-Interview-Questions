# Week 1 — Python for production, not for notebooks

> Phase 0 — Engineering Foundations  
> Raw research notes (not textbook prose). Legal sources only; no pirated books.

---

## Concept: Type hints and static typing (mypy)

### Fundamentals
Type hints are annotations that describe expected types of function parameters, return values, and variables. They do not change runtime behavior by themselves (unless you add runtime validators). Tools like **mypy** (and alternatives such as Pyright/Pylance, Pytype, or Astral’s `ty`) analyze those annotations *before* execution to catch mismatches: wrong argument types, missing returns, `None` not handled, etc. In production Python, typing is a CI gate and a documentation contract for LLM/API payloads (dicts vs Pydantic models), not optional “nice style.”

### Alternatives & Tradeoffs
- **mypy**: mature ecosystem, configurable strictness, good for gradual adoption on existing codebases (`disallow_untyped_defs` later). Incremental cache / `dmypy` for large repos.
- **Pyright / basedpyright**: often faster feedback in editors; slightly different type-system semantics than mypy — teams must pick one as the CI source of truth.
- **Runtime validation (Pydantic, msgspec)**: complementary, not a substitute — static types catch call-site mistakes; runtime validation catches malformed external I/O.
- **No typing**: fastest for throwaway notebooks; fails take-homes and multi-contributor services when shapes of RAG/agent payloads drift silently.
Tradeoff: strict typing slows early prototyping and fights dynamic LLM JSON until you model schemas; loose typing ships bugs that only appear under load or with provider response changes.

### Necessity
Skipping typing on a FastAPI/RAG service typically yields: incorrect optional handling around API responses, silent `Any` propagation through retrieval pipelines, and “works in notebook, fails in CI” regressions. mypy’s own guidance: put typing in CI ASAP so new code cannot introduce untyped holes.

### Industry Practice
- **Common:** sprinkle `str`/`dict` hints; ignore mypy locally; `ignore_missing_imports = True` globally.
- **Senior:** pin mypy version; config in `pyproject.toml`; start with a typed core (models, client wrappers); enable flags incrementally toward `--strict`; per-module overrides for untyped third parties; warm CI cache; treat `# type: ignore` as a reviewed debt item with error codes.

### Concrete Scenario
Spring’s engineering notes describe adopting mypy on a large monorepo until *strict* settings (notably `disallow_untyped_defs`) were sustainable, with third-party ignores scoped per library — a year-long climb from a few files to full coverage: https://notes.crmarsh.com/using-mypy-in-production-at-spring  
Official gradual-adoption path: https://mypy.readthedocs.io/en/stable/existing_code.html

### Open Questions
- Will Astral `ty` / Pyright convergence make mypy obsolete for greenfield apps, or will dual-checker friction persist?
- How much to type generative-AI boundaries (`dict[str, Any]` vs strict JSON Schema models) given provider schema churn?

### Sources
- https://mypy.readthedocs.io/en/stable/existing_code.html
- https://mypy.readthedocs.io/en/stable/config_file.html
- https://docs.python.org/3/library/typing.html
- https://notes.crmarsh.com/using-mypy-in-production-at-spring
- https://python-type-hints.com/static-analysis-tools-ci-integration/mypy-configuration-strictness/

---

## Concept: Project structure (src layout vs flat)

### Fundamentals
**Flat layout** puts the importable package next to `pyproject.toml` / tests at repo root. **src layout** nests importable code under `src/<package>/`. Python adds the CWD to `sys.path`, so flat layout can make tests import *uninstalled* source even when packaging is broken; src layout forces an install (usually editable) so tests exercise the packaged artifact.

### Alternatives & Tradeoffs
| Layout | Pros | Cons |
|--------|------|------|
| Flat | Quick REPL/`python script.py`; less setup | Tests can pass while wheels omit modules; import path pollution |
| Src | Catches packaging mistakes; pytest-recommended default for libs | Requires editable install / `uv sync`; slightly more ceremony |
| App-only “scripts” project | Fine for one-off tools (`uv init --no-package`) | Weak for services you ship as images/packages |

For a flagship FastAPI RAG service, src layout (or clear package boundary) matches interviewable “production package” expectations.

### Necessity
Without a real package boundary, notebook-style `sys.path` hacks and duplicate module names appear; Docker/`pip install .` then fails because tests never ran against installed code. PyPA documents accidental import of the in-development copy as a core flat-layout risk.

### Industry Practice
- **Common:** flat `app/` next to tests; `PYTHONPATH=.` in Docker.
- **Senior:** `src/<service>/` or well-defined package; editable install in CI; tests outside package; explicit console scripts; no reliance on CWD imports. `uv init` defaults toward src for packages.

### Concrete Scenario
PyPA comparison and rationale: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/  
pytest “Good Integration Practices” strongly suggests src layout especially with default import mode: https://docs.pytest.org/en/latest/goodpractices.html

### Open Questions
- For monorepos with many services, is `src/` per service vs `packages/<name>/` naming more important than the src-vs-flat binary?
- Do application-only Cloud Run services need src layout if never published to PyPI? (Still useful for install-faithful tests.)

### Sources
- https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
- https://docs.pytest.org/en/latest/goodpractices.html
- https://setuptools.pypa.io/en/latest/userguide/package_discovery.html
- https://pydevtools.com/handbook/explanation/src-layout-vs-flat-layout/

---

## Concept: Dependency management (uv / Poetry)

### Fundamentals
Dependency management pins direct + transitive packages so every developer and CI/CD installs the same graph. Modern Python uses `pyproject.toml` plus a **lockfile**. **Poetry** popularized this workflow; **uv** (Astral, Rust) is a fast all-in-one: resolve/lock, venvs, Python version install, tool runner (`uvx`), pip-compatible interface.

### Alternatives & Tradeoffs
- **pip + requirements.txt**: simple; weak reproducibility unless fully pinned + hashes (`pip-tools`).
- **Poetry**: mature DX; historically `[tool.poetry]` metadata (PEP 621 improving); slower resolve; needs pyenv/pipx for adjacent concerns.
- **uv**: 10–100× faster resolves (Astral claims vs pip); PEP 621 `[project]`; universal `uv.lock`; manages Python versions; newer, lockfile tool-specific.
- **PDM / Hatch / pip-tools**: viable; pick one lock toolchain and standardize.
Tradeoff: migrate-to-uv costs vs CI minutes saved; Poetry plugins vs uv speed; corporate “blessed” Poetry images vs new uv adoption.

### Necessity
Unlocked deps → “works on my machine,” silent OpenAI/httpx major bumps breaking tool-calling clients, and unreproducible security audits. LLM stacks move fast; without locks, eval baselines drift because library versions changed under you.

### Industry Practice
- **Common:** `pip freeze` once; mixed Poetry locally and pip in Docker.
- **Senior:** single tool (increasingly **uv** for greenfield 2025–26); lock committed; separate main/dev/optional groups; Docker uses `uv sync --frozen`; pin Python via `.python-version`; no blind `latest` base images without rebuild policy.

### Concrete Scenario
Astral uv docs position it as replacement for pip/pip-tools/poetry/virtualenv/pyenv/pipx: https://docs.astral.sh/uv/  
Benchmarks and feature comparison discussions: https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md  
Comparative handbook: https://pydevtools.com/handbook/explanation/how-do-uv-and-poetry-compare/

### Open Questions
- Post–OpenAI/Astral ownership narratives: does corporate ownership change enterprise adoption risk calculations?
- Should lockfiles be platform-universal (uv) or environment-specific — how to handle optional GPU/CUDA extras?

### Sources
- https://docs.astral.sh/uv/
- https://python-poetry.org/docs/
- https://pydevtools.com/handbook/explanation/how-do-uv-and-poetry-compare/
- https://github.com/astral-sh/uv/

---

## Concept: Virtual environments

### Fundamentals
A virtual environment is an isolated directory with its own Python interpreter site-packages so project A’s `langchain==x` does not collide with project B’s. Tools: `venv` (stdlib), `virtualenv`, Poetry env management, **uv** creating `.venv` automatically.

### Alternatives & Tradeoffs
- **Per-project `.venv`**: default best practice; easy to delete/recreate.
- **Conda/mamba**: better for heavy non-Python binary stacks (some ML); heavier, different mental model.
- **Docker-only isolation**: great for prod parity; slower inner loop if every tweak rebuilds images.
- **Global/user installs**: fine for one machine one project; catastrophic for multi-project TPM→engineer transition.
Tradeoff: conda for scientific deps vs uv/venv for app services; docker-compose for integration deps (DBs) while keeping Python deps in venv.

### Necessity
Without venvs: mysterious import of wrong `openai` SDK, broken type stubs, and CI that cannot reproduce local failures. Interview take-homes often fail on “candidate’s global site-packages.”

### Industry Practice
- **Common:** activate venv manually; forget to document Python version.
- **Senior:** tool creates env (uv/Poetry); never commit env dir; pin Python version; CI creates fresh env from lock; document `uv sync` / `poetry install` as the only supported bootstrap.

### Concrete Scenario
Python venv docs: https://docs.python.org/3/library/venv.html  
uv project environments: https://docs.astral.sh/uv/concepts/projects/layout/

### Open Questions
- Devcontainers vs local venv as the “default onboarding” path for FDE-style customer work?
- How to share CUDA toolchains cleanly with uv-managed envs?

### Sources
- https://docs.python.org/3/library/venv.html
- https://docs.astral.sh/uv/concepts/projects/
- https://pip.pypa.io/en/stable/user_guide/#virtual-environments

---

## Concept: Writing testable functions vs notebook cells

### Fundamentals
Notebooks optimize exploration: linear cells, hidden global state, ad-hoc plots. Production code needs **pure-ish functions**, dependency injection (pass the LLM client in), deterministic boundaries, and tests that run headlessly in CI. The skill is extracting notebook insights into modules with clear inputs/outputs — especially for RAG chunking, retrieval, and prompt assembly.

### Alternatives & Tradeoffs
- **Notebook-driven development**: fastest learning; poor regression control.
- **Pair notebooks + package**: research in notebooks, promote to `src/` with tests (common DS→eng path).
- **Test-first service modules**: slower initially; enables eval harnesses and refactors.
Tradeoff: delete the notebook too early and lose exploration speed; keep logic only in notebooks and you cannot CI-test prompt or retrieval changes.

### Necessity
Failure modes: unreproducible “accuracy” claims, inability to mock provider APIs, and take-home rejections for TPM-caliber structure. Syllabus explicitly flags this as the Week 1 gate.

### Industry Practice
- **Common:** export notebook to `.py` with cell debris and globals.
- **Senior:** thin CLI/HTTP adapters; domain functions pure where possible; fixtures for corpus fixtures; golden files for chunking; no network in unit tests.

### Concrete Scenario
pytest good practices assume importable packages and separated tests: https://docs.pytest.org/en/latest/goodpractices.html  
Joel Grus “I Don’t Like Notebooks” (JupyterCon talk, YouTube) — cultural critique of notebooks as software artifacts: https://www.youtube.com/watch?v=7jiPeIFXb6U

### Open Questions
- How much Marimo/reactive notebook tech changes the “notebooks aren’t software” critique?
- Where should eval exploration live — notebooks, or first-class eval CLI from day one?

### Sources
- https://docs.pytest.org/en/latest/goodpractices.html
- https://www.youtube.com/watch?v=7jiPeIFXb6U
- https://jupyter.org/documentation

---

## Concept: Logging vs print debugging

### Fundamentals
`print` writes unstructured text to stdout for humans in an interactive session. **Logging** emits leveled events (`DEBUG`…`CRITICAL`) with loggers, handlers, and formatters — filterable, redirectable to files/aggregators, and safe for libraries (don’t configure root logging inside libraries). Official guidance: use `print` for ordinary CLI user output; use loggers for operational events.

### Alternatives & Tradeoffs
- **print**: zero setup; pollutes stdout in APIs; no levels; hard to silence in tests.
- **stdlib logging + dictConfig**: standard; can be verbose to configure; use `QueueHandler` for non-blocking I/O under load (see “Modern Python logging” talk).
- **structlog / JSON logs**: better for Cloud Logging / Datadog; more upfront schema discipline.
- **OpenTelemetry traces**: complementary for request spans; not a full substitute for app logs.
Tradeoff: over-logging PII from prompts/user docs vs under-logging tool failures in agents.

### Necessity
Print-debugging in Cloud Run: cannot filter severity, cannot correlate `request_id`, secrets leak into stdout scraped by log drains, and libraries fighting over stdout. Production LLM apps need structured fields: `model`, `token_usage`, `latency_ms`, `trace_id`.

### Industry Practice
- **Common:** leftover prints; `basicConfig` once; logs without correlation IDs.
- **Senior:** `logging.getLogger(__name__)`; JSON formatter in prod; redact prompts; bind request context; library code logs but does not configure; metrics/traces alongside logs (Phase 4 observability).

### Concrete Scenario
Python Logging HOWTO task table (print vs logger): https://docs.python.org/3/howto/logging.html  
YouTube — MCoding “Modern Python logging” (`dictConfig`, QueueHandler, library vs app config): https://www.youtube.com/watch?v=9L77QExPmI0

### Open Questions
- For agent traces, do span events replace many info logs, or do teams still dual-write?
- Standard schema for LLM call logs (OpenTelemetry gen-AI semantic conventions maturity)?

### Sources
- https://docs.python.org/3/howto/logging.html
- https://docs.python.org/3/library/logging.config.html
- https://www.youtube.com/watch?v=9L77QExPmI0
- https://www.structlog.org/
