# 04 — Unit vs integration vs end-to-end tests (test pyramid)

> Week 2 concept research (deep). Legal sources only.

---

## Fundamentals

### The practical test pyramid
Mike Cohn popularized the **test pyramid**; Ham Vocke’s “The Practical Test Pyramid” (martinfowler.com, 2018) is the modern practical articulation teams cite. Core idea:

1. Write tests at **different granularities**.  
2. The higher you go, the **fewer** tests you should have (cost, speed, flakiness).

Classic layers (bottom → top):

| Layer | What it proves | Typical traits |
|-------|----------------|----------------|
| **Unit** | A small piece of logic in isolation | ms, no network, heavy use of fakes/mocks |
| **Integration** | Modules work with “real-ish” adapters (DB, filesystem, HTTP client against stub) | slower, fewer, may use containers |
| **End-to-end (E2E)** | Critical journeys through the real system (UI or full API stack) | slowest, flakiest, very few |

Vocke stresses: the pyramid is a **rule of thumb**, not dogma — but most struggling teams have the shape inverted.

### Sociable vs solitary units
- **Solitary**: dependency neighbors replaced with mocks — pinpoint failures; risk of mock theater.  
- **Sociable**: real collaborators, mock only at boundaries — more realism; wider failure blast radius.

For LLM apps: pure functions (chunking, prompt assembly, citation parsing) → solitary units; FastAPI route + validation + fake LLM → narrow integration.

### Where contract tests sit
Fowler/Vocke place **contract tests** (e.g. Pact) beside the pyramid as a way to replace many cross-service E2E checks: consumer and provider verify a shared understanding without deploying the world. See Week 2 file `06-contract-testing.md`.

### Where LLM **evals** sit
Evals are not a fourth pyramid layer — they cut across:

| Eval style | Closest pyramid analogue | Notes |
|------------|--------------------------|-------|
| Deterministic parsers / schema checks on model output | **Unit** | Fast; no model needed if fixture text used |
| RAG component metrics on fixed corpus + stubbed LLM | **Integration** | Retrieval quality without provider spend |
| Live-model quality / trajectory judges | **E2E / scheduled batch** | Costly, nondeterministic; rarely every PR |
| Contract that response JSON matches OpenAPI | **Contract / schema** | Not an eval of *quality* |

Treat **quality evals** as a separate pipeline with budgets, golden sets, and quarantine rules — don’t dump them into the unit job.

### Ice-cream cone anti-pattern
The **ice-cream cone** (inverted pyramid): many slow UI/E2E tests, few units. Symptoms:

- CI takes hours; flakes dominate Slack.  
- Failures don’t localize (“checkout broke” — was it CSS, API, or DB?).  
- Developers stop trusting/running tests.

Fix: push logic tests downward; keep a thin E2E smoke; add contracts at service boundaries.

---

## Alternatives & Tradeoffs

| Shape | Optimizes | Risk |
|-------|-----------|------|
| **Classic pyramid** | Fast feedback, localization | May under-test wiring if integration neglected |
| **Testing trophy / honeycomb** (more integration) | Confidence at boundaries | Slower suite; needs good test infra |
| **Ice-cream cone** | Apparent “user realism” | Flakes, cost, fear of deploys |
| **Only mocks** | Green CI | Production wiring broken |
| **Only live E2E** | Realism | Cost, nondeterminism, poor DX |
| **Pyramid + contracts** | Independent deploy safety | Broker/process overhead |
| **Pyramid + eval batch** | Model quality signal | Must isolate from PR-critical path |

---

## Necessity

### Failure modes if skipped
1. **Only E2E**: hour-long pipelines; “random” fails on provider latency; can’t tell if chunker or UI broke.  
2. **Only units with over-mocks**: mocks return 200 forever; real 429/5xx handling never tested; DI graph wrong in prod.  
3. **No integration around DB/vector adapters**: tests pass, deploy fails on SQL/pgvector.  
4. **Live LLM in unit job**: quota empty → red CI; spend spikes; secrets in CI.  
5. **Calling everything “unit”**: no markers → can’t run fast subset on PR.  
6. **Evals blocking merge without thresholds discipline**: flaky judge → frozen roadmap.

### Fowler/Vocke practical reminders
- Prefer tests that give **quick, reliable** feedback in the pipeline.  
- Avoid duplicating the same assertion across all layers.  
- Write clean test code — tests are production code’s peers.  
- Use CDC/Pact to shrink cross-service E2E.

---

## Industry Practice

### Common (weak)
- `tests/test_api.py` hits real OpenAI.  
- One folder of slow tests labeled “unit.”  
- No pytest markers; entire suite runs on every commit.  
- Flaky tests ignored with `xfail` forever.  
- E2E Selenium for logic that belongs in a function test.

### Strong / senior
- Explicit layers + markers: `@pytest.mark.unit`, `integration`, `e2e`, `eval`.  
- PR gate: unit + narrow ASGI integration (httpx + app) with fakes.  
- Nightly/scheduled: integration with docker-compose deps; tiny E2E smoke on staging.  
- Evals: separate workflow, pinned dataset versions, cost dashboards.  
- Quarantine flaky tests with owners; don’t delete coverage silently.  
- Fowler’s rule of thumb: keep pyramid shape unless you have a **documented** alternative (trophy) and infra to match.

### FastAPI-specific mapping

| Test | Layer | Tooling |
|------|-------|---------|
| `format_citations()` pure function | Unit | pytest |
| Route validation `422` | Narrow integration | `TestClient` / `AsyncClient`+`ASGITransport` |
| Route + fake `LLMClient` via `dependency_overrides` | Narrow integration | FastAPI testing deps |
| App + Postgres in Compose | Integration | pytest-asyncio + real DB |
| Deployed service + FE critical path | E2E | Playwright/API smoke |
| Golden RAG set with live model | Eval batch | custom runner / CI nightly |

Docs: https://fastapi.tiangolo.com/tutorial/testing/

---

## Concrete Scenario

Ham Vocke / Martin Fowler “The Practical Test Pyramid” details costs of over-relying on UI E2E, how to distribute unit/integration/contract/E2E, and explicitly discusses Pact as CDC tooling in the sample weather app: https://martinfowler.com/articles/practical-test-pyramid.html

Ice-cream cone critique appears across industry writing as the failure mode when organizations staff “QA only does UI automation” without developer-owned unit tests — symptom match for AI startups that demo via ClickOps and skip package tests.

Syllabus scenario: PR CI runs 200 unit tests + 20 ASGI tests with `FakeLLM` in <30s; nightly runs retrieval integration + a 50-case eval sample; staging smoke hits `/health` and one chat path. That shape is the pyramid applied to LLM services.

---

## Open Questions

- Is the pyramid still right **per microservice** vs **per system** when each service is tiny?  
- Should “ASGI in-process tests” be counted as unit or integration in metrics dashboards?  
- How much live-model testing is ethically/economically required before calling a release “eval-gated”?  
- Trophy vs pyramid for teams with excellent Testcontainers ergonomics?

---

## Sources

- https://martinfowler.com/articles/practical-test-pyramid.html  
- https://docs.pytest.org/en/stable/  
- https://fastapi.tiangolo.com/tutorial/testing/  
- https://docs.pact.io/getting_started  
- https://pactflow.io/blog/contract-testing-vs-integration-testing/  
