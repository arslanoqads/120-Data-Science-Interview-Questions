# Week 2 — APIs, Async, and Testing
> Phase 0 — Engineering Foundations
> Raw research notes (not textbook prose). Sources cited inline and in Sources sections.

## Concept: REST API design principles

### Fundamentals
REST is an architectural *style* for networked APIs: resources identified by URIs, manipulated via standard HTTP methods (GET/POST/PUT/PATCH/DELETE), stateless requests, and cacheable responses where appropriate. Practical REST over HTTPS uses nouns in paths (`/users/{id}`), meaningful status codes, and JSON bodies. Microsoft/Azure guidance emphasizes platform independence and loose coupling—clients shouldn’t need server internals; the API is a stable contract over the domain, not a mirror of DB tables.

### Alternatives & Tradeoffs
- **REST vs RPC-style HTTP** (`/getUser`): RPC is familiar but weaker caching/uniform interface; REST scales conventions across teams.
- **REST vs GraphQL**: GraphQL reduces over/under-fetch for complex clients; adds caching/auth complexity and a heavier runtime.
- **REST vs gRPC**: gRPC excels service-to-service with protobuf and streaming; browser/client ergonomics favor REST/JSON for public APIs.
- **HATEOAS purity vs pragmatic REST**: full hypermedia rarely shipped; most “REST” APIs are resourceful HTTP + OpenAPI.
- **Versioning**: URI (`/v1/`) vs headers—trade discoverability vs purity.

### Necessity
Inconsistent verbs-in-paths, wrong status codes, and leaking internal schemas create brittle clients, unsafe retries (non-idempotent POSTs for updates), and breaking changes when DB columns rename. Without pagination/filtering conventions, list endpoints melt under load.

### Industry Practice
**Common:** CRUD JSON endpoints with ad-hoc naming. **Strong:** noun resources; idempotent writes where retries matter; problem-details or consistent error envelopes; pagination cursor/limit; OpenAPI as source of truth; explicit compatibility policy (Azure guidelines: don’t break customer workloads). Avoid exposing raw ORM models.

### Concrete Scenario
Microsoft Learn’s API design guidance: model the *domain* as the contract; don’t mirror DB schema—refactoring storage shouldn’t force client changes: https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design. Stack Overflow’s engineering blog restates noun paths + HTTP method semantics + status codes as the consistency baseline: https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/.

### Open Questions
Is OpenAPI-first or code-first better for FastAPI teams? When should public LLM product APIs prefer async job resources (`202` + poll) over long-lived request timeouts? REST’s fit for streaming token endpoints (SSE/WebSocket) vs pure resource CRUD.

### Sources
- https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design
- https://github.com/microsoft/api-guidelines
- https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/
- https://learn.microsoft.com/en-us/azure/architecture/microservices/design/api-design

---

## Concept: FastAPI (path/query/body validation with Pydantic)

### Fundamentals
FastAPI declares HTTP APIs with Python type hints. Path params, query params, and JSON bodies are distinguished by name/type (and explicit `Path`/`Query`/`Body`). Validation runs via Pydantic before the route body executes: bad input → `422` with a structured `detail` location (`path`/`query`/`body`). Declaring a Pydantic model parameter reads JSON body; scalars become query params unless marked otherwise.

### Alternatives & Tradeoffs
- **FastAPI vs Flask/Django Ninja/Litestar**: FastAPI’s selling point is first-class typing + auto OpenAPI; Flask needs more manual schema work.
- **Pydantic v2 vs hand-rolled validators**: Pydantic is fast/expressive; ultra-hot paths sometimes use msgspec—but lose ecosystem integration.
- **Annotated metadata** (`Annotated[int, Path(ge=1)]`) vs default-arg style: Annotated is preferred modern style; clearer separation of defaults vs validation.
- **One fat model vs many small**: shared models risk overexposing fields; separate request/response DTOs cost duplication.

### Necessity
Without request validation, garbage types hit business logic (`item_id="foo"`), causing 500s or subtle corruption. FastAPI docs show `/items/foo` against `item_id: int` returning a clear validation error instead of a crash—validation is the boundary firewall.

### Industry Practice
**Common:** one Pydantic model reused for ORM and API. **Strong:** dedicated request/response schemas; `Field` constraints; `model_config` to forbid extras where appropriate; dependency-injected settings; response_model to prevent accidental field leakage; generated OpenAPI reviewed like a public contract.

### Concrete Scenario
Official FastAPI body tutorial: declare `item: Item` (Pydantic) + path + optional query; framework parses JSON, coerces types, and returns precise errors on failure: https://fastapi.tiangolo.com/tutorial/body/. Path validation example with non-int path segment: https://fastapi.tiangolo.com/tutorial/path-params/.

