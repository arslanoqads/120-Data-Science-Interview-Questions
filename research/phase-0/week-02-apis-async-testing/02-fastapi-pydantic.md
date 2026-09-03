# 02 — FastAPI and Pydantic validation

> Week 2 concept research (deep). Legal sources only.

---

## Fundamentals

### What FastAPI contributes
**FastAPI** is an ASGI web framework that declares HTTP APIs with Python type hints. It sits on Starlette (HTTP/WebSocket) and Pydantic (validation/serialization). Declaring a route is enough to get:

1. Request parsing (path, query, headers, body).  
2. Validation before your function runs.  
3. JSON Schema + **OpenAPI** generation (`/openapi.json`, `/docs` Swagger UI, `/redoc`).  
4. Editor completion from the same annotations.

### Path / Query / Body distinction
FastAPI decides parameter sources by rules (official body tutorial):

- Name matches a path template `{item_id}` → **path**.  
- Singular simple types (`int`, `str`, `bool`, …) not in the path → **query**.  
- Pydantic `BaseModel` (or similar) → **JSON body**.  
- Explicit markers: `Path()`, `Query()`, `Body()`, `Header()`, `Cookie()` when you need constraints or to disambiguate.

Invalid input → **`422 Unprocessable Entity`** with structured `detail` locating `path` / `query` / `body`. Example: `/items/foo` against `item_id: int` fails validation instead of crashing in business logic.

### Pydantic v2
Pydantic v2 (Rust-powered `pydantic-core`) validates and serializes models. Key mental model for APIs:

- **Request models**: coerce and constrain untrusted input (`Field(ge=0)`, `max_length`, custom validators).  
- **Response models**: shape outbound JSON; exclude secrets.  
- `model_dump()` / `model_dump_json()` (v2 names; not v1 `dict()`/`json()`).  
- `model_config` (`ConfigDict`) for `extra='forbid'`, frozen models, etc.  
- Prefer **dedicated API schemas** over reusing ORM/SQLAlchemy models as request bodies.

### `response_model`
Decorating with `response_model=ItemOut` (or return annotation) tells FastAPI to:

- Filter the returned object to the response schema (prevents leaking `password_hash`).  
- Document the success response in OpenAPI.  
- Optionally exclude unset/defaults depending on parameters.

Without `response_model`, whatever you return is JSON-encoded — accidental field leakage is a common vuln class in AI demos that return full provider payloads.

### `Annotated` style
Modern FastAPI prefers:

```python
from typing import Annotated
from fastapi import Path, Query

async def read_item(
    item_id: Annotated[int, Path(ge=1)],
    q: Annotated[str | None, Query(max_length=50)] = None,
): ...
```

Benefits: default values stay true Python defaults; metadata doesn’t overload `=` with `Query(...)`. Docs explicitly recommend Annotated over the older `q: str = Query(None)` style when possible.

### OpenAPI as artifact
FastAPI builds an OpenAPI document from routes + models. That JSON is not just “pretty docs” — it is the **provider contract candidate** for Schemathesis, SDK codegen, and partner review. Treat drift (code vs published spec) as a release bug.

---

## Alternatives & Tradeoffs

| Approach | Strengths | Weaknesses | When |
|----------|-----------|------------|------|
| **FastAPI** | Typing + OpenAPI + async ASGI | Younger than Django; magic can confuse juniors | Default for new Python LLM APIs |
| **Django Ninja / Litestar / Flask+APISpec** | Ecosystem fit | Varying OpenAPI depth | Existing stack lock-in |
| **Pydantic v2** | Fast, expressive, FastAPI-native | v1→v2 migration costs | New code |
| **msgspec / attrs** | Extreme perf | Weaker FastAPI integration | Hot inner paths, not HTTP boundary |
| **One model for ORM+API** | Less typing | Overexposure, tight coupling | Avoid in production |
| **Separate In/Out DTOs** | Clear boundaries | Duplication | Strong default |
| **Code-first OpenAPI** | Fast iteration | Spec quality depends on annotations | Solo/FDE Week 2 |
| **Spec-first + codegen** | Contract discipline | Slower for prototypes | Multi-team platforms |

