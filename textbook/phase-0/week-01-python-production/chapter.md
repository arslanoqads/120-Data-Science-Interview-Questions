# Chapter 1 — Python for Production, Not for Notebooks

> **Phase 0 — Engineering Foundations**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-0/week-01-python-production/`  
> **Syllabus Build:** Refactor an existing RAG chatbot backend into a proper package with a pytest skeleton and CI that runs lint + type-check on every push.

---

## Chapter framing

Hiring screens for AI Engineer and Forward Deployed Engineer roles usually check software-engineering discipline before they look at RAG architecture or agent cleverness. Notebook-shaped Python—global state, untyped dictionaries, `print` debugging, unpinned dependencies—fails take-homes even when the author understands language models.

Week 1 turns an existing chatbot backend into something a reviewer can clone, install, type-check, lint, and test without tribal knowledge. The six ideas below are one system: types make contracts checkable; layout makes tests exercise the installed artifact; dependency locks and virtual environments make installs reproducible; testable functions make logic regressable; logging makes production behavior filterable; CI makes all of that enforceable.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) being packaged for the first time.

---

### Type hints and static typing (mypy)

* **Fundamentals:**  
  **Type hints** are annotations on parameters, return values, and variables that declare expected types (standardized in PEP 484). They are part of Python’s grammar, but by themselves they do **not** change how the program runs at runtime. A separate tool—a **static type checker**—reads those annotations and reports inconsistencies *without executing the code*. The checker emphasized in this curriculum is **mypy**; editors often also run **Pyright** (or **basedpyright** / Pylance). **Gradual typing** means you may mix annotated and unannotated code: the special type `Any` means “this checker should not complain here.”

  Why this exists for LLM services: provider payloads, tool-call JSON, and chunk metadata often start life as bare `dict` values. A missing key or a `None` where a `str` was assumed becomes a 500 in production or a silent bad retrieval. Static types catch mistakes at *call sites inside your code*; **runtime validation** (for example Pydantic models at HTTP or model-output boundaries) catches untrusted *external* input. Both layers matter; neither replaces the other.

  Constructs that show up immediately in a RAG backend: `TypedDict` or Pydantic models for JSON shapes; `Protocol` for duck-typed ports such as an `LLMClient` with a `complete(...)` method; generics for reusable pipeline stages; union syntax (`X | None`) for optional values.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | mypy in CI | Mature gradual-adoption story; widely understood | Config surface; can be slower than editor checkers | Default backend gate in this syllabus |
  | Pyright / basedpyright as sole CI | Fast feedback; strong inference | Semantics can disagree with mypy if both gate PRs | Editor-first teams; some greenfield stacks |
  | Runtime validation only (Pydantic) | Catches malformed HTTP/LLM JSON | Misses internal call-site bugs | Always at untrusted boundaries—not a mypy substitute |
  | No typing | Maximum notebook speed | Refactor fear; take-home failure; `Any` contagion | Throwaway exploration only |

  The syllabus selects **mypy as the CI type gate** because Week 1’s build explicitly requires type-check on every push, and the research playbook (annotate hubs first, ratchet strictness, scoped ignores for untyped libraries) matches how production Python teams grew typing without a big-bang rewrite. Prefer: untyped or loosely typed boundary → validate into a typed model → typed core.

  Strictness is a ladder, not a binary switch: start with useful warnings and `check_untyped_defs`, then move toward `disallow_untyped_defs` / `--strict` as packages stabilize. You may set `strict = true` and subtract flags that fight unfinished third-party stubs.

* **Failure Modes:**  
  - Silent `Any` spreads through retrieve → rank → prompt assembly; bugs appear only on odd documents.  
  - Optional/`None` mishandling on empty provider responses (`choices[0]` when the list is empty).  
  - Refactor paralysis when swapping provider client shapes.  
  - Automated take-homes reject the submission when mypy is required.  
  - Tests that never exercise narrowing branches give false confidence.  
  - Global `ignore_missing_imports = True` or bare `# type: ignore` hides real errors forever.

* **Average vs. Strong Engineer:**  
  **Average:** occasional `str` / `list` hints; no CI; ignores without error codes; editor green while CI red (or the reverse)—no single source of truth.  
  **Strong:** pinned mypy in a dependency group; `[tool.mypy]` in `pyproject.toml`; typed domain models, LLM port interface, and chunk metadata first; per-module overrides for untyped libraries; `disallow_untyped_defs` on finished packages; pre-commit and CI both check the **full import graph**; ignore debt tracked and reduced. Industry playbooks at large scale (for example Dropbox’s multi-year mypy migration and Spring’s permanent strict settings after full coverage) share the same small-team pattern: CI early, hubs first, strictness ratchet, scoped ignores—not “type four million lines.”

