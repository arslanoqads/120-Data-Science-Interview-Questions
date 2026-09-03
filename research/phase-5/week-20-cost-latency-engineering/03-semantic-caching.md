# 03 — Semantic caching: embedding similarity vs exact-match; threshold calibration

> Week 20 — skip generation when the **answer is already known**.  
> Research notes (raw). Provider **prefix/KV** prompt caching is file [04](04-prompt-cache-compression-batching.md) (different layer). Tenant isolation for cache keys is mandatory (Week 19).

---

## Fundamentals

Two **response caches** (store **outputs**, not KV tensors):

**Exact-match cache.** Hash the full request that affects generation: model (or routed model), `messages`, tools, temperature, seed, response format, **tenant_id**, prompt version. Store in Redis/disk/S3. Hit only on identical prompts. Lookup is sub-ms after the hash. Safe for **temperature=0** FAQ and idempotent classify endpoints.

LiteLLM exact cache types: in-memory, disk, Redis, Valkey, S3, GCS ([proxy caching](https://docs.litellm.ai/docs/proxy/caching); [all caches](https://docs.litellm.ai/docs/caching/all_caches)). Dynamic per-request controls: `ttl`, `s-maxage`, `no-cache`, `no-store`, `namespace`. Response header `x-litellm-cache-key` on hits. `/cache/ping`, `/cache/delete` for ops.

**Semantic cache.** Embed the prompt (LiteLLM: **entire `messages` array**, system included). Return the nearest prior **response** if cosine similarity ≥ `similarity_threshold`. Hits paraphrases (“reset password” ≈ “how do I change my pwd?”). Backends: **Redis semantic**, **Qdrant semantic**, **Valkey semantic**.

**Inline embedding tax:** LiteLLM runs the embedding **before** the LLM; default cap **5 seconds**. On timeout: miss, header `x-litellm-semantic-similarity: 0.0`, proceed to the model. Tune `semantic_cache_embedding_timeout` / `SEMANTIC_CACHE_EMBEDDING_TIMEOUT_SECONDS`. A hanging embedder therefore adds seconds to **every** request — budget this like a router.

**Threshold calibration.** Too low (e.g. 0.7) → **wrong-answer reuse** (silent corruption). Too high (e.g. 0.98) → few hits (you paid for embeddings and got nothing). Procedure:

1. Build labeled pairs: paraphrase / same intent / **same gold answer** vs similar-but-different (refund vs cancel).  
2. Plot **precision of “safe to reuse”** vs threshold; optionally recall (hit rate).  
3. Pick operating point from product risk (support macros: high precision; trivia: looser).  
4. Re-calibrate when embedding **model** or prompt **template** changes (the space moved).

**Tenant-scope is not optional.** Cache key / vector filter **must** include `tenant_id` (and often `user_id` if answers are personalized). Cross-tenant semantic hit = data leak. Week 19 PEP applies to Redis as much as Postgres.

**Agentic / multi-turn (LiteLLM explicit warning).** Consecutive agent turns are previous messages **plus a small delta**; embeddings sit at **~0.99**. Any practical τ replays the **previous turn’s** reply → repeated **tool calls**. Raising τ does not reliably fix it. `tool_calls` are **not** in the embedded text, so the cache cannot see “we already called `create_ticket`.” **Recommendation:** semantic cache for **single-shot**; exact-match (full-request hash) for agents. Mitigations: virtual-key `metadata.cache.no-cache`, `mode: default_off` + opt-in, or per-request `no-cache`. Anthropic `/v1/messages` and passthrough routes **skip** LiteLLM response cache entirely.

**Never cache** authorized, personalized, or **post-mutation** answers without authz context in the key (and usually `no-store` after tools that changed CRM state).

**Relationship to routing:** cache **before** the quality router when the answer is reusable **across models** only if you **key by answer-equivalence**, not by model — usually you **should include model ID** (Haiku wording ≠ Sonnet). Shared embedding model with an embedding **router** is attractive but conflates “similar question” with “similar difficulty.”

---

## Alternatives & Tradeoffs

| Cache | Hit rate | Risk | Extra latency |
|-------|----------|------|----------------|
| Exact (Redis hash) | Low–medium | Low | Minimal |
| Semantic | Higher on FAQ | Stale / wrong-intent / cross-tenant if miskeyed | **Embed every request** |
| Prompt/KV cache (provider) | Reuses **prefix compute**, still generates | Prefix discipline; not an answer store | None to app on hit (faster prefill) |
| No cache | Zero reuse risk | Max $ | — |
| HTTP CDN on GET APIs | Great for public docs | Wrong for POST chat | Edge |

| Semantic backend | Pros | Cons |
|------------------|------|------|
| Redis-semantic | Ops-familiar | ANN quality vs dedicated vector DB |
| Qdrant-semantic | Real vector index | Another cluster |
| Valkey-semantic | Redis-compatible fork | Same design as Redis path |

---

## Necessity

Skipping cache leaves **easy money** on support bots with repeated intents.

Uncalibrated semantic cache creates **confident wrong** replies. Exact-prompt eval suites **will not catch** this (they never paraphrase).

Global (no tenant) semantic cache is a **SEV-0 class leak**, same as unfiltered RAG.

Semantic cache on a **coding agent** looks like a “stuck loop” bug and will be mis-attributed to the model.

Embed timeout without a **miss-and-proceed** policy turns an embed outage into a **full gateway outage**.

---

## Industry Practice

**Common:** Redis exact cache on temperature-0 classify/summarize; semantic off; one global namespace.

**Strong:**

1. Separate caches **per task type** (FAQ vs RAG vs agent) with different τ and TTLs.  
2. TTL by **content volatility** (tax policy: hours; math identity: days).  
3. Key includes **model ID + prompt version + tenant**.  
4. Dashboards: hit rate, embed latency, similarity **of accepted hits**, wrong-hit rate from sampled review.  
5. Kill switch (`mode: default_off` or key `no-cache`).  
6. Exclude PII-heavy traffic; hash or drop.  
7. Bypass when tools already mutated state.  
8. `/cache/ping` in readiness (Week 18 `/ready` should not require cache for liveness, but degraded mode should be visible).  
9. Virtual-key auth cache (`enable_redis_auth_cache`) is **not** a response cache — do not confuse the two LiteLLM Redis uses.

---

## Concrete Scenario

LiteLLM config sketch (from docs; verify field names live):

```yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis-semantic
    similarity_threshold: 0.8   # calibrate; 0.8 is an example not a default-of-record
    redis_semantic_cache_embedding_model: my-embedding-model
    semantic_cache_embedding_timeout: 10.0
    ttl: 600
```

Docs (exact + semantic, agentic warning, 5 s embed timeout):  
https://docs.litellm.ai/docs/proxy/caching  
https://docs.litellm.ai/docs/caching/all_caches  

Prompt-caching (different feature) is cross-linked from those pages:  
https://docs.litellm.ai/docs/completion/prompt_caching  

**Calibration scenario:** 1,000 support paraphrases labeled by humans. At τ=0.92, precision 99%, hit rate 18%. At τ=0.80, precision 91%, hit rate 41%. Legal/refund intents stay on exact-match or no-cache.

---

## Open Questions

- Can learned **routers** and semantic caches share one embedding space without leaking difficulty into “sameness”?  
- Legal status of caching **customer prompts** under EU residency / ZDR (Week 19) — cache replicas in-region?  
- Optimal metric beyond cosine for **short noisy** queries (BM25 hybrid cache key)?  
- Should a semantic hit **credit** the team that paid for the original generation (file [05](05-cost-attribution-dashboards.md))?  
- LLM-generated **canonical questions** as cache keys vs raw embed of user text.

---

## Sources

- https://docs.litellm.ai/docs/proxy/caching  
- https://docs.litellm.ai/docs/caching/all_caches  
- https://docs.litellm.ai/docs/completion/prompt_caching  
- https://docs.litellm.ai/docs/proxy/virtual_keys  
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  
- https://www.lmsys.org/blog/2024-07-01-routellm/  