**Validation placement tradeoff:** API-layer Pydantic catches wire mistakes early; domain-layer validation catches business rules (`end_date > start_date`, “corpus exists”). Do both — wire schema ≠ domain invariants.

---

## Necessity

### Failure modes if skipped
1. **`item_id="foo"`** reaches DB/LLM code → `500` instead of `422`.  
2. **Unconstrained strings** (`prompt: str`) accept 10MB bodies → memory/cost bombs.  
3. **Returning ORM/provider objects** leaks API keys, system prompts, or PII in JSON.  
4. **No OpenAPI** → partners reverse-engineer; FE guesses field names; interviewers can’t explore `/docs`.  
5. **Shared mutable default models** or `extra` ignored → silent drop of typos (`topK` vs `top_k`).  
6. **Hand-rolled parsers** diverge from docs; contract tests impossible.

### Official must-dos
From FastAPI body/path docs:

- Declare bodies as Pydantic models.  
- Let the framework parse/coerce/validate before your logic.  
- Combine path + query + body in one signature; framework routes data to the right place.  
- Prefer Annotated constraints for path/query.

---

## Industry Practice

### Common (weak)
- Single `dict` body: `payload: dict`.  
- Same `Document` model for DB, embedding pipeline, and HTTP.  
- `response_model` omitted; return `provider_response.model_dump()`.  
- Business logic inside route functions with no service layer.  
- OpenAPI left with default `FastAPI` title and no version.

### Strong / senior
- Package layout: `api/routes`, `api/schemas`, `domain/`, `adapters/llm`.  
- `CreateQueryRequest` / `QueryResponse` pairs; `Field` descriptions appear in OpenAPI.  
- `response_model` + explicit status codes (`status_code=201`).  
- `Annotated` everywhere for Path/Query/Depends.  
- App metadata: `title`, `version`, `description`; tags per router.  
- Forbid extras on write models where forward-compat isn’t needed; document when extras are allowed.  
- Export `openapi.json` in CI and fail on unintentional diff (or Spectral lint).  
- Dependency-injected settings (`pydantic-settings`) for provider base URLs — not module globals.

### RAG chatbot Week 2 application
Schemas to define first:

- `ChatMessage` (`role`, `content` with `max_length`)  
- `ChatRequest` (messages, `top_k`, `temperature` bounded `0–2`)  
- `Citation` (doc_id, score, snippet)  
- `ChatResponse` (message, citations, `request_id`) — **no** raw provider payload  
- Path: `conversation_id: Annotated[UUID, Path()]`

Wire `response_model=ChatResponse` so a mistaken `return full_openai_object` cannot ship secrets.

---

## Concrete Scenario

Official FastAPI body tutorial: declare `item: Item` (Pydantic) on POST; framework reads JSON, coerces types, returns precise errors on failure; schemas feed OpenAPI automatically: https://fastapi.tiangolo.com/tutorial/body/

Path validation: non-integer path segment against `item_id: int` yields validation error rather than application exception: https://fastapi.tiangolo.com/tutorial/path-params/

Parameters reference documents Path/Query/Body and Annotated patterns: https://fastapi.tiangolo.com/reference/parameters/

Pydantic docs are the source for v2 validators, `ConfigDict`, and serialization: https://docs.pydantic.dev/

Interview demo: hit `/docs`, try `temperature: 9`, show `422` with body location — proves the boundary firewall before any LLM call.

---

## Open Questions

- How far should API models go for **structured LLM outputs** (Pydantic AI / instructor) vs keeping provider adapters separate?  
- Strict query models rejecting unknown params — better DX safety or worse forward compatibility?  
- Should `422` validation errors be mapped to RFC 9457 while keeping FastAPI’s detail list as an extension member?  
- OpenAPI 3.1 + JSON Schema overlap: generate once or maintain hand-written overlays for webhooks/SSE?

---

## Sources

- https://fastapi.tiangolo.com/tutorial/body/  
- https://fastapi.tiangolo.com/tutorial/path-params/  
- https://fastapi.tiangolo.com/tutorial/query-params/  
- https://fastapi.tiangolo.com/reference/parameters/  
- https://fastapi.tiangolo.com/tutorial/response-model/  
- https://docs.pydantic.dev/  
- https://docs.pydantic.dev/latest/concepts/models/  
