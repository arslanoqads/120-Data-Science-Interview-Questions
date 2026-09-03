# 01 — Type hints and static typing (mypy)

> Week 1 concept research (deep). Legal sources only.

---

## Fundamentals

### What type hints are
**Type hints** (PEP 484) are annotations on parameters, returns, and variables describing expected types. They are part of the language grammar but **do not change runtime behavior** by themselves (unless you add runtime validators like Pydantic, or compile with mypyc which *does* enforce/optimize). Offline tools—**mypy**, **Pyright/basedpyright**, **Pytype**, Astral **ty**—read annotations and report inconsistencies before execution.

PEP 484 goals (priority order): static analysis, IDE support/refactoring, documentation. Gradual typing (PEP 483 ideas) allows mixing typed and untyped code via `Any`.

### What mypy does
mypy is a static type checker: it finds bugs without running the program. Gradual typing means you can annotate incrementally. Annotations behave like structured comments for the interpreter—code still runs if mypy fails (CI is what makes failures blocking).

Key constructs for production LLM services:
- `TypedDict` / Pydantic models for JSON shapes (tool args, provider payloads)
- `Protocol` for duck-typed clients (`LLMClient.complete(...)`)
- `Generic` / `TypeVar` / PEP 695 type-parameter syntax for reusable pipeline stages
- `ParamSpec` (PEP 612) for decorators that preserve signatures (retry wrappers, logging wrappers)
- `|` union syntax (3.10+) and `X | None` instead of `Optional[X]`

### Why it matters for RAG/agents
Provider responses, tool JSON, and chunk metadata are soft-typed in notebooks (`dict`). In services, a missing key or `None` where `str` was assumed becomes a production 500 or silent bad retrieval. Static types catch call-site mistakes; runtime validation catches untrusted I/O—**both** are needed.

---

## Alternatives & Tradeoffs

| Approach | Strengths | Weaknesses | When |
|----------|-----------|------------|------|
| **mypy** | Mature, gradual adoption docs, daemon, ecosystem, Dropbox-scale proven | Can be slower than Pyright; config surface large | Default CI checker for many Python backends |
| **Pyright / basedpyright / Pylance** | Fast editor feedback; good inference | Semantics differ from mypy → dual-checker pain if both gate CI | Editor; some teams use as sole CI |
| **Astral ty** | Emerging; Rust-speed narrative | Less battle history than mypy | Watch for greenfield 2026+ |
| **Runtime only (Pydantic)** | Catches malformed HTTP/LLM JSON | Misses internal call-site bugs; cost at boundary | Always for external I/O; not a mypy substitute |
| **mypyc** | Compiles annotated Python to C extensions; mypy itself ~4× faster compiled | Alpha-ish for general prod; not for every module | Hot paths after typing exists |
| **No typing** | Fastest notebook velocity | Refactor fear; take-home failure; `Any` contagion | Throwaway only |

**Strictness ladder** (from mypy docs — equivalent to `--strict` as of mypy 1.0):
1. Easy wins: `warn_unused_configs`, `warn_redundant_casts`, `warn_unused_ignores`, `strict_equality`
2. `check_untyped_defs` (strongly recommended early)
3. `disallow_any_generics`, `disallow_subclassing_any`, `disallow_untyped_decorators`
4. Gradations: `disallow_untyped_calls` → `disallow_incomplete_defs` → `disallow_untyped_defs`
5. `no_implicit_reexport`, `warn_return_any`, `extra_checks`

You can set `strict = True` and subtract flags that fight untyped libraries.

**Tradeoff:** Strict typing fights dynamic LLM JSON until schemas exist. Prefer: untyped boundary → validated into TypedDict/Pydantic → typed core.

---

## Necessity

### Failure modes if skipped
1. **Silent `Any` propagation** through retrieval → ranking → prompt assembly; bugs surface only on odd documents.  
2. **Optional/None mishandling** on provider errors (`response.choices[0]` when empty).  
3. **Refactor paralysis** when swapping OpenAI ↔ Anthropic client shapes.  
4. **CI/take-home rejection** when gates require mypy.  
5. **False confidence** from tests that never exercise type-narrowing branches.

### Official guidance (must-dos)
From mypy “existing codebase”:
- Start small (5k–50k LOC subset); get *some* mypy green in days.  
- **Pin mypy version**; same options for all devs; config in repo.  
- **CI ASAP** to prevent new untyped holes.  
- Annotate **widely imported modules first** (models, clients, utils).  
- New code must be annotated (style rule).  
- Scope `# type: ignore` / `ignore_missing_imports` **per third-party module**, never globally if avoidable.  
- Aim for `mypy --strict` as a north star.  
- Use **dmypy** daemon; remote cache at ~100k+ LOC.

---

## Industry Practice

