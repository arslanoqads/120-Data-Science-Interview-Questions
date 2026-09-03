# 99 — Week 2 master source map

> Consolidated index of RFCs, docs, blogs, talks. Legal sources only.

---

## RFCs / standards

| Spec | Topic | URL |
|------|-------|-----|
| RFC 9457 | Problem Details for HTTP APIs (`application/problem+json`) | https://www.rfc-editor.org/rfc/rfc9457.html |
| RFC 9457 (tracker) | Datatracker entry | https://datatracker.ietf.org/doc/html/rfc9457 |
| RFC 7807 | Predecessor (obsolete) — historical only | https://www.rfc-editor.org/rfc/rfc7807.html |
| OASIS Repeatable Requests | Idempotent POST headers | https://docs.oasis-open.org/odata/repeatable-requests/v1.0/repeatable-requests-v1.0.html |
| OpenAPI Specification | Provider schema standard | https://spec.openapis.org/oas/latest.html |

---

## Microsoft / Azure API design

- Microsoft Learn — API design best practices: https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design  
- Microsoft Learn — Microservice API design: https://learn.microsoft.com/en-us/azure/architecture/microservices/design/api-design  
- Microsoft REST API Guidelines (repo): https://github.com/microsoft/api-guidelines  
- Azure data-plane guidelines (vNext): https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md  
- Azure TypeSpec — Long-running operations: https://azure.github.io/typespec-azure/docs/howtos/azure-core/long-running-operations/  
- Azure SDK general design (api-version, LRO pollers): https://azure.github.io/azure-sdk/general_design.html  
- ACS repeatable requests (headers in practice): https://learn.microsoft.com/en-us/rest/api/communication/repeatable-requests  

---

## FastAPI / Pydantic / Starlette

- FastAPI async / concurrency: https://fastapi.tiangolo.com/async/  
- FastAPI request body: https://fastapi.tiangolo.com/tutorial/body/  
- FastAPI path params: https://fastapi.tiangolo.com/tutorial/path-params/  
- FastAPI query params: https://fastapi.tiangolo.com/tutorial/query-params/  
- FastAPI response model: https://fastapi.tiangolo.com/tutorial/response-model/  
- FastAPI parameters reference: https://fastapi.tiangolo.com/reference/parameters/  
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/  
- FastAPI async tests (ASGITransport): https://fastapi.tiangolo.com/advanced/async-tests/  
- FastAPI testing dependencies (overrides): https://fastapi.tiangolo.com/advanced/testing-dependencies/  
- Pydantic docs: https://docs.pydantic.dev/  
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/  

---

## Async HTTP / Python

- asyncio library: https://docs.python.org/3/library/asyncio.html  
- asyncio sync primitives (Semaphore): https://docs.python.org/3/library/asyncio-sync.html  
- HTTPX async: https://www.python-httpx.org/async/  
- HTTPX transports / ASGI: https://www.python-httpx.org/advanced/transports/  
- respx (httpx mock): https://lundberg.github.io/respx/  

---

## Testing pyramid / pytest

- Ham Vocke / Martin Fowler — The Practical Test Pyramid: https://martinfowler.com/articles/practical-test-pyramid.html  
- pytest: https://docs.pytest.org/en/stable/  
- pytest monkeypatch: https://docs.pytest.org/en/stable/how-to/monkeypatch.html  
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html  

---

## Contract testing

- Pact — introduction / getting started: https://docs.pact.io/getting_started  
- Pact — consumer docs: https://docs.pact.io/consumer  
- Pact — comparisons (schema vs contract): https://docs.pact.io/getting_started/comparisons  
- Pact Python examples index: https://docs.pact.io/implementation_guides/python/examples  
- Pact Python — FastAPI consumer example: https://pact-foundation.github.io/pact-python/examples/http/requests_and_fastapi/test_consumer/  
- Pact Python — FastAPI provider example: https://pact-foundation.github.io/pact-python/examples/http/requests_and_fastapi/test_provider/  
- Schemathesis docs: https://schemathesis.readthedocs.io/en/stable/  
- PactFlow — contract vs integration testing: https://pactflow.io/blog/contract-testing-vs-integration-testing/  

---

## Industry blogs / articles

- Stack Overflow — Best practices for REST API design: https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/  

---

## YouTube / conference video

| Talk / search hub | Link |
|-------------------|------|
| Sebastián Ramírez — FastAPI (official channel / talks) | https://www.youtube.com/results?search_query=sebastian+ramirez+fastapi |
| FastAPI async concurrency explained (community search) | https://www.youtube.com/results?search_query=fastapi+async+await+concurrency |
| Pact contract testing introduction series (linked from docs) | https://docs.pact.io/getting_started |
| Search hub: practical test pyramid / Mike Cohn | https://www.youtube.com/results?search_query=practical+test+pyramid+ham+vocke |
| Search hub: Schemathesis OpenAPI testing | https://www.youtube.com/results?search_query=schemathesis+openapi |
| How Pact works (animated explainer linked from Pact docs) | https://docs.pact.io/getting_started |

---

## GitHub

- microsoft/api-guidelines: https://github.com/microsoft/api-guidelines  
- fastapi/fastapi: https://github.com/fastapi/fastapi  
- encode/httpx: https://github.com/encode/httpx  
- pact-foundation/pact-python: https://github.com/pact-foundation/pact-python  
- schemathesis/schemathesis: https://github.com/schemathesis/schemathesis  

---

## Syllabus build reminder

Ship a **FastAPI** service with **OpenAPI**, **async** LLM I/O, and **pytest** that **mocks** the provider (no live keys in unit/CI). Optional stretch: export `openapi.json` + Schemathesis; add Pact when a second consumer appears. This corpus exists to make every Week 2 design choice **explainable with citations**.
