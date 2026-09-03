# 05 — Mocking external APIs in tests

> Week 2 concept research (deep). Legal sources only.

---

## Fundamentals

### Why mock
Mocks/fakes replace network/SDK calls with controlled doubles so tests **don’t hit** real OpenAI/Anthropic/Stripe/etc. Goals:

- Determinism (no provider drift mid-suite).  
- Speed (ms vs hundreds of ms).  
- Safety (**no live API keys** in unit/CI jobs).  
- Force error paths (429, 500, malformed JSON) that are hard to trigger live.

### Prefer seams over patching globals
Best seam for FastAPI LLM apps:

1. Define a **`Protocol`** (structural typing) for the port:

```python
from typing import Protocol

class LLMClient(Protocol):
    async def complete(self, prompt: str) -> str: ...
```

2. Inject via `Depends(get_llm_client)`.  
3. In tests, replace with a fake using **`app.dependency_overrides`**.

FastAPI docs: override dependencies so external auth/provider isn’t called every test — provider may charge per request and add latency: https://fastapi.tiangolo.com/advanced/testing-dependencies/

Reset overrides after tests (`app.dependency_overrides.clear()` or `={}`) to avoid cross-test pollution.

### TestClient vs AsyncClient + ASGITransport

| Client | Test style | Event-loop notes |
|--------|------------|------------------|
| `fastapi.testclient.TestClient` | Sync `def` tests | Starlette/httpx magic; familiar Requests-like API |
| `httpx.AsyncClient` + `httpx.ASGITransport(app=app)` | `async def` tests (`anyio`/`pytest-asyncio`) | Runs app on the **same** loop as the test — needed when async fixtures share loop-bound resources |

FastAPI testing tutorial uses `TestClient` for standard pytest: https://fastapi.tiangolo.com/tutorial/testing/  
Async tests docs show `ASGITransport` pattern: https://fastapi.tiangolo.com/advanced/async-tests/

Neither opens a real TCP socket; both exercise routing, validation, middleware (with caveats around lifespan — TestClient context manager runs lifespan; raw ASGITransport may need explicit lifespan management).

### Transport-level HTTP mocks
When code uses httpx directly (adapter module):

- **`respx`**: mock httpx routes (method/URL → response).  
- **`pytest-httpx`**: alternative httpx mock plugin.  
- **`responses`**: for `requests`.  
- **`unittest.mock.AsyncMock`**: mock async methods; forgetting AsyncMock on async deps causes `coroutine was never awaited` or hangs.

Assert on **outgoing** URL/headers/body, not only return values — proves the adapter builds the provider request correctly.

### Never live keys in unit tests
Hard rules for Week 2 syllabus:

- Unit/narrow integration jobs: `OPENAI_API_KEY` unset or set to obvious `"test-not-a-key"`.  
- Autouse fixture that **fails** if real network escape occurs (pytest monkeypatch docs show deleting `Session.request` to catch accidental remote calls): https://docs.pytest.org/en/stable/how-to/monkeypatch.html  
- Optional: `respx` assert `all_called` / no unexpected requests.  
- Live keys only in clearly marked `@pytest.mark.smoke` jobs with secret store injection — not default PR CI.

---

## Alternatives & Tradeoffs

| Technique | Strengths | Weaknesses | When |
|-----------|-----------|------------|------|
| **`dependency_overrides` + FakeLLM** | Clean; tests real routes | Requires DI design | FastAPI apps (preferred) |
| **Protocol + constructor injection** | Works outside FastAPI | More plumbing | Domain services |
| **monkeypatch / mock.patch** | Quick | Brittle patch targets (“patch where used”) | Legacy code |
| **respx / httpx mock** | Validates HTTP wiring | Tied to URL strings | Adapter unit tests |
| **VCR/record-replay** | Realistic payloads | Cassettes stale; scrub secrets | Rare characterization tests |
| **Pact mock server** | Contract-grade | Heavier | Multi-service CDC |
| **Live provider** | Ultimate realism | Flakes, cost, secrets | Tiny smoke only |

---

## Necessity

### Failure modes if skipped
1. **Unmocked calls in CI**: flakes, rate-limit bans, unexpected bills, secrets in logs.  
2. **Wrong patch target**: mock never hits; test silently uses real network — or always uses real and “passes” locally with `.env`.  
3. **Over-mocking**: adapter always returns 200; production can’t parse provider error envelopes.  
4. **Sync Mock on async method**: suite hangs or warnings become errors under `-W error`.  
5. **Overrides not cleared**: later tests use FakeLLM accidentally (or vice versa).  
6. **Recording cassettes with Authorization headers committed** → key leak.

### Must-dos
- Design LLM access behind an interface.  
- Override at the FastAPI dependency boundary for route tests.  
- Forbid network in unit jobs.  
- Explicitly test 422 (validation), 401/403 (auth fake), 503/429 (provider fake).

---

## Industry Practice

### Common (weak)
- `os.environ["OPENAI_API_KEY"]` required to collect tests.  
- `unittest.mock.patch("openai.ChatCompletion.create")` against outdated paths.  
- One happy-path TestClient test.  
- No assertion that the fake was invoked with expected prompt/messages.

### Strong / senior
- `FakeLLM` with scripted queue of responses + failure injections.  
- `dependency_overrides[get_llm] = lambda: fake` in fixture teardown-cleared.  
- Adapter tests with respx verifying wire format once; route tests use Protocol fake (not both every time — avoid duplication).  
- Autouse “no network” guard in `unit` marker tests.  
- Snapshot optional for large JSON fixtures; keep them scrubbed.  
- Streaming: fake async iterator yielding SSE chunks; assert client reconnect/cancel behavior in a dedicated test.

### Example fixture sketch (conceptual)

```python
@pytest.fixture
def client(fake_llm):
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

For async:

```python
@pytest.mark.anyio
async def test_chat(fake_llm):
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/v1/chat", json={...})
    app.dependency_overrides.clear()
    assert r.status_code == 200
```

---

## Concrete Scenario

pytest monkeypatch docs include mocking `requests.get` to return a `MockResponse` with `.json()`, plus an autouse pattern that removes `Session.request` so accidental remote calls fail loudly: https://docs.pytest.org/en/stable/how-to/monkeypatch.html

FastAPI dependency override docs use external auth provider as the motivating example — same pattern maps 1:1 to LLM providers (cost + latency + nondeterminism): https://fastapi.tiangolo.com/advanced/testing-dependencies/

Pact Python’s FastAPI provider example shows verification with mocked DB state handlers — complementary to unit fakes when a consumer contract exists: https://pact-foundation.github.io/pact-python/examples/http/requests_and_fastapi/test_provider/

Syllabus bar: CI green with **unset** provider key; a deliberately wrong key still yields green unit tests because the fake never reads it.

---

## Open Questions

- Recorded fixtures vs synthetic stubs when provider error schemas churn monthly?  
- How to mock **streaming** token iterators cleanly across SDK versions?  
- Is `respx` on adapters enough, or always require Protocol fakes at the domain boundary?  
- Should smoke tests live in the same repo workflow file with `if: secrets` guards?

---

## Sources

- https://fastapi.tiangolo.com/advanced/testing-dependencies/  
- https://fastapi.tiangolo.com/tutorial/testing/  
- https://fastapi.tiangolo.com/advanced/async-tests/  
- https://docs.pytest.org/en/stable/how-to/monkeypatch.html  
- https://docs.python.org/3/library/unittest.mock.html  
- https://www.python-httpx.org/async/  
- https://lundberg.github.io/respx/  
- https://pact-foundation.github.io/pact-python/examples/http/requests_and_fastapi/test_provider/  