* **Worked Example:**  
  While packaging Deployment Copilot, you introduce:

  ```python
  # src/deployment_copilot/domain/chunks.py
  from typing import Protocol, TypedDict


  class ChunkMetadata(TypedDict):
      source: str
      section: str
      page: int | None


  class DocumentChunk(TypedDict):
      id: str
      text: str
      metadata: ChunkMetadata


  class LLMClient(Protocol):
      def complete(self, prompt: str) -> str: ...
  ```

  The FastAPI (or current HTTP) layer still accepts JSON, but the first step after parsing is to build `DocumentChunk` values. Provider SDK edges that lack stubs get a **module-scoped** override in `pyproject.toml`, not a repo-wide silence. CI runs `mypy src` so a new untyped helper in `domain/` fails the PR before merge.

* **Apply It:**  
  1. Pin mypy in the project’s dev dependency group; commit the lockfile.  
  2. Add `[tool.mypy]` with `python_version` matching the project; enable `show_error_codes`.  
  3. Type `DocumentChunk` / metadata and an `LLMClient` Protocol before annotating every route.  
  4. Add a CI job that typechecks `src/` even if you temporarily allow scoped ignores.  
  5. Ban new unscoped `# type: ignore`; require an error code when an ignore is unavoidable.  
  6. After hubs are clean, turn on `check_untyped_defs`, then package-local `disallow_untyped_defs`.

---

### Project structure (src layout vs flat)

* **Fundamentals:**  
  **Flat layout** places the importable package beside `pyproject.toml` at the repo root (for example `deployment_copilot/` next to config). **Src layout** places importable code under `src/deployment_copilot/` while tests and config stay at the root.

  Python puts the **current working directory on `sys.path` first**. In a flat layout, `import deployment_copilot` during pytest often imports the **local tree**, not the **installed** distribution. Packaging mistakes—missing package data, a forgotten subpackage, an empty wheel—stay invisible until Docker or `pip install` in CI/production.

  Src layout keeps the package off the default path unless the project is installed (editable or regular). Tests then fail loudly with `ModuleNotFoundError` until `uv sync` / editable install succeeds—that failure is the signal you want. An **editable install** wires metadata and path hooks so source edits apply immediately while still going through the packaging story.

* **The Alternatives:**  

  | Pattern | Upside | Downside |
  |---------||--------|----------|
  | Flat | REPL-friendly; less ceremony | Tests can false-green; path pollution |
  | Src | Install-faithful tests; cleaner discovery | Requires install before import; slightly more ceremony |
  | Script-only (`uv init --no-package`) | Fine for one-offs | Wrong for a shippable service |
  | Monorepo packages / workspaces | Clear multi-service boundaries | Needs workspace tooling |

  The syllabus selects **src layout for the flagship package** because later weeks (containers, evals, interview walkthroughs) assume importable modules and install-faithful tests. Flat remains acceptable for true throwaway scripts—not for Deployment Copilot.

* **Failure Modes:**  
  - Empty or incomplete wheels: tests passed against cwd; production missing prompt templates or chunkers.  
  - `PYTHONPATH=.` in Docker papers over broken packaging and diverges from the local uv environment.  
  - Filename collisions (`openai.py`, careless `test_utils.py`) shadow real libraries.  
  - Reviewers open a root full of notebook debris and no package—weak interview signal.  
  - Coverage measured against the source tree while the test runner exercised a different installed artifact.

* **Average vs. Strong Engineer:**  
  **Average:** `app.py` + `utils.py` + `requirements.txt` + `test_app.py`, or flat `app/` with `PYTHONPATH` hacks.  
  **Strong:** `src/<package>/` with clear `api/`, `domain/`, `adapters/` (or equivalent); `tests/` at repo root; editable install in CI before pytest; console scripts declared in project metadata; resource files (prompts, schemas) included as package data; no reliance on cwd imports. Even Cloud Run–only apps benefit: image builds install the package, and tests fail if packaging is wrong.

