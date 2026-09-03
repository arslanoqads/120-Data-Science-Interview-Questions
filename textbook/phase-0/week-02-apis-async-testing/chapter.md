# Chapter 2 — APIs, Async, and Testing Discipline

> **Phase 0 — Engineering Foundations**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-0/week-02-apis-async-testing/`  
> **Syllabus Build:** Rebuild the chatbot backend as a FastAPI service with a documented OpenAPI schema, async LLM calls, and a pytest suite that mocks the model provider (no live API keys in unit/CI tests).

---

## Chapter framing

Week 1 left you with an installable package. Week 2 turns that package into an **HTTP surface** other systems—and interviewers—can call. Hiring screens for AI Engineer and Forward Deployed Engineer roles often open `/docs`, send a bad body, expect a clean `422`, then ask why the chat route is `async def` and how CI stays green without an `OPENAI_API_KEY`.

The six ideas below are one delivery loop: REST design sets the public contract; FastAPI and Pydantic implement it with typed validation and auto-OpenAPI; async/await keeps I/O-bound LLM waits concurrent without blocking the event loop; the test pyramid decides how many unit vs integration vs end-to-end checks you write; mocking replaces the provider so CI is fast, deterministic, and secret-free; contract testing keeps consumer expectations aligned with the OpenAPI (or Pact) artifact as the API evolves.

Skip any one and trust collapses: polished Swagger with blocking `requests` inside `async def` still melts under load; a green mock suite with no contract gate still breaks clients on a field rename. Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) being exposed as an HTTP API for the first time.

---

### REST API design principles

* **Fundamentals:**  
  **REST** is an architectural *style* for networked APIs: resources identified by URIs, manipulated with uniform HTTP methods, stateless requests, and cacheable responses where that makes sense. In product practice over HTTPS that means **nouns in paths** (`/users/{id}`, `/jobs/{id}`), not verbs (`/getUser`); **methods that carry intent** (GET retrieve, POST create or trigger, PUT replace, PATCH partial update, DELETE remove); **status codes as part of the contract** (`200`/`201`/`204` for success shapes, `4xx` for client fault, `5xx` for server fault); JSON as the default representation documented in OpenAPI; and **statelessness**—each request carries auth and context so the server does not rely on sticky conversational memory in HTTP itself.

  Industry guidelines (Microsoft REST / Azure data-plane style) treat the API as a **stable contract over the domain**, not a mirror of database tables or internal class names. Goals include developer-friendly HTTP/JSON, SDK-friendly shapes, fault-tolerant clients via retries and idempotency, and versionability so customer workloads do not break silently.

  **Error bodies:** RFC 9457 defines **Problem Details** (`application/problem+json`) with canonical members `type` (URI identifying the problem type—the primary machine key), `title`, `status`, `detail` (occurrence-specific; do not parse for control flow), and `instance`. Extensions are allowed; clients must ignore unknown members. FastAPI’s default validation error is `{"detail": [...]}` with `422`—useful, but not problem+json. Strong APIs either adopt RFC 9457 for operational errors or document one envelope and stick to it.

  **Idempotency:** repeating the same request leaves the system in the same state (and ideally the same observable result). GET/PUT/DELETE are conventionally idempotent; POST often is not. Patterns include natural idempotency (PUT replace by id), **Idempotency-Key** / repeatable-request headers for POST, and deduplicating on client-supplied job ids for LLM batch submissions—so a timeout plus retry does not double-spend tokens.

  **Long work:** when latency is long (Azure’s long-running-operation heuristic points at roughly p99 above ~1s, or minutes for reindex/fine-tune/agent runs), do not hold the HTTP connection. Pattern: client starts work → service returns **`202 Accepted`** with an operation/status URL → client polls until a terminal state; optionally use `Retry-After`. Interactive chat often pairs this with **SSE** (`text/event-stream`) or WebSocket for token deltas. Design **resources first** (conversations, messages, documents, jobs); treat streaming as a representation of in-progress generation, not an excuse for RPC-only paths.

  **Versioning:** breaking changes need an explicit policy—URI prefix `/v1/`, required `api-version` query parameter (Azure-style), media-type, or header versioning. URI versions are obvious in logs; header versions are harder to debug in browsers.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Pragmatic REST + OpenAPI | Broad client support, HTTP tooling, caching | Weaker for highly connected graphs | Default public LLM/product APIs |
  | RPC-style HTTP (`/getUser`) | Familiar to some teams | Weak caching; inconsistent conventions | Internal scripts only |
  | GraphQL | Flexible client queries | Auth/caching complexity; N+1 risk | Complex multi-entity UIs |
  | gRPC | Fast service-to-service; streaming protobuf | Harder public/browser DX | Internal mesh |
  | HATEOAS-pure REST | Discoverability ideal | Rarely shipped; client complexity | Almost never for LLM APIs |
  | URI versioning `/v1/` | Obvious in curl/logs | URL churn; duplicate routes | Public APIs, take-homes |
  | `api-version` query | Compatibility story at platform scale | Every call must pass it | Platform APIs |
  | Sync hold-until-done | Simple client | Timeouts, LB kills, poor LLM UX | Only sub-second work |
  | `202` + poll | Resilient to long work | More client code | Jobs, reindex, batch |
  | SSE stream | Low time-to-first-token for chat | Proxy buffering; harder tests | Interactive generation |

  For Deployment Copilot, prefer **resourceful REST + OpenAPI**, with **SSE for interactive chat** and **`202` jobs** for ingest/eval—not a streaming-only surface with no pollable job resource.

* **Failure Modes:**  
  - Verb paths and random status codes force every client to reinvent error handling; retries of POST create duplicates.  
  - ORM/DB models as API schemas: renaming a column breaks mobile apps and overexposes internals (same failure as exposing raw embedding vectors and index column names on `/chunks`).  
  - Ad-hoc error JSON: SDKs cannot switch on stable `type` URIs; support scrapes `detail` strings.  
  - No idempotency on “create completion job”: timeout + retry = double LLM spend.  
  - Multi-minute blocking HTTP for RAG: gateway `504`, user refresh, thundering herd.  
  - Unversioned breaking field rename: silent client nulls that “worked in Postman.”  
  - Streaming-only API with no job resource: CI/evals cannot poll deterministically; mobile backgrounds kill sockets.

* **Average vs. Strong Engineer:**  
  **Average:** `/api/getChatResponse` POST returning `200` with `{ "data": ..., "error": null }` even on failures; stack traces or raw provider errors forwarded to clients; no pagination on `/documents`; OpenAPI generated once and never reviewed; chat holds the connection for minutes with no heartbeat.  
  **Strong:** resource nouns and collection conventions (`limit`/`cursor` or equivalent paging); separate write and read DTOs; consistent errors (problem+json or one documented envelope); map provider `429` to your `429`/`503` with `Retry-After`; idempotency keys on job creation; LRO for ingest/eval and SSE for interactive chat, both documented; a written compatibility policy with `/v1` or `api-version` enforced in route tests. For a RAG service, model at least query/chat, ingest jobs, document listing, and conversation messages—with named problem types such as retrieval-empty and provider-rate-limited.

* **Worked Example:**  
  While exposing Deployment Copilot, you refuse to ship `/getAnswer`. Instead:

  ```text
  POST /v1/chat/completions     → sync short path or SSE for interactive chat
  POST /v1/jobs/rag-ingest      → 202 + Operation-Location / GET /v1/jobs/{id}
  GET  /v1/documents?cursor=    → paginated public document fields (vectors stay internal)
  GET  /v1/conversations/{id}/messages
  ```

  A client that times out on ingest retries with the same `Idempotency-Key`; the service returns the original job rather than starting a second embed. Provider rate limits surface as a documented problem type with `retry_after_ms`, not as a dumped OpenAI error string. Interviewers hit a deliberately invalid body and see a stable client-error shape—not a `500`.

* **Apply It:**  
  1. List domain resources (conversations, messages, documents, jobs)—not DB tables—and map HTTP methods + status codes for each.  
  2. Choose `/v1/` (or `api-version`) and write one sentence on what counts as a breaking change.  
  3. Add idempotency for job-creating POSTs; store request identity → response for a replay window.  
  4. Implement ingest/reindex as `202` + poll; keep interactive chat on SSE or a short sync path.  
  5. Pick one error envelope (RFC 9457 or FastAPI `detail`) and use it consistently; never return raw provider payloads.  
  6. Document both success and error shapes so they appear in the generated OpenAPI for this week’s build.

---

### FastAPI (path/query/body validation with Pydantic)

* **Fundamentals:**  
  **FastAPI** is an ASGI web framework that declares HTTP APIs with Python type hints. It sits on Starlette (HTTP/WebSocket) and **Pydantic** (validation/serialization). Declaring a route is enough to get request parsing (path, query, headers, body), validation before your function runs, JSON Schema + **OpenAPI** generation (`/openapi.json`, `/docs`, `/redoc`), and editor completion from the same annotations.

  Parameter sources follow framework rules: a name that matches a path template `{item_id}` is **path**; a singular simple type not in the path is **query**; a Pydantic `BaseModel` (or similar) is **JSON body**. Explicit markers—`Path()`, `Query()`, `Body()`, `Header()`, `Cookie()`—add constraints or disambiguate. Invalid input yields **`422 Unprocessable Entity`** with structured `detail` locating `path` / `query` / `body` instead of crashing in business logic.

  **Pydantic v2** (Rust-powered core) validates and serializes models. Use **request models** to coerce and constrain untrusted input (`Field(ge=0)`, `max_length`, custom validators) and **response models** to shape outbound JSON and exclude secrets. Prefer v2 APIs (`model_dump` / `model_dump_json`, `ConfigDict`) and **dedicated API schemas**—do not reuse ORM models as request bodies. Decorating with **`response_model`** filters the returned object to the response schema (preventing accidental leakage of `password_hash` or full provider payloads), documents the success response in OpenAPI, and is the difference between “docs” and a trustworthy contract candidate.

  Modern style prefers **`Annotated`** for constraints so defaults stay true Python defaults:

  ```python
  from typing import Annotated
  from fastapi import Path, Query

  async def read_item(
      item_id: Annotated[int, Path(ge=1)],
      q: Annotated[str | None, Query(max_length=50)] = None,
  ): ...
  ```

  Wire-schema validation at the API layer catches malformed HTTP early; domain-layer rules (`end_date > start_date`, “corpus exists”) still belong in the domain. Both layers matter.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | FastAPI | Typing + OpenAPI + async ASGI | Magic can confuse juniors | Default for new Python LLM APIs |
  | Django Ninja / Litestar / Flask+APISpec | Ecosystem fit | Varying OpenAPI depth | Existing stack lock-in |
  | Pydantic v2 | Fast, expressive, FastAPI-native | v1→v2 migration costs | New code |
  | msgspec / attrs at the HTTP edge | Extreme perf | Weaker FastAPI integration | Hot inner paths, not the wire boundary |
  | One model for ORM + API | Less typing | Overexposure, tight coupling | Avoid in production |
  | Separate In/Out DTOs | Clear boundaries | Some duplication | Strong default |
  | Code-first OpenAPI | Fast iteration | Spec quality depends on annotations | Solo/FDE Week 2 |
  | Spec-first + codegen | Contract discipline | Ceremony for a take-home | Multi-team platforms |

  The syllabus selects **FastAPI code-first with Pydantic v2 and `response_model`**: speed to OpenAPI and validation for the rebuild, with the caveat that unused `response_model` lets the published spec drift from reality.

* **Failure Modes:**  
  - Path/query coercion never runs: `"foo"` reaches DB/LLM code as a `500` instead of `422`.  
  - Unconstrained `prompt: str` accepts multi-megabyte bodies → memory and cost bombs.  
  - Returning ORM or provider objects leaks API keys, system prompts, or PII.  
  - No OpenAPI (or empty schemas): partners reverse-engineer; frontends guess field names; interviewers cannot explore `/docs`.  
  - `extra` ignored or loose defaults: typos like `topK` vs `top_k` silently drop.  
  - Hand-rolled parsers diverge from docs; contract tests become impossible.

* **Average vs. Strong Engineer:**  
  **Average:** `payload: dict`; one `Document` model for DB, embeddings, and HTTP; `response_model` omitted and `return provider_response.model_dump()`; business logic jammed into route functions; default FastAPI title and no version in metadata.  
  **Strong:** `api/routes`, `api/schemas`, `domain/`, `adapters/llm`; `CreateQueryRequest` / `QueryResponse` pairs with `Field` descriptions that appear in OpenAPI; `response_model` plus explicit status codes; `Annotated` for Path/Query/Depends; app `title`/`version`/`description` and router tags; forbid extras on write models where forward-compat is not needed; export `openapi.json` in CI (and optionally lint it); inject settings via dependency injection rather than module globals.

* **Worked Example:**  
  For Deployment Copilot’s chat endpoint you define schemas first:

  ```python
  # src/deployment_copilot/api/schemas/chat.py
  from typing import Annotated, Literal
  from uuid import UUID
  from pydantic import BaseModel, Field


  class ChatMessage(BaseModel):
      role: Literal["user", "assistant", "system"]
      content: str = Field(..., max_length=32_000)


  class ChatRequest(BaseModel):
      messages: list[ChatMessage]
      top_k: Annotated[int, Field(ge=1, le=20)] = 5
      temperature: Annotated[float, Field(ge=0, le=2)] = 0.2


  class Citation(BaseModel):
      doc_id: str
      score: float
      snippet: str


  class ChatResponse(BaseModel):
      message: ChatMessage
      citations: list[Citation]
      request_id: str
  ```

  The route uses `response_model=ChatResponse` and `conversation_id: Annotated[UUID, Path()]`. Hitting `/docs` with `temperature: 9` yields `422` with a body location—proving the boundary firewall **before** any LLM call. A mistaken `return full_openai_object` cannot ship secrets through the documented response shape.

* **Apply It:**  
  1. Add FastAPI app metadata (`title`, `version`, `description`) and mount routers under `/v1`.  
  2. Define In/Out Pydantic models for chat (and jobs); never accept bare `dict` bodies.  
  3. Constrain path/query/body with `Annotated` + `Field` (`max_length`, bounds on `temperature`/`top_k`).  
  4. Set `response_model` on every success path that returns JSON.  
  5. Confirm `/docs` and `/openapi.json` reflect those models; fix any route that serializes provider dumps.  
  6. Export OpenAPI in CI so later contract checks have an artifact (see contract-testing section).

---

### async/await and why it matters for I/O-bound LLM calls

* **Fundamentals:**  
  **`async`/`await`** lets a single thread **interleave waiting on I/O** (HTTP to a model provider, database, vector store, object storage). While one coroutine awaits a network response, the event loop runs others. That raises concurrency for **I/O-bound** workloads without one OS thread per in-flight request. It is **not** free parallelism for CPU-bound work (large embedding batches, heavy tokenization)—CPU work still blocks the loop unless offloaded to threads, processes, or workers.

  Core asyncio ideas: an **event loop** schedules ready coroutines and parks those awaiting I/O; an **`async def`** returns a coroutine object driven by `await`; **tasks** (`asyncio.create_task`, `asyncio.gather`) run concurrent work; **cancellation** should stop in-flight generation when a client disconnects (especially for streaming).

  FastAPI’s concurrency model:

  | Route style | Use when | Runtime behavior |
  |-------------|----------|------------------|
  | `async def` | You `await` async libraries (httpx, asyncpg, …) | Runs on the event loop |
  | `def` | Blocking/sync libraries | FastAPI runs it in a **threadpool** |
  | Mix per route | Per-route best choice | Supported |

  **Critical footgun:** declaring `async def` and then calling blocking `requests.get` or a sync SDK `OpenAI().chat.completions.create(...)` **blocks the entire event loop**—every other request on that worker stalls. Prefer native async clients (`httpx.AsyncClient`, async SDK methods), a sync `def` route (threadpool), or `await asyncio.to_thread(...)` for occasional sync calls. If you are unsure and not awaiting anything, prefer normal `def`.

  **HTTPX** `AsyncClient` is the usual async HTTP client. Do **not** create a new client per request in a hot path—share one via app lifespan for connection pooling; stream with `client.stream` + async iterators for SSE proxy patterns. **Semaphores** bound in-flight provider calls: unbounded `gather` over hundreds of docs produces `429` storms, retry amplification, and ban risk. Semaphores are **per process**—multiply by worker count when sizing. Also set HTTP timeouts, jittered retries on `429`, and metrics for in-flight calls.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | async httpx + async routes | High concurrency while waiting on LLM | Must avoid blocking calls | Default Week 2 LLM gateway |
  | Sync `def` + sync SDK | Simple; threadpool isolation | Threadpool exhaustion under load | Wrapping stubborn sync libs |
  | Threads only (no async) | Easy mental model | Worse scaling for many idle sockets | Low-QPS internal tools |
  | Process/GPU workers | True parallelism for CPU/GPU | Ops complexity | Embeddings, local models |
  | Unbounded `gather` | Apparent max throughput | Rate-limit disasters | Never in production |
  | Semaphore / queue | Protects provider and spend | Adds latency under burst | Always for fan-out |
  | Per-request `AsyncClient` | Local reasoning | No pooling; TLS/FD pressure | Avoid |
  | App-lifespan shared client | Pooling, one config | Lifecycle discipline | Strong default |

* **Failure Modes:**  
  - Serial awaits in multi-doc RAG: five × 800 ms becomes ~4 s user-visible latency that bounded `gather` could cut.  
  - Blocking sync SDK inside `async def`: p99 for *all* users spikes when one completion is slow.  
  - No timeouts: hung provider socket holds a concurrency slot forever.  
  - No semaphore: burst fans out hundreds of completions → `429` → naive retries → outage.  
  - New client per request: handshake tax and file-descriptor pressure.  
  - Ignoring cancellation: disconnected clients keep burning tokens.

* **Average vs. Strong Engineer:**  
  **Average:** `async def` everywhere plus `import requests`; a global `AsyncClient` never closed; `await gather(*[llm(c) for c in chunks])` with no limit; default or missing timeouts; streaming generators that never close the upstream response.  
  **Strong:** lifespan creates `AsyncClient`, attaches it to app state, and `aclose`s on shutdown; port interface `LLMClient` with `async def complete` / `async def stream`; semaphore (or token bucket) aligned to provider quotas; structured retries only on idempotent operations; metrics for in-flight LLM calls, queue wait, provider latency, and `429` count; load-tested fan-out before claiming “async makes us fast.” For sync-only SDKs: isolate with `to_thread` or a worker service—do not pretend they are async.

* **Worked Example:**  
  Deployment Copilot’s chat route is `async def` because it awaits the LLM port. On startup:

  ```python
  # lifespan sketch
  async with httpx.AsyncClient(timeout=30.0) as http:
      app.state.http = http
      app.state.llm_sem = asyncio.Semaphore(8)
      yield
  ```

  The adapter does `async with sem: return await client.post(...)`. A multi-query retrieval step uses `asyncio.gather` over a **bounded** set of prompts, not unbounded fan-out. In an interview demo, fifty concurrent clients each waiting ~1 s on mocked async I/O overlap on one uvicorn worker; the same load with `time.sleep` inside `async def` serializes—and that contrast is the point of the week’s async story.

* **Apply It:**  
  1. Make LLM-calling routes `async def` only if they truly `await` async I/O.  
  2. Put provider HTTP behind `httpx.AsyncClient` created in lifespan; never per-request clients.  
  3. Wrap provider fan-out in `asyncio.Semaphore` sized to RPM/TPM reality × worker count.  
  4. Set explicit timeouts; handle `429` with backoff—not blind retry loops.  
  5. If a sync SDK is unavoidable, use `def` routes or `asyncio.to_thread`—never block the loop.  
  6. Add a quick concurrency smoke (even with a fake sleep) so regressions to blocking calls are visible.

---

### Unit vs integration vs end-to-end tests

* **Fundamentals:**  
  The **practical test pyramid** (Mike Cohn’s idea; Ham Vocke’s articulation on martinfowler.com is the version teams cite) says: write tests at **different granularities**, and the higher you go, the **fewer** tests you should have—because cost, speed, and flakiness rise with the stack.

  | Layer | What it proves | Typical traits |
  |-------|----------------|----------------|
  | **Unit** | A small piece of logic in isolation | Milliseconds; no network; fakes/mocks |
  | **Integration** | Modules work with real-ish adapters (DB, filesystem, HTTP against a stub) | Slower; fewer; may use containers |
  | **End-to-end (E2E)** | Critical journeys through the real system | Slowest; flakiest; very few |

  The pyramid is a **rule of thumb**, not dogma—but most struggling teams have the shape inverted. **Solitary** units replace neighbors with mocks (pinpoint failures; risk of mock theater). **Sociable** units keep real collaborators and mock only at boundaries (more realism; wider blast radius). For LLM apps: pure functions (chunking, prompt assembly, citation parsing) → solitary units; FastAPI route + validation + fake LLM → narrow integration.

  **Contract tests** sit beside the pyramid as a way to replace many cross-service E2E checks (see the next-but-one section). **LLM evals** are not a fourth pyramid layer—they cut across: deterministic parsers on fixture text behave like units; RAG metrics on a fixed corpus with a stubbed LLM behave like integration; live-model quality judges belong in scheduled/E2E-cost territory; OpenAPI schema conformance is contract/schema work, not a quality eval. Keep quality evals on a separate pipeline with budgets and golden sets—do not dump them into the unit job.

  The **ice-cream cone** anti-pattern inverts the pyramid: many slow UI/E2E tests, few units. CI takes hours; flakes dominate; failures do not localize. Fix by pushing logic tests downward, keeping a thin E2E smoke, and adding contracts at service boundaries.

* **The Alternatives:**  

  | Shape | What you optimize | Risk |
  |-------|-------------------|------|
  | Classic pyramid | Fast feedback, localization | May under-test wiring if integration is neglected |
  | Testing trophy / honeycomb (more integration) | Confidence at boundaries | Slower suite; needs good infra |
  | Ice-cream cone | Apparent “user realism” | Flakes, cost, fear of deploys |
  | Only mocks | Green CI | Production wiring broken |
  | Only live E2E | Realism | Cost, nondeterminism, poor DX |
  | Pyramid + contracts | Independent deploy safety | Broker/process overhead |
  | Pyramid + eval batch | Model quality signal | Must isolate from PR-critical path |

* **Failure Modes:**  
  - Only E2E: hour-long pipelines; “random” fails on provider latency; cannot tell if chunker or UI broke.  
  - Only over-mocked units: mocks return 200 forever; real `429`/`5xx` handling never tested; DI graph wrong in production.  
  - No integration around DB/vector adapters: tests pass, deploy fails on SQL/pgvector.  
  - Live LLM in the unit job: empty quota → red CI; spend spikes; secrets in CI.  
  - Calling everything “unit” with no markers → cannot run a fast PR subset.  
  - Evals blocking merge without threshold discipline → flaky judges freeze the roadmap.

* **Average vs. Strong Engineer:**  
  **Average:** `tests/test_api.py` hits real OpenAI; one folder of slow tests labeled “unit”; no pytest markers; flaky tests parked on permanent `xfail`; Selenium for logic that belongs in a function test.  
  **Strong:** explicit markers (`unit`, `integration`, `e2e`, `eval`); PR gate = unit + narrow ASGI integration with fakes; nightly = docker-compose deps + tiny staging smoke; evals in a separate workflow with pinned datasets and cost dashboards; quarantine flakes with owners. FastAPI mapping: pure helpers as units; `422` validation and route + `FakeLLM` via dependency overrides as narrow integration; Compose DB as integration; Playwright/API smoke as E2E; golden RAG with live model as eval batch.

* **Worked Example:**  
  Deployment Copilot’s CI shape for Week 2:

  ```text
  PR (<30s):  unit tests for citation formatting + prompt assembly
              + ~20 ASGI tests (TestClient / AsyncClient) with FakeLLM
  Nightly:    retrieval against Compose Postgres/vector
              + small eval sample (not merge-blocking without thresholds)
  Staging:    /health + one chat path smoke
  ```

  Asserting the same “citations non-empty” rule in unit, ASGI, and Playwright is waste—pick one layer per assertion. Markers let `pytest -m unit` stay the default local loop.

* **Apply It:**  
  1. Add pytest markers for `unit`, `integration`, `e2e`, and (if needed) `eval`.  
  2. Put pure domain helpers under unit tests with no network.  
  3. Cover routes with narrow ASGI tests and a fake LLM (see mocking section).  
  4. Keep live-provider and heavy eval work out of the default PR job.  
  5. Add at most a thin E2E/smoke path; do not build an ice-cream cone.  
  6. Document which assertions live at which layer so duplicates get deleted.

---

### Mocking external API calls in tests

* **Fundamentals:**  
  **Mocks and fakes** replace network/SDK calls with controlled doubles so tests do not hit real OpenAI, Anthropic, or similar providers. Goals: **determinism** (no provider drift mid-suite), **speed** (milliseconds vs hundreds of milliseconds), **safety** (**no live API keys** in unit/CI jobs), and the ability to force error paths (`429`, `500`, malformed JSON) that are hard to trigger live.

  Prefer **seams over patching globals**. For FastAPI LLM apps the preferred seam is:

  1. Define a **`Protocol`** port (`LLMClient` with `async def complete` / `stream`).  
  2. Inject via `Depends(get_llm_client)`.  
  3. In tests, replace with a fake using **`app.dependency_overrides`**.  
  4. Reset overrides after tests (`clear()` or `={}`) to avoid cross-test pollution.

  FastAPI documents dependency overrides so external auth/providers are not called every test—providers may charge per request and add latency. The same pattern maps 1:1 to LLM clients.

  | Client | Test style | Notes |
  |--------|------------|-------|
  | `TestClient` | Sync `def` tests | Familiar Requests-like API |
  | `httpx.AsyncClient` + `ASGITransport` | `async def` tests | Same event loop as async fixtures |

  Neither opens a real TCP socket; both exercise routing, validation, and middleware (watch lifespan: `TestClient` as a context manager runs lifespan; raw `ASGITransport` may need explicit lifespan management).

  When adapters use httpx directly, **transport-level** tools (`respx`, `pytest-httpx`) mock method/URL → response. Use `unittest.mock.AsyncMock` for async methods—plain `Mock` causes “coroutine was never awaited” or hangs. Assert on **outgoing** URL/headers/body where you care about wire format, not only return values.

  Hard syllabus rule: unit/narrow integration jobs leave `OPENAI_API_KEY` unset or set to an obvious non-secret; optionally fail loudly if real network escapes (for example monkeypatching away session request). Live keys belong only in clearly marked smoke jobs with secret-store injection—not default PR CI.

* **The Alternatives:**  

  | Technique | What you gain | What it costs | When it fits |
  |-----------|---------------|---------------|--------------|
  | `dependency_overrides` + FakeLLM | Clean; tests real routes | Requires DI design | FastAPI apps (preferred) |
  | Protocol + constructor injection | Works outside FastAPI | More plumbing | Domain services |
  | monkeypatch / `mock.patch` | Quick | Brittle “patch where used” | Legacy code |
  | respx / httpx mock | Validates HTTP wiring | Tied to URL strings | Adapter unit tests |
  | VCR/record-replay | Realistic payloads | Stale cassettes; secret scrubbing | Rare characterization |
  | Pact mock server | Contract-grade | Heavier | Multi-service CDC |
  | Live provider | Ultimate realism | Flakes, cost, secrets | Tiny smoke only |

* **Failure Modes:**  
  - Unmocked calls in CI: flakes, rate-limit bans, unexpected bills, secrets in logs.  
  - Wrong patch target: mock never hits; test silently uses the network—or always uses `.env` locally and “passes.”  
  - Over-mocking: adapter always returns 200; production cannot parse provider error envelopes.  
  - Sync `Mock` on an async method: hangs or warnings-as-errors.  
  - Overrides not cleared: later tests accidentally use FakeLLM (or the real client).  
  - Recording cassettes with `Authorization` headers committed → key leak.

* **Average vs. Strong Engineer:**  
  **Average:** collection requires `OPENAI_API_KEY`; `patch` against outdated SDK paths; one happy-path `TestClient` test; no assertion that the fake was invoked with expected messages.  
  **Strong:** `FakeLLM` with a scripted queue of responses and failure injections; fixture that sets `dependency_overrides` and clears on teardown; adapter tests with respx verifying wire format once, route tests using the Protocol fake (avoid duplicating both every time); autouse “no network” guard for `unit` markers; scrubbed fixtures; streaming tested with a fake async iterator of SSE chunks.

* **Worked Example:**  
  Syllabus bar: CI green with an **unset** provider key.

  ```python
  @pytest.fixture
  def client(fake_llm):
      app.dependency_overrides[get_llm_client] = lambda: fake_llm
      with TestClient(app) as c:
          yield c
      app.dependency_overrides.clear()


  def test_chat_ok(client, fake_llm):
      fake_llm.queue_response("Hello from fake")
      r = client.post(
          "/v1/chat/completions",
          json={"messages": [{"role": "user", "content": "hi"}]},
      )
      assert r.status_code == 200
      assert r.json()["message"]["content"] == "Hello from fake"
      assert fake_llm.calls  # prompt/messages were received


  def test_chat_validation(client):
      r = client.post("/v1/chat/completions", json={"messages": []})
      assert r.status_code == 422
  ```

  A deliberately wrong key in the environment still yields green unit tests because the fake never reads it. Separate tests inject provider `429`/`503` from the fake and assert your mapped status and error envelope.

* **Apply It:**  
  1. Define `LLMClient` Protocol and inject it with `Depends`—no direct SDK imports in routes.  
  2. Build `FakeLLM` (scripted successes + failures + optional stream chunks).  
  3. Wire `dependency_overrides` in fixtures; always clear after.  
  4. Cover `422` (validation), auth failures if present, and provider error mapping with the fake.  
  5. Optionally add respx only on the HTTP adapter—do not double-mock every layer.  
  6. Ensure the default CI job has no live provider secret and fails if network escapes.

---

### Contract testing

* **Fundamentals:**  
  **Contract testing** verifies that a **consumer** and a **provider** share a compatible understanding of messages (HTTP or queues) **without** deploying the full coupled system. The Pact metaphor: you do not set the house on fire to test the smoke alarm—you use the test button. Contracts are that button for integrations.

  **Consumer-driven contracts (CDC) with Pact** are code-first: the consumer writes a unit test against a Pact mock provider specifying expected interactions; running tests generates a **pact file** (JSON)—a contract by example, not a full schema of every possible state; the file is published (broker or file exchange); the provider **verifies** by replaying those interactions against the real provider with dependencies stubbed; optionally **can-i-deploy** gates releases. Advantage vs OpenAPI alone: only **what consumers actually use** is locked; unused provider fields can evolve. Exercise the **real consumer client code** against the mock—do not fire raw httpx outside the client under test.

  Pact distinguishes **integration contract testing** (consumer ↔ provider compatibility) from **provider contract testing** (implementation ↔ its OpenAPI doc). The latter is useful but insufficient alone—it does not prove consumers call correctly.

  **Provider-driven OpenAPI + Schemathesis:** FastAPI’s generated OpenAPI describes possible requests/responses. Schemathesis generates property-based tests from the schema, hits the running app, checks conformance, and hunts `500`s—keeping the provider honest relative to its published spec. It does not, by itself, prove any particular consumer’s assumptions.

  **Bi-directional contract testing (BDCT):** provider publishes verified OpenAPI; consumer publishes Pact expectations; a broker statically compares them. Critical caveat: if OpenAPI does not match reality, the broker approves lies—**self-verification of OpenAPI against the live app is mandatory**.

  FastAPI’s `/openapi.json` is a first-class **provider contract candidate**: export in CI, lint for style/breaking changes, feed Schemathesis, publish a versioned artifact beside images, generate SDKs when partners need them. Missing `response_model` weakens schemas and creates false confidence—pair OpenAPI export with the validation practices from the FastAPI section.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Pact CDC | Locks real consumer usage; independent deploys | Broker/process learning curve | Multi-service / multi-team |
  | OpenAPI conformance (Schemathesis) | Schema violations + fuzz bugs | Doesn’t prove consumer behavior | Any FastAPI service with a spec |
  | BDCT (Pact + OpenAPI) | Scales verification | Needs disciplined spec self-check | Platforms with many consumers |
  | Shared E2E env only | Feels “real” | Slow, flaky, contention | Legacy default to escape |
  | Manual Postman | Low ceremony | Not CI-gated; drifts | Prototypes only |
  | Wiremock stubs without contracts | Fast consumer tests | Stubs lie when provider changes | Pair with Pact or drop |
  | File-exchange pacts (no broker) | Simple for two services | Harder can-i-deploy | Week 2 learning / small teams |

  For a solo Week 2 take-home, **OpenAPI export + TestClient schema assertions + Schemathesis** may be enough. Introduce Pact when a second deployable consumer appears. Contracts **complement** unit fakes—they do not replace mocking.

* **Failure Modes:**  
  - Microservice version hell: provider renames a field; consumer discovers it in production.  
  - Only shared staging E2E: queue for the env; flaky data; teams cannot parallelize.  
  - Cosmetic OpenAPI: `/docs` shows fields the code no longer returns; Schemathesis never run.  
  - Consumer tests hit raw mock URLs instead of the real client → client bugs untested while the pact stays “green.”  
  - Provider verification without state handlers → cannot fixture “user exists”; false failures.  
  - BDCT without self-verification → broker says OK; production `500`s on undocumented enums.

* **Average vs. Strong Engineer:**  
  **Average:** Slack message “we changed the response shape”; Postman collection in Downloads; Swagger screenshot in a wiki; consumer fixtures that diverge from the provider.  
  **Strong:** Pact consumer tests in the FE/BFF repo and provider verify in the API repo; broker + `can-i-deploy` in CD; Schemathesis on PR against ASGI or ephemeral Compose; OpenAPI diff comments on breaking changes; stub downstream LLM deps during provider verification. FDE pragmatism: ship truthful OpenAPI first; add Pact when a second consumer appears. LLM-specific angles include tool/function JSON schemas between agent runtime and tools, and versioning (`/v1` or `api-version`) selected during verification.

* **Worked Example:**  
  For Deployment Copilot Week 2 you treat OpenAPI as a build artifact:

  ```text
  CI steps (provider side):
    1. Boot app with FakeLLM via dependency overrides
    2. Write openapi.json from app.openapi() (or /openapi.json)
    3. Fail PR on unintentional OpenAPI diff / Spectral lint break
    4. Optional: schemathesis run openapi.json against ASGI/TestClient base URL
  ```

  When a web BFF later consumes chat, that repo adds Pact consumer tests that exercise the real BFF client against a Pact mock; the API repo verifies those interactions with the LLM port still faked. Until that second consumer exists, Schemathesis + `response_model`-truthful OpenAPI is the contract gate for the take-home—without claiming it replaces evals or unit tests.

* **Apply It:**  
  1. Export `openapi.json` in CI from the FastAPI app; commit or publish it as an artifact.  
  2. Keep schemas truthful with `response_model` on every JSON success path.  
  3. Add at least one provider-driven check (schema assertions in pytest and/or Schemathesis).  
  4. Stub the LLM (and other downstreams) during any provider verification—never live keys.  
  5. Defer Pact/broker until a second consumer exists; use file exchange if you practice CDC early.  
  6. If you adopt BDCT later, self-verify OpenAPI against the running app before trusting the broker.

---

## Week 2 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **REST surface:** Resource nouns under `/v1/`; correct methods and status codes; idempotency on job-creating POSTs; `202` + poll for long ingest; SSE or short sync for interactive chat; one consistent error envelope.  
2. **FastAPI + Pydantic:** Path/query/body models with `Annotated` constraints; separate In/Out DTOs; `response_model` everywhere; app metadata that shows up in `/docs`.  
3. **Async LLM I/O:** `async def` routes that truly await; shared `httpx.AsyncClient` in lifespan; semaphore around provider fan-out; no blocking SDK calls on the event loop.  
4. **Pyramid:** Markers for unit / integration / e2e; PR suite stays fast; evals and live-model checks stay off the default merge gate.  
5. **Mocking:** `LLMClient` Protocol + `dependency_overrides` + `FakeLLM`; CI green with no live provider key; explicit tests for `422` and provider error mapping.  
6. **Contracts:** Export OpenAPI as an artifact; keep it honest; optional Schemathesis; introduce Pact when a second consumer appears.

When those six steps are true, Week 2 is done in the syllabus sense: Deployment Copilot is an HTTP service an interviewer can explore via OpenAPI, exercise under async load reasoning, and trust via a secret-free mocked test suite.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-0/week-02-apis-async-testing/` (`00`–`06` and the week README).  
- No section required `[NEEDS MORE RESEARCH]` for the six syllabus concepts.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.
