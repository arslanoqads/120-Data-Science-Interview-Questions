# Week 1 Research Corpus — Python for production, not for notebooks

> Phase 0 — Engineering Foundations  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 1 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping, build task, failure modes of “notebook Python” |
| 01 | [01-type-hints-and-mypy.md](01-type-hints-and-mypy.md) | Type hints, mypy, gradual typing, CI gates |
| 02 | [02-project-structure-src-vs-flat.md](02-project-structure-src-vs-flat.md) | src layout vs flat, packaging, editable installs |
| 03 | [03-dependency-management-uv-poetry.md](03-dependency-management-uv-poetry.md) | uv, Poetry, lockfiles, PEP 621/735, workspaces |
| 04 | [04-virtual-environments.md](04-virtual-environments.md) | venv, isolation, Python version pinning |
| 05 | [05-testable-functions-vs-notebooks.md](05-testable-functions-vs-notebooks.md) | Notebooks vs modules, DI, promotion path |
| 06 | [06-logging-vs-print.md](06-logging-vs-print.md) | logging, structlog, JSON, OTel correlation |
| 07 | [07-ci-lint-typecheck.md](07-ci-lint-typecheck.md) | Ruff + mypy CI gate (syllabus build) |
| — | [99-source-map.md](99-source-map.md) | Master URL / YouTube / PEP index |

## Completeness checklist (Week 1)

- [x] All syllabus Week 1 concepts covered with 7 required fields  
- [x] Dropbox / Spring production typing case studies  
- [x] Hynek / PyPA packaging rationale  
- [x] uv official docs + PEP 735 dependency groups  
- [x] Notebook critique (Grus) + modern alternatives (marimo/nbdev)  
- [x] Logging HOWTO + structured logging + QueueHandler / OTel  
- [x] CI lint+type-check (Ruff/mypy) research for build task  
- [x] YouTube / conference talk citations  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
