# 01 — REST API design principles

> Week 2 concept research (deep). Legal sources only.

---

## Fundamentals

### What REST is (and is not)
**REST** is an architectural *style* for networked APIs: resources identified by URIs, manipulated via uniform HTTP methods, stateless requests, and cacheable responses where appropriate. Practical “REST over HTTPS” for product APIs means:

- **Nouns in paths** (`/users/{id}`, `/jobs/{id}`), not verbs (`/getUser`).  
- **HTTP methods carry intent**: GET retrieve, POST create/action, PUT replace, PATCH partial update, DELETE remove.  
- **Status codes are part of the contract**: `200`/`201`/`204` success shapes; `4xx` client fault; `5xx` server fault.  
- **JSON bodies** as the default representation; OpenAPI documents the schema.  
- **Statelessness**: each request carries auth/context; servers don’t rely on sticky conversational memory in HTTP itself (session cookies are a pragmatic exception).

Microsoft’s REST API Guidelines and Azure data-plane guidelines treat the API as a **stable contract over the domain**, not a mirror of database tables or internal class names. Azure’s goals include: developer-friendly HTTP/JSON, SDK-friendly shapes, fault-tolerant clients via retries/idempotency/optimistic concurrency, and versionability so customer workloads never break silently.

### Error bodies: RFC 9457 Problem Details
RFC 9457 (obsoleting RFC 7807) defines **Problem Details** for HTTP APIs. Media type: `application/problem+json`. Canonical members:

| Member | Role |
|--------|------|
| `type` | URI identifying the problem *type* (primary machine key) |
| `title` | Short, stable human summary for that type |
| `status` | HTTP status for this occurrence |
| `detail` | Occurrence-specific human explanation (don’t parse for logic) |
| `instance` | URI for this occurrence (often correlation/request id) |

Extensions (e.g. `balance`, `request_id`, `errors[]`) are allowed; clients must ignore unknown members. FastAPI’s default validation error is `{"detail": [...]}` with `422` — useful, but **not** problem+json. Strong APIs either adopt RFC 9457 for operational errors or document a single envelope and stick to it.

### Idempotency
An operation is **idempotent** if repeating the same request leaves the system in the same state (and ideally same observable result). GET/PUT/DELETE are conventionally idempotent; POST often is not. Azure guidance: customers must be able to build fault-tolerant clients — retries after timeouts must not double-charge or double-create.

Patterns:

- Natural idempotency (PUT replace by id).  
- **Idempotency-Key** / OASIS Repeatable Requests headers (`Repeatability-Request-ID`, `Repeatability-First-Sent`) for POST.  
- Deduplicating on client-supplied job ids for LLM batch submissions.

### Async jobs: `202 Accepted`
When p99 latency exceeds ~1s (Azure LRO heuristic) or work is minutes-long (RAG reindex, fine-tune, multi-step agent), **don’t hold the HTTP connection**. Azure Long-Running Operations (LRO):

1. Client POSTs/PUTs to start work.  
2. Service returns **`202 Accepted`** with `Operation-Location` (status monitor URL).  
3. Client polls until terminal state (`Succeeded` / `Failed` / `Canceled`).  
4. Optionally `Retry-After` to pace polls.

LLM product APIs often combine this with **SSE/WebSocket streaming** for interactive chat (see hybrid below).

### Versioning
Breaking changes need an explicit policy. Azure data-plane: required `api-version` query parameter on every operation; customer workloads must never break due to a silent service change; adopting a new version should not require unrelated code rewrites when possible. Alternatives: URI prefix `/v1/`, media-type versioning, header versioning. Tradeoff: URI versions are discoverable; header versions are “purer” but harder to debug in browsers/logs.

### LLM API hybrid: REST resources + SSE
Chat/completion products rarely are pure CRUD:

- **REST resources**: conversations, messages, files, jobs, API keys, usage — list/get/create with normal status codes.  
- **Streaming generation**: `text/event-stream` (SSE) or WebSocket for token deltas — not a classic resource representation.  
- **Batch / eval runs**: `202` + poll.  
- **Tool/webhook callbacks**: often separate authenticated POST endpoints with idempotency.

Design the resource model first; treat streaming as a *representation* of an in-progress generation, not as an excuse for RPC-only paths.

---

## Alternatives & Tradeoffs

| Approach | Strengths | Weaknesses | When |
|----------|-----------|------------|------|
| **Pragmatic REST + OpenAPI** | Broad client support, caching, HTTP tooling | Weak for highly connected graphs | Default public LLM/product APIs |
| **RPC-style HTTP** (`/getUser`) | Familiar to some teams | Weak caching, inconsistent conventions | Internal quick scripts only |
| **GraphQL** | Flexible client queries | Auth/caching complexity; N+1 risk | Complex multi-entity UIs |
| **gRPC** | Fast service-to-service, streaming protobuf | Browser/public DX harder | Internal mesh |
| **HATEOAS-pure REST** | Discoverability ideal | Rarely shipped; client complexity | Almost never for LLM APIs |
| **URI versioning `/v1/`** | Obvious in logs/curl | URL churn; duplicate routes | Public APIs, take-homes |
| **`api-version` query** | Azure-scale compatibility story | Every call must pass it | Platform APIs |
| **Sync request until done** | Simple client | Timeouts, LB kills, poor UX for LLM | Only sub-second work |
| **`202` + poll** | Resilient to long work | More client code | Jobs, reindex, batch |
| **SSE stream** | Low TTFT for chat | Proxy buffering issues; harder tests | Interactive generation |