* **Worked Example:**  
  Before:

  ```text
  chatbot/
    app.py
    rag.py
    requirements.txt
    scratch.ipynb
  ```

  After Week 1:

  ```text
  deployment-copilot/
    pyproject.toml
    uv.lock
    .python-version
    src/
      deployment_copilot/
        __init__.py
        domain/
        adapters/
        api/
    tests/
    .github/workflows/ci.yml
  ```

  A unit test does `from deployment_copilot.domain.chunks import DocumentChunk` only after `uv sync`. Forgetting to declare prompt templates as package data fails a test that loads them via package resources—before Cloud Run.

* **Apply It:**  
  1. Create `src/deployment_copilot/` and move backend modules under domain/adapters/api boundaries.  
  2. Configure package discovery for the `src` tree in `pyproject.toml`.  
  3. Ensure CI runs an install (for example `uv sync --frozen`) before pytest.  
  4. Delete or quarantine root-level runnable scripts that bypass the package.  
  5. Add a smoke test that imports the package and loads one packaged resource (prompt or config).

---

### Dependency management (uv / Poetry)

* **Fundamentals:**  
  A Python app depends on a **graph** of packages. Without a **lockfile**—a pinned, fully resolved set of direct and transitive versions—two machines can install different graphs. That produces “works on my machine,” flaky CI, and **eval baseline drift** when libraries under the chatbot shift silently.

  Modern projects declare metadata and direct dependencies in **`pyproject.toml`** (PEP 621). A tool then writes a lockfile. **uv** (Astral) is a fast all-in-one resolver/installer that creates environments, locks, and runs commands (`uv lock`, `uv sync`, `uv run`). **Poetry** popularized the project+lock+venv workflow and remains common in enterprises. **Dependency groups** (PEP 735) hold non-published needs such as pytest, mypy, and ruff—distinct from optional extras meant for end users.

* **The Alternatives:**  

  | Choice | Upside | Downside |
  |--------|--------|----------|
  | uv greenfield | Speed; Python version management; PEP 621; workspaces | Newer; org policy lag; uv-specific lockfile |
  | Poetry | Mature DX; known to enterprises | Slower resolve historically; extra tools often still needed |
  | pip-tools | Simple mental model | Easy to forget re-compile; split tooling |
  | Unpinned `requirements.txt` | Zero ceremony | Non-reproducible; weak security story |
  | Conda `environment.yml` | Binary-heavy science stacks | Awkward fit for pure app services |

  The syllabus highlights **uv/Poetry** and research practice for new AI services leans **uv**: one toolchain locally, in CI, and in Docker (`uv sync --frozen`), with the lockfile committed. LLM stacks churn; upgrades should arrive as PRs that re-run checks—not as silent local bumps.

* **Failure Modes:**  
  - Silent major bumps break tool-calling or JSON parsing.  
  - Security reviews cannot name installed versions.  
  - Golden evals disagree across laptops.  
  - Onboarding burns hours on “install these somehow.”  
  - Poetry locally + raw pip in Docker → environment drift.

* **Average vs. Strong Engineer:**  
  **Average:** `pip freeze > requirements.txt` once; never re-resolve; mix Poetry and pip without a single story.  
  **Strong:** one toolchain; committed lockfile; dependency groups for test/lint/type tools; `uv sync --frozen` in CI and Docker; pinned Python via `requires-python` and `.python-version`; bootstrap docs that only document `uv sync`; automated update PRs gated by tests (and later evals).

* **Worked Example:**  
  You initialize the package, add runtime libraries (HTTP, provider SDK) with `uv add`, and add mypy/ruff/pytest with a **dev dependency group**. `uv.lock` is committed. Docker and GitHub Actions both run `uv sync --frozen --no-dev` (or with only needed groups) so production images never quietly re-resolve. When someone bumps the OpenAI SDK, the lockfile diff is reviewable and CI must stay green.

* **Apply It:**  
  1. Express the project in PEP 621 `[project]` form.  
  2. Put pytest, ruff, and mypy in a dependency group—not in runtime dependencies.  
  3. Commit `uv.lock` (or Poetry’s lockfile if that is the chosen toolchain).  
  4. Make CI and Docker use frozen sync only.  
  5. Document a single bootstrap command for contributors.

---

### Virtual environments

