# Week 2 Research Corpus — APIs, Async, and Testing

> Phase 0 — Engineering Foundations  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 2 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: FastAPI service, OpenAPI, async LLM, mocked tests |
| 01 | [01-rest-api-design.md](01-rest-api-design.md) | REST principles, Microsoft/Azure guidelines, RFC 9457, idempotency, 202 jobs, versioning, LLM hybrid (REST + SSE) |
| 02 | [02-fastapi-pydantic.md](02-fastapi-pydantic.md) | FastAPI validation, Path/Query/Body, Pydantic v2, OpenAPI, response_model, Annotated |
| 03 | [03-async-await-llm-io.md](03-async-await-llm-io.md) | asyncio, FastAPI async vs def/threadpool, httpx async, blocking pitfalls, semaphores |
| 04 | [04-test-pyramid.md](04-test-pyramid.md) | Unit/integration/e2e, Fowler practical pyramid, where evals sit, ice-cream cone |
| 05 | [05-mocking-external-apis.md](05-mocking-external-apis.md) | dependency_overrides, Protocol LLMClient, TestClient vs AsyncClient, respx/httpx |
| 06 | [06-contract-testing.md](06-contract-testing.md) | Pact CDC, OpenAPI/Schemathesis provider-driven, bi-directional, FastAPI OpenAPI artifact |
| — | [99-source-map.md](99-source-map.md) | Master URL / YouTube / RFC index |

## Completeness checklist (Week 2)

- [x] All syllabus Week 2 concepts covered with 7 required fields  
- [x] Microsoft REST / Azure API design guidelines cited  
- [x] RFC 9457 `application/problem+json` covered  
- [x] Idempotency, 202 async jobs / LRO, API versioning covered  
- [x] LLM API hybrid (REST resource + SSE streaming) covered  
- [x] FastAPI + Pydantic v2 + Annotated + OpenAPI generation covered  
- [x] Async LLM I/O, httpx, threadpool vs event-loop pitfalls, semaphores covered  
- [x] Fowler practical test pyramid + ice-cream cone anti-pattern covered  
- [x] Where LLM evals sit in the pyramid documented  
- [x] Mocking: dependency_overrides, Protocol ports, TestClient vs ASGITransport, respx  
- [x] Never live provider keys in unit tests stated with practice  
- [x] Pact CDC + Schemathesis/OpenAPI provider-driven + bi-directional covered  
- [x] FastAPI OpenAPI as publishable contract artifact covered  
- [x] YouTube / conference talk citations in source map  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 2)

Ship a **FastAPI service** with OpenAPI docs, async LLM client calls, and a **pytest suite that mocks the provider** — no live API keys in unit/CI tests. This corpus makes every design choice (status codes, validation boundary, async shape, test layers, contracts) explainable with citations.
