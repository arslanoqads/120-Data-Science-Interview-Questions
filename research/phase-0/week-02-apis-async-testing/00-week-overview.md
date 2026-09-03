# 00 — Week overview & syllabus mapping

> Week 2 — APIs, Async, and Testing  
> Research notes (raw).

---

## Fundamentals

Week 2 turns the Week 1 package into a **HTTP service** that other systems (and interviewers) can call. The syllabus spine is: expose a FastAPI app with generated OpenAPI, call an LLM provider over async HTTP, and prove behavior with a layered pytest suite that **never needs live keys** for unit/CI runs.

The six concepts form one delivery loop:

1. **REST design** defines the public contract (resources, status codes, errors, versioning, async jobs).  
2. **FastAPI + Pydantic** implement that contract with typed request/response validation and auto-OpenAPI.  
3. **async/await** makes LLM I/O concurrency safe under one worker without blocking the event loop.  
4. **Test pyramid** decides *how many* unit vs integration vs E2E tests you write.  
5. **Mocking** replaces the LLM port so CI is fast, deterministic, and secret-free.  
6. **Contract testing** keeps consumer expectations aligned with the OpenAPI/Pact artifact as the API evolves.

Skipping any one collapses trust: a pretty OpenAPI with blocking `requests` inside `async def` still melts under load; a green mock suite with no contract gate still breaks clients on field renames.

Week 2 is the bridge from “importable RAG package” (Week 1) to “deployable API surface” that Week 3 containers and later RAG/agent weeks hang off.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Flask + hand-rolled JSON | Familiarity, minimal deps | Auto-OpenAPI, first-class typing, ASGI async story |
| FastAPI code-first (syllabus default) | Speed to OpenAPI + validation | Spec can drift if `response_model` unused |
| OpenAPI-first + codegen | Spec as source of truth | Ceremony for a solo take-home |
| Sync-only routes + threadpool | Simpler mental model | Worse concurrency for many waiting LLM calls |
| Live-key smoke tests in every PR | “Real” confidence | Flakes, cost, secret sprawl, rate limits |
| Only E2E against staging | Realism | Ice-cream cone: slow CI, weak localization |

For the flagship Deployment Copilot / RAG chatbot backend, Week 2 should prefer **FastAPI + async httpx client behind a Protocol**, OpenAPI reviewed as the product contract, pyramid tests with provider fakes, and optionally Schemathesis/Pact when a second consumer appears.

---

## Necessity

Concrete failure modes if Week 2 is skipped:

- Take-home has a notebook or CLI only — no HTTP contract for evaluators to hit.  
- Clients timeout on 30–120s LLM calls because there is no `202` job or SSE stream design.  
- Validation errors return ad-hoc `{ "error": "..." }` strings; SDKs cannot branch.  
- `async def` routes call sync OpenAI SDK → one slow completion stalls all requests on the worker.  
- CI uses a real `OPENAI_API_KEY` → flakes, spend, and “tests pass only when quota remains.”  
- Breaking OpenAPI changes ship because nothing verified consumer assumptions.

---

## Industry Practice

- **Common (self-taught AI):** single `main.py` FastAPI route, sync `openai` call, one happy-path TestClient test, Swagger left as-is.  
- **Strong:** resourceful URLs; RFC 9457-ish or consistent problem details; request/response DTOs; `response_model`; shared `httpx.AsyncClient` lifespan; `asyncio.Semaphore` around provider fan-out; `dependency_overrides` + Protocol fake; markers for unit/integration; OpenAPI artifact in CI.  
- **FDE / platform bar:** can explain idempotency for retries, when to use LRO (`202`) vs SSE, and how Pact/Schemathesis reduce cross-service E2E without claiming they replace evals.

---

## Concrete Scenario

Syllabus build task (verbatim intent): FastAPI service + OpenAPI + async LLM calls + mocked pytest suite. Interviewers hit `/docs`, send a bad body, expect `422`; send a completion request with a fake client, expect deterministic JSON; ask why the route is `async def` and how you would avoid 429 storms under fan-out.

Public anchors for the same skills:

- Microsoft Learn API design — model domain resources, not DB tables: https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design  
- FastAPI concurrency docs — when to use `async def` vs `def`: https://fastapi.tiangolo.com/async/  
- Fowler practical test pyramid — cost/shape of layers: https://martinfowler.com/articles/practical-test-pyramid.html  
- FastAPI testing dependencies — override external auth/LLM deps: https://fastapi.tiangolo.com/advanced/testing-dependencies/

---

## Open Questions

- For product LLM APIs, default to **SSE token stream**, **202 job + poll**, or both behind feature flags?  
- Should Week 2 mandate RFC 9457 problem details, or keep FastAPI’s default `{"detail": ...}` and map later?  
- When do evals become a first-class CI job vs a nightly batch (cost vs signal)?  
- OpenAPI-first vs FastAPI code-first for a single-service FDE engagement?

---

## Sources

- Syllabus PDF (uploaded): AQ AI Engineer FDE Syllabus  
- https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design  
- https://github.com/microsoft/api-guidelines  
- https://fastapi.tiangolo.com/async/  
- https://fastapi.tiangolo.com/tutorial/testing/  
- https://martinfowler.com/articles/practical-test-pyramid.html  
- https://docs.pact.io/getting_started  