* **Fundamentals:**  
  A **virtual environment** is an isolated directory tree with its own Python interpreter and `site-packages`. Installing project A’s library versions does not overwrite project B’s. Creation options include the stdlib (`python -m venv`), Poetry’s env management, and **uv** (which typically auto-creates `.venv`). **Activation** (`source .venv/bin/activate`) is classic; **`uv run`** executes inside the project environment without manual activation, reducing “forgot to activate” failures.

  Isolation is **not** a security sandbox, **not** a substitute for Docker production parity, and **not** cross-project sharing of installed packages (uv may cache downloaded wheels globally while still installing into per-project envs).

* **The Alternatives:**  

  | Strategy | Upside | Downside |
  |----------|--------|----------|
  | Per-project `.venv` | Clear; deletable; standard | Disk use (mitigated by caches) |
  | Conda/mamba | Native binary stacks | Heavier; mix with pip carefully |
  | Docker-only for all work | Prod parity | Slow inner loop if every change rebuilds |
  | Devcontainers | Consistent onboarding | Requires Docker for contributors |
  | Global user installs | Convenient for one forever-project | Multi-project collisions; take-home disaster |

  The syllabus expects project-local environments. A common strong pattern pairs **Python deps in a venv** with **datastores in docker-compose** (Week 3)—do not put the database *inside* the venv.

* **Failure Modes:**  
  - Wrong SDK imported from a global site-packages → mysterious tool-call bugs.  
  - System Python fights `apt`/`brew`/pyenv installs.  
  - CI cannot reproduce local failures.  
  - Stack traces reveal global paths—an interview smell.  
  - Unpinned Python (3.11 vs 3.12) drifts typing and syntax while mypy’s `python_version` disagrees.

* **Average vs. Strong Engineer:**  
  **Average:** create a venv once; never document it; accidentally commit `venv/`; develop on whatever Python Ubuntu shipped.  
  **Strong:** `.venv/` gitignored; `requires-python` + `.python-version`; bootstrap is `uv sync` only; CI creates a fresh env from the lock every job; never `sudo pip install`; optional Devcontainer later for customer-laptop variance.

* **Worked Example:**  
  A grader clones your chatbot and runs `uv sync --frozen && uv run pytest`. It fails because you developed against a globally installed pre-release provider SDK. After Week 1, the only way you run tools is `uv run ...` against `.venv` populated from the lockfile—the grader’s path matches yours.

* **Apply It:**  
  1. Ensure `.venv/` is listed in `.gitignore`.  
  2. Pin Python with `.python-version` / `uv python pin` aligned to `requires-python`.  
  3. Replace global `pip install` habits with `uv sync` + `uv run`.  
  4. Confirm CI does not reuse a dirty env across unrelated projects.  
  5. Smoke-check: `uv run python -c "import deployment_copilot"`.

---

### Writing testable functions vs notebook cells

* **Fundamentals:**  
  **Jupyter notebooks** interleave code, outputs, and narrative in JSON (`.ipynb`). Cells run in a **persistent kernel**. Execution order can diverge from top-to-bottom order, creating **hidden state**: a deleted cell can leave variables alive; reordered cells produce unreproducible results. That medium is excellent for exploration and weak as the source of truth for a production service.

  Production code needs clear inputs and outputs; **dependency injection** (pass an `LLMClient` instead of importing a global singleton); deterministic tests without network access; importable modules under `src/`; and no reliance on cell order.

  A pragmatic **promotion path**: explore interactively → extract pure functions (chunking, scoring, prompt render) → place under `src/` with pytest → keep thin adapters (HTTP, CLI) → leave notebooks (if any) as demos or analysis only.

* **The Alternatives:**  

  | Approach | Upside | Downside |
  |----------|--------|----------|
  | Notebook-only | Fast insight | Hidden state; no CI; take-home failure |
  | nbdev (notebook as source) | Export to modules; assertions as tests | Team must buy notebook-centric workflow |
  | marimo (reactive, `.py` files) | Git-friendly; less hidden state; can be pytest-able | Younger ecosystem; familiarity gap |
  | Explore in notebook, ship from package | Pragmatic | Requires discipline to promote code |
  | Package-first + eval CLI | Best regression story | Slower early exploration |

  The syllabus selects **testable functions in a package** for the flagship backend because Week 1’s build is an explicit refactor away from notebook-caliber structure. Interactive tools remain fine for exploration; they are not the ship artifact.

