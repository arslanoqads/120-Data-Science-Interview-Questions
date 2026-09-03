# 04 — Virtual environments

> Week 1 concept research (deep). Legal sources only.

---

## Fundamentals

A **virtual environment** is an isolated directory tree containing a Python interpreter and its own `site-packages`. Installing project A’s `langchain==0.2` does not overwrite project B’s `langchain==0.3`.

### Creation mechanisms
| Mechanism | Notes |
|-----------|-------|
| `python -m venv .venv` | Stdlib; baseline |
| `virtualenv` | Faster/heavier features historically |
| Poetry env management | Tied to Poetry projects |
| **uv** | Auto-creates `.venv`; `uv venv`; can install Python versions first |
| Conda/mamba | Isolates binaries/libs beyond pure Python; different solver |

### Activation vs `uv run`
Classic: `source .venv/bin/activate`. Modern: `uv run pytest` uses the project env without manual activation—reduces “forgot to activate” class of bugs.

### What isolation is *not*
- Not a security sandbox (same user permissions).  
- Not a substitute for Docker prod parity.  
- Not cross-project sharing (except uv’s global cache of *wheels*, which still installs into per-project envs).

---

## Alternatives & Tradeoffs

| Strategy | Pros | Cons |
|----------|------|------|
| Per-project `.venv` | Clear; deletable; standard | Disk use (mitigated by hardlink caches in uv) |
| Conda | Native deps (MKL, CUDA toolkits) | Heavier; solver complexity; mix with pip carefully |
| Docker-only | True parity with prod | Slow inner loop if rebuild always |
| Devcontainers | Onboarding consistency | Docker dependency for all contributors |
| Global user installs | Convenient for one project forever | Multi-project hell; take-home disaster |

**Compose pattern:** Python deps in venv; Postgres/redis/vector DB in docker-compose (Week 3). Don’t put the database *in* the venv.

---

## Necessity

Without venvs:
- Wrong `openai` SDK imported → mysterious tool-call bugs.  
- System Python polluted; `apt`/`brew` Python fights pyenv.  
- CI cannot reproduce local failures.  
- Interviewers spot global site-packages paths in stack traces.

With venvs but **unpinned Python**:
- 3.11 vs 3.12 typing/syntax drift; uv/mypy `python_version` mismatch.

---

## Industry Practice

### Common
Create venv once; never document; commit `venv/` by accident; use system Python 3.9 “because Ubuntu.”

### Senior
- `.venv/` in `.gitignore`.  
- `requires-python` + `.python-version` (uv python pin).  
- Bootstrap doc: `uv sync` only.  
- CI: fresh env every job from lock.  
- Optional: Devcontainer for FDE customer laptop variance.  
- Never `sudo pip install`.

### uv-specific
- Global cache stores downloaded wheels/sdists; envs stay project-local.  
- `uv python install 3.12` then `uv venv --python 3.12`.  
- Workspace: typically one shared `.venv` at root (see Week concept 03).

---

## Concrete Scenario

Python stdlib venv docs: https://docs.python.org/3/library/venv.html  
pip virtualenv user guide: https://pip.pypa.io/en/stable/user_guide/#virtual-environments  
uv Python versions & projects: https://docs.astral.sh/uv/concepts/projects/  
uv install Python guide (from uv docs hub): https://docs.astral.sh/uv/

**Scenario:** Candidate demos RAG bot; grader’s CI uses clean `uv sync --frozen` and fails because candidate developed against globally installed pre-release `openai`. Week 1 venv+lock prevents this.

---

## Open Questions

1. Default teaching path: Devcontainer vs bare uv for TPM→engineer curriculum?  
2. CUDA/PyTorch: uv-managed venv + system CUDA vs conda—team standard?  
3. Should Cloud Agent / CI cache `.venv` or only the download cache?

---

## Sources

- https://docs.python.org/3/library/venv.html  
- https://docs.python.org/3/tutorial/venv.html  
- https://pip.pypa.io/en/stable/user_guide/#virtual-environments  
- https://docs.astral.sh/uv/  
- https://docs.astral.sh/uv/concepts/projects/  
- https://virtualenv.pypa.io/en/latest/  