### Open Questions
How far to push validation in API layer vs domain layer? Pydantic AI / structured LLM outputs blurring “request model” and “model output model.” Optional strict query models rejecting unknown params—DX vs forward compatibility.

### Sources
- https://fastapi.tiangolo.com/tutorial/body/
- https://fastapi.tiangolo.com/tutorial/path-params/
- https://fastapi.tiangolo.com/reference/parameters/
- https://docs.pydantic.dev/

---

## Concept: async/await for I/O-bound LLM calls

### Fundamentals
`async`/`await` lets a single thread interleave waiting on I/O (HTTP to OpenAI/Anthropic, DB, vector DB). While one coroutine awaits a network response, the event loop runs others—raising concurrency for I/O-bound workloads without one OS thread per request. FastAPI can declare `async def` routes; under the hood it runs on an ASGI server (uvicorn). CPU-bound work still blocks the loop unless offloaded.

### Alternatives & Tradeoffs
- **async vs threads/processes**: threads OK for modest concurrency; async scales many waiting connections better; processes/GPU workers for heavy compute.
- **async def vs def in FastAPI**: sync `def` runs in a threadpool—fine for blocking SDKs; accidental blocking calls *inside* `async def` stall the whole server.
- **httpx.AsyncClient vs vendor async SDKs**: prefer native async clients; wrapping sync SDK in `async def` without `to_thread` is a footgun.
- **Fan-out patterns**: `asyncio.gather` for parallel LLM calls; need semaphores to respect rate limits.

### Necessity
Serial awaits for multi-tool or multi-doc LLM pipelines multiply latency (e.g., 5 × 800 ms = 4 s). A blocking HTTP client in the async event loop tanks tail latency for all users under load. FastAPI’s async docs stress understanding the event loop vs threadpool behavior.

### Industry Practice
**Common:** `async def` everywhere while still calling sync `requests`. **Strong:** async HTTP throughout; shared client lifecycle; timeouts/retries; bounded concurrency; sync libraries isolated via `asyncio.to_thread` or dedicated workers; load-test concurrent LLM fan-out.

### Concrete Scenario
FastAPI’s concurrency/async documentation explains when path operations should be async and how blocking code interacts with the event loop: https://fastapi.tiangolo.com/async/. For LLM gateways, the practical benchmark is concurrent in-flight requests per worker versus sequential client calls—throughput rises until rate limits/CPU bound.

### Open Questions
Should LLM SDKs standardize on async-first APIs? Structured streaming (SSE) + async cancellation semantics when clients disconnect mid-generation. GIL/free-threaded Python’s impact on mixed CPU+I/O agents.

### Sources
- https://fastapi.tiangolo.com/async/
- https://docs.python.org/3/library/asyncio.html
- https://www.python-httpx.org/async/

---

## Concept: unit vs integration vs end-to-end tests

### Fundamentals
The test pyramid (Fowler/Cohn practical articulation): many fast **unit** tests (small pieces in isolation), fewer **integration** tests (modules + real-ish adapters: DB, queue), few **end-to-end** tests (full system through UI/API). Higher layers catch more realism and more flakiness/cost. Unit tests pin logic; integration pins wiring; E2E pins critical user journeys.

### Alternatives & Tradeoffs
- **Ice cream cone anti-pattern**: too many E2E, few units—slow CI, flaky failures.
- **Testing trophy / honeycomb** (some microservice schools): more integration, fewer pure units—trade speed for confidence at boundaries.
- **Contract tests** sit beside the pyramid to replace many cross-service E2E checks.
- **In-process ASGI tests** (httpx + FastAPI app): “integration-lite”—faster than real HTTP server E2E.

### Necessity
Only E2E: hour-long pipelines, nondeterministic fails, weak defect localization. Only units with heavy mocks: green CI, broken production wiring. Skipping integration around DB/LLM adapters is a top cause of “tests pass, deploy fails.”

### Industry Practice
**Common:** mixed folder of slow tests called “unit.” **Strong:** explicit layers and markers (`@pytest.mark.integration`); unit tests dominate PR checks; integration on docker-compose services; tiny E2E smoke on staging; quarantine flaky tests; Fowler’s rule of thumb—keep the pyramid shape unless you have a deliberate alternative.

### Concrete Scenario
Martin Fowler’s “The Practical Test Pyramid” details costs of over-relying on UI E2E and how to distribute tests: https://martinfowler.com/articles/practical-test-pyramid.html. FastAPI stacks often unit-test pure functions, integration-test routes with `httpx.ASGITransport`, and reserve true E2E for deployed environments.

### Open Questions
Where do LLM evals sit—unit (deterministic parsers), integration (stubbed model), or E2E (live model)? Cost of live-model tests in CI. Microservice tax: is the pyramid still right per service or per system?