* **Failure Modes:**  
  - Cannot mock the LLM—logic buried in cells with live API keys.  
  - “Quality improved” claims with no unit tests on chunking edge cases.  
  - Unreadable git diffs (notebook JSON).  
  - Onboarding becomes “run all cells somehow.”  
  - Production ports copy globals and `sys.path.insert` hacks.  
  - Metrics collapse when a teammate re-runs a notebook top-to-bottom and loses hidden state (for example a deleted cell that redefined `CHUNK_SIZE`).

* **Average vs. Strong Engineer:**  
  **Average:** export a notebook to `.py` with `# In[47]:` debris and ship it.  
  **Strong:** domain layer of pure-ish functions + Protocols; adapters for HTTP/filesystem/SDKs; fixtures with messy sample docs; golden-file tests for prompt render or chunk boundaries; eval exploration may use notebooks but metric code lives in an importable package; CI forbids network in unit tests.

* **Worked Example:**  
  A notebook cell embeds retrieval and a live provider call. You extract:

  ```python
  def select_chunks(candidates: list[DocumentChunk], k: int) -> list[DocumentChunk]:
      if k < 0:
          raise ValueError("k must be non-negative")
      return candidates[:k]
  ```

  A pytest unit test covers `k=0`, `k` larger than the list, and ordering. The HTTP handler calls `select_chunks` and an injected `LLMClient`; the unit suite never opens a network socket. Week 2 will deepen mocking; Week 1 only needs the skeleton to import and run.

* **Apply It:**  
  1. Inventory backend logic still living in notebooks or monolithic scripts.  
  2. Extract at least chunking/prompt-assembly helpers into `src/.../domain/`.  
  3. Add `tests/` with a skeleton that imports the installed package.  
  4. Inject provider access behind a Protocol; do not hard-wire live calls in unit tests.  
  5. Keep notebooks (if any) out of the production install path.

---

### Logging vs print debugging

* **Fundamentals:**  
  **`print`** writes ordinary human output to stdout. **Logging** is a leveled event system: loggers, handlers, and formatters send **DEBUG / INFO / WARNING / ERROR / CRITICAL** records to one or more destinations and can be filtered. Libraries should **log but not configure**; the application configures logging once at startup.

  For services that ship to Cloud Logging, Datadog, or similar, prefer **structured logging**—often JSON—with stable fields such as `event`, `request_id`, `model`, `token_usage`, `latency_ms`, and `error_type`. Libraries like **structlog** build event dictionaries through a processor pipeline and can bridge to the standard library. Handlers that write to disk or the network can block workers; a common pattern is **QueueHandler + QueueListener** so I/O runs off the request path. Correlate logs with traces later by attaching `trace_id` / `span_id` when OpenTelemetry is introduced (Phase 4). Treat prompts and retrieved documents as sensitive: prefer metadata (token counts, chunk ids) over raw bodies in production logs.

* **The Alternatives:**  

  | Approach | Upside | Downside |
  |----------|--------|----------|
  | print | Zero setup | No levels; hard to silence in tests; pollutes library output |
  | `basicConfig` | Quick | Global; fights libraries; weak structure |
  | `dictConfig` + stdlib | Standard and powerful | Easy to misconfigure |
  | structlog | Bound context; processors | Extra dependency; must integrate cleanly |
  | Traces-only observability | Unified telemetry | Overkill as the *only* Week 1 tool; still need local console |

  The syllabus includes logging in Week 1 so the refactored service is observable without print pollution. Research does not require a single mandatory library beyond using the logging system properly; structlog is a strong option, not the only one.

* **Failure Modes:**  
  - Cloud Run/Kubernetes stdout soup cannot be filtered by severity.  
  - No `request_id` across retrieve → generate → respond.  
  - Secrets and PII scraped into aggregators.  
  - Library noise interleaved with app prints.  
  - Synchronous logging blocks workers under load.  
  - Over-logging costs money and leaks data; under-logging hides tool failures.

* **Average vs. Strong Engineer:**  
  **Average:** leftover prints; `basicConfig(level=DEBUG)`; no correlation IDs; full prompt text at INFO.  
  **Strong:** `logging.getLogger(__name__)` in modules; application-only configuration at startup; JSON in prod and human-readable console in dev; `request_id` bound in middleware (contextvars); QueueHandler when handlers are slow; redaction for secrets and prompt bodies; metrics/traces alongside logs rather than overloading logs as analytics.

* **Worked Example:**  
  Intermittent 5xx on the chatbot. With JSON logs and `request_id`, you filter failures and find they share `provider=anthropic` and `error_class=TimeoutError` after a deploy—pointing to a missing timeout budget, not “RAG is broken.” A Week 1 implementation logs `event=llm_call`, model, latency, and error class without dumping the full prompt.