---

## Necessity

### Failure modes if skipped
1. **Verb paths and random status codes** → every client reinvents error handling; retries POST and create duplicates.  
2. **DB/ORM models as API schemas** → renaming a column breaks mobile apps; overexposes internals.  
3. **Ad-hoc error JSON** → SDKs cannot switch on stable `type` URIs; support scrapes `detail` strings.  
4. **No idempotency on “create completion job”** → timeout + retry = double spend on LLM tokens.  
5. **60s blocking HTTP for RAG** → gateway `504`; users refresh; thundering herd.  
6. **Unversioned breaking field rename** → silent client nulls; “works in our Postman.”  
7. **Streaming-only API with no job resource** → CI/evals can’t poll deterministically; mobile backgrounds kill sockets.

### Must-dos from cited guidance
- Microsoft Learn: design around **business entities/operations**, organize around resources, use HTTP methods correctly, return appropriate status codes, support filtering/pagination for collections.  
- Azure guidelines: don’t break customer workloads; make operations retry-safe; use `202` + LRO when async; require explicit API version.  
- RFC 9457: prefer stable `type` for branching; don’t put secrets/stack traces in `detail`.

---

## Industry Practice

### Common (weak)
- `/api/getChatResponse` POST returning `200` with `{ "data": ..., "error": null }` even on failures.  
- Stack traces or raw provider errors forwarded to clients.  
- No pagination on `/documents`; returns entire corpus.  
- OpenAPI generated once, never reviewed; `additionalProperties` chaos.  
- Chat endpoint holds connection 2 minutes with no heartbeat.

### Strong / senior
- Resource nouns; collection conventions (`limit`/`cursor` or Azure-style paging).  
- Separate **write DTOs** from **read DTOs**; never expose ORM directly.  
- Consistent errors: problem+json or documented envelope; map provider 429 → your 429/503 with `Retry-After`.  
- Idempotency keys on job creation; store request hash → response for replay window.  
- LRO for ingest/eval; SSE for interactive chat; document both in OpenAPI (`text/event-stream` where supported).  
- Compatibility policy written down (what is breaking); `api-version` or `/v1` enforced in CI route tests.  
- Microsoft api-guidelines repo used as checklist in design review: https://github.com/microsoft/api-guidelines

### RAG / LLM service application
Model at least:

- `POST /v1/queries` or `POST /v1/chat/completions` (sync short path)  
- `POST /v1/jobs/rag-ingest` → `202` + `GET /v1/jobs/{id}`  
- `GET /v1/documents?cursor=`  
- `GET /v1/conversations/{id}/messages`  
- Error types: `https://api.example.com/problems/retrieval-empty`, `.../provider-rate-limited`, `.../validation-error`

---

## Concrete Scenario

Microsoft Learn’s API design article warns against designing the API as a thin veneer over the database — when storage evolves, clients shouldn’t. Same failure in RAG: exposing `/chunks` with raw embedding vectors and pgvector column names locks clients to your index schema. Prefer `/documents/{id}` with stable public fields and keep vectors internal: https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design

Azure LRO pattern for a slow re-embed: client `POST /indexes/{name}:reindex` gets `202` + `Operation-Location: /operations/{opId}?api-version=2024-01-01`; poll until `status=Succeeded`. Mirrors how cloud SDKs expose `begin_*` pollers: https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md

RFC 9457 example shape (out-of-credit) shows `type`/`title`/`detail`/`instance` plus extensions — use the same structure for `provider_rate_limited` with `retry_after_ms`: https://www.rfc-editor.org/rfc/rfc9457.html

Stack Overflow engineering blog restates noun paths + method semantics + status codes as the consistency baseline teams actually enforce in code review: https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/

---

## Open Questions

- Should public LLM APIs standardize on OpenAI-compatible paths (`/v1/chat/completions`) for ecosystem tooling, or domain-specific resources for clarity?  
- Is problem+json worth the migration from FastAPI’s default `detail` early, or only at externalization?  
- How to represent partial streaming failures in SSE vs final problem+json on the job resource?  
- Cursor vs page-number pagination for vector search result sets that aren’t totally ordered?

---

## Sources

- https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design  
- https://learn.microsoft.com/en-us/azure/architecture/microservices/design/api-design  
- https://github.com/microsoft/api-guidelines  
- https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md  
- https://www.rfc-editor.org/rfc/rfc9457.html  
- https://datatracker.ietf.org/doc/html/rfc9457  
- https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/  
- https://azure.github.io/typespec-azure/docs/howtos/azure-core/long-running-operations/  
- https://learn.microsoft.com/en-us/rest/api/communication/repeatable-requests  
