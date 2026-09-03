# 05 — Writing testable functions vs notebook cells

> Week 1 concept research (deep). Legal sources only.

---

## Fundamentals

### Notebooks as a medium
Jupyter notebooks interleave code, outputs, and narrative in JSON (`.ipynb`). Cells execute in a **persistent kernel**. Execution order can diverge from visual top-to-bottom order → **hidden state**: deleted cells leave variables alive; reordered cells produce unreproducible results.

Joel Grus’s JupyterCon 2018 talk “I Don’t Like Notebooks” popularized this critique (also: teaching bad habits, weak modularity, poor git diffs, testing difficulty). JetBrains study cited by marimo: large fraction of GitHub notebooks not reproducible (marimo cites 36% in one study; another claim &lt;4% fully reproducible—treat magnitudes as directional, not gospel).

### Production functions
Production code needs:
- **Clear inputs/outputs** (pure-ish functions where possible)
- **Dependency injection** (pass `LLMClient`, don’t global-import a singleton)
- **Deterministic tests** without network
- **Importable modules** under `src/`
- **No reliance on cell order**

### The promotion path (DS → eng)
1. Explore in notebook / marimo.  
2. Extract pure functions (chunking, scoring, prompt render).  
3. Place under `src/`; add pytest.  
4. Thin adapters: FastAPI routes, CLI.  
5. Keep notebooks as demos/analysis only—or discard.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| Notebook-only | Fast insight | Hidden state; no CI; take-home fail |
| nbdev (notebook as source of truth) | Export to modules; git hooks strip noise; assertions as tests | Still notebook-centric workflow; team buy-in |
| marimo (reactive, `.py` files) | Git-friendly; reactive; runnable as script/app; pytest-able | Ecosystem younger than Jupyter; team familiarity |
| Pair: notebook explore + package ship | Pragmatic | Discipline required to promote code |
| Package-first + eval CLI | Best regression story | Slower early exploration |

**marimo** positions itself as solving Grus’s complaints while keeping interactive UX: stored as Python, reactive execution, no hidden state on delete, deployable as apps: https://marimo.io/blog/introducing-marimo

**nbdev** (fast.ai): `#export` cells → library modules; CI runs assertions: orthogonal goal (notebooks *are* the package source).

---

## Necessity

Syllabus Week 1 gate: TPM-caliber notebook structure fails take-homes.

Failure modes:
1. Cannot mock LLM—logic buried in cells with live keys.  
2. “Accuracy improved” with no unit tests on chunking edge cases.  
3. Git diffs unreadable (notebook JSON).  
4. Onboarding: “run all cells somehow.”  
5. Production port copies globals and `sys.path.insert(0, ...)`.

---

## Industry Practice

### Common
Export notebook to `.py` with `# In[47]:` debris; ship it.

### Senior
- Domain layer: pure functions + Protocols.  
- Adapters: HTTP, filesystem, provider SDKs.  
- Fixtures: sample messy docs (not only Wikipedia).  
- Golden file tests for prompt render / chunk boundaries.  
- Eval exploration may use notebooks **but** metrics code lives in `evals/` package.  
- CI forbids network in unit tests.

### Week 1 build mapping
Refactor chatbot backend → package; pytest skeleton that imports from installed package; mock provider at port boundary (deepens in Week 2).

---

## Concrete Scenario

- Grus talk (YouTube): https://www.youtube.com/watch?v=7jiPeIFXb6U  
- Grus speaking page (context for related reproducibility talks): https://joelgrus.com/speaking/  
- pytest good practices: https://docs.pytest.org/en/latest/goodpractices.html  
- marimo intro: https://marimo.io/blog/introducing-marimo  
- marimo vs Jupyter: https://marimo.io/features/vs-jupyter-alternative  
- marimo “Python not JSON”: https://marimo.io/blog/python-not-json  

**Scenario:** Engineer demos RAG quality in a notebook with out-of-order cells. Teammate re-runs top-to-bottom—retrieval metrics collapse. Root cause: hidden state from a deleted cell that redefined `CHUNK_SIZE`. Extraction into a typed function with a unit test prevents recurrence.

---

## Open Questions

1. For AI evals, is marimo the right interactive layer or a dedicated Streamlit/eval UI?  
2. Should curriculum ban `.ipynb` in the flagship repo, allowing only marimo/scripts?  
3. How much functional purity is realistic around stateful agent graphs (Week 13)?  
4. Databricks-style “notebooks as jobs” in enterprises—how to reconcile with package discipline?

---

## Sources

- https://www.youtube.com/watch?v=7jiPeIFXb6U  
- https://joelgrus.com/speaking/  
- https://docs.pytest.org/en/latest/goodpractices.html  
- https://jupyter.org/documentation  
- https://marimo.io/blog/introducing-marimo  
- https://marimo.io/blog/python-not-json  
- https://marimo.io/features/vs-jupyter-alternative  
- https://nbdev.fast.ai/ (nbdev docs hub)  