### Sources
- https://martinfowler.com/articles/practical-test-pyramid.html
- https://docs.pytest.org/en/stable/
- https://fastapi.tiangolo.com/tutorial/testing/

---

## Concept: mocking external API calls in tests

### Fundamentals
Mocks replace network/SDK calls with controlled doubles so tests don’t hit real OpenAI/Stripe/etc. pytest’s `monkeypatch` can replace `requests.get` or client methods; `unittest.mock`/`AsyncMock` similar; transport-level tools (`respx` for httpx, `responses` for requests) stub HTTP. Prefer injecting interfaces so tests pass fakes without patching globals.

### Alternatives & Tradeoffs
- **Monkeypatch/mock**: quick; brittle if patch target wrong (patch where used, not where defined).
- **Dependency injection / FastAPI `dependency_overrides`**: cleaner for app code; requires design for testability.
- **Record/replay (VCR)**: realistic payloads; cassettes go stale; secret scrubbing required.
- **Contract mock servers (Pact)**: stronger multi-service guarantees than ad-hoc stubs.
- **Autouse “no network” fixtures**: pytest docs show deleting `Session.request` to fail tests that accidentally escape.

### Necessity
Unmocked external calls: flaky CI, rate-limit bans, secret needs in CI, slow suites, and bills. Conversely, wrong mocks that always return 200 hide client bug handling for 429/5xx.

### Industry Practice
**Common:** patch `requests.get` ad hoc. **Strong:** forbid real network in unit tests; fixture-based fakes; assert request URL/headers/body; separate rare smoke tests with credentials; for async, mock async clients properly (`AsyncMock`) so awaits don’t hang.

### Concrete Scenario
pytest monkeypatch docs include a full `requests.get` mock returning a `MockResponse.json()` dict, plus an autouse fixture that removes `Session.request` to prevent accidental remote calls: https://docs.pytest.org/en/stable/how-to/monkeypatch.html.

### Open Questions
Should LLM tests use recorded fixtures or synthetic deterministic stubs? How to mock streaming token iterators cleanly? Balancing mock realism vs test speed when providers change error schemas often.

### Sources
- https://docs.pytest.org/en/stable/how-to/monkeypatch.html
- https://docs.python.org/3/library/unittest.mock.html
- https://fastapi.tiangolo.com/advanced/testing-dependencies/

---

## Concept: contract testing

### Fundamentals
Contract testing verifies that a **consumer** and **provider** share a compatible message understanding—HTTP request/response or queue messages—without deploying the full system. Pact is a leading consumer-driven tool: consumer tests generate a contract (pact file) against a mock provider; provider verification replays those interactions against the real provider. Contrasts with schema-only checks (OpenAPI) that may not reflect what consumers actually call.

### Alternatives & Tradeoffs
- **Contract vs E2E integration**: contracts are cheaper/stabler; E2E still needed for emergent behaviors.
- **Consumer-driven (Pact) vs provider-driven (OpenAPI conformance)**: CDC prevents unused provider fields from locking evolution; provider schema tests keep docs honest but don’t prove consumer usage.
- **Broker vs file exchange**: Pact Broker adds versioning/can-i-deploy; more ops overhead.
- **Bi-directional contracts**: emerging patterns combining OpenAPI + consumer tests.

### Necessity
Without contracts, microservice teams rely on brittle shared envs; independent deploys break clients (“works in our test env”). Expensive full-stack E2E becomes the only safety net and still misses uncommon consumer paths.

### Industry Practice
**Common:** manual Postman collections / informal Slack API changes. **Strong:** Pact (or similar) in CI; publish contracts per consumer version; provider verification gated on merge; “can-i-deploy” before release; message contracts for async workers. Docs stress: don’t call mock with raw httpx outside the real client code—test the actual consumer client.

### Concrete Scenario
Pact’s intro: contract tests assert integrations conform to a shared understanding; analogy—“test the smoke alarm with the test button, don’t set the house on fire”: https://docs.pact.io/getting_started. Pact Python async consumer examples show defining interactions then exercising the real async client against `pact.serve()`: https://pact-foundation.github.io/pact-python/examples/http/aiohttp_and_flask/test_consumer/.

### Open Questions
How to contract-test LLM tool schemas and MCP servers? Are OpenAPI + spectral linting “good enough” for many FDE single-service deployments? Contract testing adoption cost for small teams vs monoliths.

### Sources
- https://docs.pact.io/getting_started
- https://docs.pact.io/consumer
- https://pact-foundation.github.io/pact-python/examples/http/aiohttp_and_flask/test_consumer/
- https://docs.pact.io/getting_started/comparisons
