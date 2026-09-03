# 03 — async/await for I/O-bound LLM calls

> Week 2 concept research (deep). Legal sources only.

---

## Fundamentals

### What async buys you
`async`/`await` lets a single thread **interleave waiting on I/O** (HTTP to OpenAI/Anthropic, DB, vector DB, object storage). While one coroutine awaits a network response, the event loop runs others. That raises concurrency for **I/O-bound** workloads without one OS thread per in-flight request.

It is **not** free parallelism for CPU-bound work (embedding large batches, tokenization-heavy prep). CPU work still blocks the loop unless offloaded to threads/processes/workers.

### asyncio core ideas
- **Event loop**: schedules ready coroutines; parks those awaiting I/O.  
- **Coroutine**: `async def` function; calling it returns a coroutine object; `await` drives it.  
- **Tasks**: `asyncio.create_task` for concurrent work; `asyncio.gather` to wait on many.  
- **Cancellation**: client disconnects should cancel in-flight generation when designed to (streaming).

Official reference: https://docs.python.org/3/library/asyncio.html

### FastAPI: `async def` vs `def`
From FastAPI’s concurrency docs (TL;DR):

| Route style | Use when | Runtime behavior |
|-------------|----------|------------------|
| `async def` | You `await` async libraries (httpx, asyncpg, …) | Runs on the event loop |
| `def` | Blocking/sync libraries (many DB drivers historically, sync SDK) | FastAPI runs it in a **threadpool** |
| Mix | Per-route best choice | Supported; FastAPI “does the right thing” |

**Critical footgun:** declaring `async def` and then calling **blocking** `requests.get` or sync `OpenAI().chat.completions.create(...)` **blocks the entire event loop** — every other request on that worker stalls. Prefer:

- Native async clients (`httpx.AsyncClient`, async SDK methods), or  
- Sync `def` route (threadpool), or  
- `await asyncio.to_thread(blocking_fn, ...)` for occasional sync calls.

If unsure and not awaiting anything, FastAPI suggests normal `def`.

### httpx async
HTTPX provides `AsyncClient` for async frameworks:

```python
async with httpx.AsyncClient(timeout=30.0) as client:
    r = await client.post(url, json=payload, headers=headers)
```

Docs warn: **don’t create a new client per request in a hot loop** — use one shared client (lifespan/app state) for connection pooling. Streaming: `async with client.stream(...)` + `aiter_bytes`/`aiter_text` for SSE proxy patterns: https://www.python-httpx.org/async/

### Concurrency limits / semaphores
LLM providers enforce **RPM/TPM rate limits**. Unbounded `asyncio.gather` on 500 docs → 429 storms, retry amplification, ban risk.

Pattern:

```python
sem = asyncio.Semaphore(8)  # max in-flight completions per process

async def complete(prompt: str) -> str:
    async with sem:
        return await llm.complete(prompt)
```

Also set: HTTP timeouts, retry with jitter on 429, circuit breakers, and queue depth metrics. Semaphores are **per process** — multiply by worker count when sizing.

---

## Alternatives & Tradeoffs

| Approach | Strengths | Weaknesses | When |
|----------|-----------|------------|------|
| **async httpx + async routes** | High concurrency waiting on LLM | Must avoid blocking calls | Default Week 2 LLM gateway |
| **Sync `def` + sync SDK** | Simple; threadpool isolation | Threadpool exhaustion under load | Wrapping stubborn sync libs |
| **Threads only (no async)** | Easy mental model | Worse scaling for many idle sockets | Low QPS internal tools |
| **Process/GPU workers** | True parallelism for CPU/GPU | Ops complexity | Embeddings, local models |
| **Unbounded gather** | Max throughput attempt | Rate-limit disasters | Never in prod |
| **Semaphore / queue** | Protects provider + your wallet | Adds latency under burst | Always for fan-out |
| **Per-request AsyncClient** | Local reasoning | No pooling; extra latency | Avoid |
| **App-lifespan shared client** | Pooling, one config | Lifecycle discipline | Strong default |

---

## Necessity

### Failure modes if skipped
1. **Serial awaits** in multi-doc RAG: 5 × 800 ms = 4 s user-visible latency that `gather` + sem could cut.  
2. **Blocking sync SDK in `async def`**: p99 latency for *all* users spikes when one completion is slow.  
3. **No timeouts**: hung provider socket holds a concurrency slot forever.  
4. **No semaphore**: burst fans out 200 completions → 429 → naive retries → outage.  
5. **New client per request**: TLS handshake tax; file descriptor pressure.  
6. **Ignoring cancellation**: disconnected clients keep burning tokens.

### FastAPI guidance (must internalize)
- Use `async def` when you await.  
- Use `def` for blocking libraries so work goes to the threadpool.  
- Mixing is OK; accidental blocking inside `async def` is not.

---

## Industry Practice

### Common (weak)
- `async def` everywhere + `import requests`.  
- Global `httpx.AsyncClient()` never closed.  
- `await gather(*[llm(c) for c in chunks])` with no limit.  
- Default timeouts (or none); no 429 handling.  
- Streaming generator that won’t close the upstream response.

### Strong / senior
- Lifespan context: create `AsyncClient`, attach to `app.state`, `aclose` on shutdown.  
- Port interface `LLMClient` with `async def complete` / `async def stream`.  
- Semaphore + token-bucket aligned to provider quotas.  
- Structured retries (tenacity/backoff) only on idempotent GETs or idempotent job creates.  
- Metrics: in-flight LLM calls, queue wait, provider latency, 429 count.  
- Load-test concurrent fan-out before claiming “async makes us fast.”  
- For sync-only SDKs: isolate in `to_thread` or a dedicated worker service — don’t pretend they’re async.

### RAG / agent pipelines
Typical concurrent stages:

1. Embed query (1 call).  
2. Retrieve (DB async).  
3. Optional parallel rerank / multi-query (`gather` + sem).  
4. Completion (1 stream).  
5. Parallel tool calls inside an agent step (bounded).

Bound **tool fan-out** and **map over documents** separately; one global semaphore is a blunt but good first control.

---

## Concrete Scenario

FastAPI’s async documentation explains event-loop vs threadpool behavior and when path operations should be async: https://fastapi.tiangolo.com/async/

Practical benchmark for an LLM gateway: one uvicorn worker, 50 concurrent clients each waiting ~1s on a mocked async sleep vs blocking `time.sleep` inside `async def`. The blocking version serializes; the async version overlaps. Same demo in interviews proves you understand the loop.

HTTPX async streaming example (forward upstream stream to Starlette `StreamingResponse`) shows why shared clients + explicit `aclose` matter for SSE proxies: https://www.python-httpx.org/async/

Python asyncio docs for `Semaphore` and task groups: https://docs.python.org/3/library/asyncio-sync.html

---

## Open Questions

- Should vendor SDKs be **async-first** with sync wrappers, or the reverse?  
- Structured streaming + cancellation: who owns abort — ASGI disconnect, client `AbortController`, or job cancel API?  
- Free-threaded CPython impact on mixed CPU+I/O agents — still offload embeddings?  
- Per-tenant semaphores vs global — fairness under noisy neighbors?

---

## Sources

- https://fastapi.tiangolo.com/async/  
- https://docs.python.org/3/library/asyncio.html  
- https://docs.python.org/3/library/asyncio-sync.html  
- https://www.python-httpx.org/async/  
- https://www.python-httpx.org/advanced/transports/  