* **Apply It:**  
  1. Remove diagnostic `print` calls from the backend package.  
  2. Configure logging once at process startup; use module loggers elsewhere.  
  3. Add a `request_id` (even a simple middleware/contextvar) to request-scoped logs.  
  4. Log LLM/provider outcomes with metadata fields, not raw secrets.  
  5. Ensure tests can raise the log level or capture logs without depending on stdout prints.

---

### CI: lint and type-check on every push

* **Fundamentals:**  
  **Continuous Integration (CI)** runs automated checks on every push or pull request so the main branch stays releasable. For Week 1 the minimum bar is: **lint** (style and bug-finding rules—commonly **Ruff**, which covers much of flake8/isort territory and can format) and **type-check** (mypy on `src/`). Pytest should at least **collect** via a skeleton suite; deeper API mocking arrives in Week 2. CI is the enforcement layer that turns typing, layout, and dependency discipline into team reality instead of optional local habits.

* **The Alternatives:**  

  | Lint stack | Upside | Downside |
  |------------|--------|----------|
  | Ruff | Fast; one tool for lint (+ format) | Some deep pylint-style checks absent |
  | flake8 + black + isort | Familiar | Slower; more configs |
  | pylint alone | Deep analysis | Noisy; slow |

  | Policy | Upside | Downside |
  |--------|--------|----------|
  | Fail PRs on mypy from day one | Forces the ratchet | Painful until hubs are annotated |
  | Warn-only mypy | Gentler | Coverage decays unless you tighten soon |

  The syllabus explicitly requires **lint + type-check on every push**. Research consensus for 2025–26 stacks: **Ruff + mypy together**—Ruff for file-local lint/format, mypy for cross-module types. Disable overlapping Ruff annotation rules when mypy owns typing diagnostics. Pin tool versions via the lockfile; prefer `uv run ruff` / `uv run mypy` so local and CI match.

* **Failure Modes:**  
  - Typed code regresses on the next feature branch.  
  - Interviewers clone a repo with no green checks.  
  - “Passed on my laptop” with different Ruff/mypy versions.  
  - Enabling both Ruff annotation rules and mypy strict creates duplicate noisy diagnostics.

* **Average vs. Strong Engineer:**  
  **Average:** no CI, or CI that only runs pytest without lint/types.  
  **Strong:** a quality job that syncs from the lockfile, runs `ruff check`, `ruff format --check`, `mypy src`, and `pytest`; caches downloads; required status checks on `main`; optional pre-commit hooks that mirror CI, with CI remaining source of truth; mypy pre-commit configured to check the full graph (not only changed filenames).

* **Worked Example:**  
  A PR adds an untyped helper used by retrieval. CI runs mypy and fails; the author annotates the helper and merges. Separately, the team disables Ruff’s annotation-overlap rules so PR comments don’t double-report what mypy already says. The Week 1 workflow file becomes the first commit interviewers can point to as proof the system is maintained under gates.

* **Apply It:**  
  1. Add a CI workflow on push/PR.  
  2. Install dependencies with frozen sync from the lockfile.  
  3. Run Ruff check (and format check if you adopt formatter-in-CI).  
  4. Run mypy on `src/`.  
  5. Run pytest skeleton (collect + any smoke imports).  
  6. Mark the quality job as a required check before merging to main.

---

## Week 1 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Layout:** Move the chatbot backend under `src/<package>/`; add root `tests/`.  
2. **Environment:** Pin Python; create project venv via the chosen tool (uv recommended by research practice).  
3. **Dependencies:** Declare runtime + dependency groups; commit the lockfile; frozen sync in CI.  
4. **Types:** Annotate domain hubs + `LLMClient` Protocol; configure mypy.  
5. **Testability:** Extract pure helpers; add pytest skeleton that imports the installed package.  
6. **Logging:** Replace prints with module loggers and request-scoped correlation fields.  
7. **CI:** On every push, lint (Ruff) + type-check (mypy); keep pytest collecting.

When those seven steps are true, Week 1 is done in the syllabus sense: the flagship system is a package an interviewer can walk commit-by-commit before any AI-specific deep dive.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-0/week-01-python-production/`.  
- No section required `[NEEDS MORE RESEARCH]` for the six syllabus concepts plus the CI build gate covered in research file `07`.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.