### Common (weak)
- Occasional `str`/`list` hints; no CI.  
- `ignore_missing_imports = True` globally.  
- `# type: ignore` without error codes.  
- Editor Pyright green, CI mypy red (or vice versa)—no single source of truth.

### Strong / senior
- `pyproject.toml` `[tool.mypy]` with pinned mypy in dependency-groups.  
- Typed core: domain models, LLM port interface, chunk metadata.  
- Per-module overrides for untyped libs (`openai` stubs improving over time; still gaps).  
- `disallow_untyped_defs` on completed packages.  
- Pre-commit + CI both run mypy on **full graph** (`pass_filenames: false` pattern for pre-commit).  
- Warm CI cache; track ignore debt.  
- Spring: year to full coverage then permanent strict (`disallow_untyped_defs`); third-party ignores scoped: https://notes.crmarsh.com/using-mypy-in-production-at-spring  
- Dropbox: ~4M lines typed; coverage reports including imprecision (`Any`, untyped imports); contributed stubs to typeshed; incremental + daemon + mypyc for checker speed: https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python

### Automation aids
- **MonkeyType**, **autotyping**, **PyAnnotate** — draft annotations from traces/tests (mypy docs).  
- Collect types from tests first; production sampling needs care (reliability/perf).

### RAG chatbot Week 1 application
Type first:
- `DocumentChunk` (id, text, metadata, embedding optional)
- `LLMClient` Protocol
- FastAPI request/response models (ties to Week 2 Pydantic)
Leave provider SDK edges with scoped ignores until stubs exist.

---

## Concrete Scenario

**Dropbox (canonical industry story):** Dynamic typing at millions of LOC hurt productivity. Gradual mypy migration over years → ~4M annotated lines. Performance of the *checker* became the bottleneck → incremental checking, mypy daemon, mypyc (mypy compiled ~4×). Process: increase strictness for new code over time; eventually require annotations in new files and most existing files. PyBay 2019 talk: “mypy: Getting to Four Million Lines of Typed Python” — https://pyvideo.org/pybay-2019/mypy-getting-to-four-million-lines-of-typed-python.html (YouTube via PyVideo).

**Spring:** Strict settings maintained after complete coverage; `ParamSpec` via typing-extensions on older Python; professional-grade config aligned with Wolt’s public writeup.

**Local lesson for FDE candidates:** You will not type 4M lines—but the *playbook* (CI early, annotate hubs first, strictness ratchet, scoped ignores) is exactly how to harden a RAG service without a big-bang rewrite.

---

## Open Questions

1. **Single CI checker:** mypy vs basedpyright as sole gate—when is dual-running worth the noise?  
2. **LLM boundaries:** Is `dict[str, Any]` → Pydantic parse enough, or should TypedDict mirror every provider event?  
3. **ty (Astral):** Will it displace mypy for greenfield FastAPI apps in 2026–27?  
4. **mypyc for app code:** Worth compiling hot chunking/embedding glue, or only leave that to Rust/vector DBs?  
5. **PEP 695 adoption:** How quickly to require new type-parameter syntax in style guides on 3.12+?

---

## Excerpts / operational snippets (research aides)

### Minimal pyproject mypy starter
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = false  # relax until third parties improve
show_error_codes = true

[[tool.mypy.overrides]]
module = ["some_untyped_lib.*"]
ignore_missing_imports = true
```

### Adoption sequence (research synthesis)
1. Pin mypy; add CI job that typechecks `src/` even if many ignores.  
2. Type `models/` + `clients/`.  
3. Enable `check_untyped_defs`.  
4. Per-package `disallow_untyped_defs`.  
5. Ratify `--strict` for new packages.

---

## Sources

### Specs & official
- https://peps.python.org/pep-0484/ — Type Hints  
- https://peps.python.org/pep-0483/ — Theory of type hints / gradual typing  
- https://peps.python.org/pep-0612/ — ParamSpec  
- https://peps.python.org/pep-0695/ — Type parameter syntax  
- https://docs.python.org/3/library/typing.html  
- https://mypy.readthedocs.io/en/stable/existing_code.html  
- https://mypy.readthedocs.io/en/stable/config_file.html  
- https://mypy.readthedocs.io/en/stable/command_line.html  
- https://github.com/python/mypy  
- https://mypyc.readthedocs.io/en/latest/introduction.html  

### Industry / practice
- https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python  
- https://notes.crmarsh.com/using-mypy-in-production-at-spring  
- https://python-type-hints.com/static-analysis-tools-ci-integration/mypy-configuration-strictness/  
- https://pyvideo.org/pybay-2019/mypy-getting-to-four-million-lines-of-typed-python.html  

### YouTube / talks
- Search: “mypy Getting to Four Million Lines” PyBay 2019 (Michael Sullivan / Dropbox)  
- https://www.youtube.com/results?search_query=mypy+four+million+lines+dropbox+pybay  
