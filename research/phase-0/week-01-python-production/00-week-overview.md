# 00 — Week overview & syllabus mapping

> Week 1 — Python for production, not for notebooks  
> Research notes (raw).

---

## Fundamentals

Week 1 exists because hiring gates screen **software engineering discipline** before AI-specific skill. The syllabus states a “TPM/analyst wrote this” caliber of code fails take-homes even when the candidate understands LLMs. The deliverable spine is: refactor an existing RAG chatbot backend into a **proper package** with **pytest skeleton** and **CI running lint + type-check on every push**.

The six concepts form one system:

1. **Types** make contracts checkable in CI.  
2. **Layout** makes tests exercise the installed artifact.  
3. **Deps + lock** make environments reproducible.  
4. **Venvs** isolate those environments.  
5. **Testable functions** make RAG/prompt logic unit-testable without notebooks.  
6. **Logging** makes production behavior observable without `print` pollution.

Skipping any one collapses the rest (e.g., typed code in a flat layout still ships empty wheels; locked deps in a global site-packages still collide).

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Stay in notebooks + paste into Cloud Run | Speed of exploration | Reproducibility, CI, interview narrative |
| Half-refactor (`app.py` + requirements.txt) | Minimal ceremony | Packaging bugs, dep drift, weak take-home signal |
| Full Week 1 package (src + uv + mypy + pytest + logging) | Production credibility | 1–2 days of ceremony before feature work |
| Monorepo / uv workspace from day one | Scale to multiple services | Cognitive overhead for a single chatbot |

For the flagship “Deployment Copilot,” Week 1 should prefer the full package path: the living system design doc (Week 3) and eval harness (Week 10+) assume importable modules and CI gates.

---

## Necessity

Concrete failure modes if Week 1 is skipped:

- Take-home fails automated lint/type/test gates.  
- “Works on my machine” because OpenAI SDK major version differs.  
- Chunking/prompt changes cannot be regression-tested → eval claims are anecdotal.  
- Cloud Run logs are unfilterable stdout soup; incidents un-debuggable.  
- Docker `COPY` + `pip install .` fails because tests never ran against installed code.

---

## Industry Practice

- **Common (self-taught AI):** single `main.py`, `pip install openai langchain`, prints, Colab heritage.  
- **Strong:** `src/<pkg>/`, `uv.lock`, mypy/ruff in CI, pytest with mocked LLM client, structured JSON logs with `request_id`.  
- **FAANG/FDE bar signal:** can explain *why* src layout and why lockfiles matter for eval reproducibility—not just that tools exist.

---

## Concrete Scenario

Syllabus build task (verbatim intent): refactor RAG chatbot backend into package structure + pytest skeleton + CI lint + type-check. Interviewers walk commit-by-commit; Week 1 commits are the first proof that the candidate ships maintainable systems.

Related public bar: Dropbox’s productivity crisis at millions of lines of untyped Python motivated org-wide mypy adoption — the same class of problem (understandability + refactor safety) appears at small scale in LLM apps when schemas churn: https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python

---

## Open Questions

- How early should eval harness directories exist in the package (`tests/` vs `evals/`)?  
- Should Week 1 mandate Ruff (lint+format) alongside mypy, or keep scope to typing + layout + deps?  
- Devcontainer as default onboarding vs documented `uv sync` only?

---

## Sources

- Syllabus PDF (uploaded): AQ AI Engineer FDE Syllabus  
- https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python  
- https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/  
- https://docs.astral.sh/uv/  
