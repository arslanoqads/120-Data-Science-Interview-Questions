# 04 — Prompt caching, prompt compression, and batching

> Week 20 — cheaper **generation** when you still must call a model.  
> Research notes (raw). Response-level semantic/exact cache is file [03](03-semantic-caching.md).

---

## Fundamentals

Three different “batch/cache/compress” ideas get mixed in slides. Keep them separate:

| Layer | What is reused | Interactive? |
|-------|----------------|--------------|
| **Provider prompt / prefix / KV cache** | Attention state for a **byte-identical prefix** | Yes — faster prefill, cheaper input tokens on hits |
| **Prompt compression** | Shorter **text** sent to the API | Yes — quality risk |
| **Continuous batching** (self-hosted) | GPU timesteps across **many users** | Yes — throughput; can add queueing latency |
| **Provider Batch API** | Offline job discount | **No** — hours of lag |

### Provider prompt caching

**Anthropic.** Explicit `cache_control` (`type: ephemeral`). **Automatic** (top-level `cache_control`; breakpoint on last cacheable block, moves as the conversation grows) vs **explicit** breakpoints on blocks (up to **4**; automatic uses one slot). Prefix order: **`tools` → `system` → `messages`**. Writes happen **at breakpoints**; reads look back (on the order of **20 blocks**) for a prior write — a breakpoint on a **changing** suffix (timestamps) never hits. Default TTL **5 minutes**, refreshed on hit; **1-hour** TTL exists at higher **write** price. Pricing pattern (confirm live): 5-minute **writes ~1.25×** base input; **1h writes ~2×**; **reads ~0.1×** (90% off). Minimum tokens: **1,024** for many Sonnet-class models; **4,096** for some Opus/Haiku SKUs — below min, no error, usage shows zeros. Usage fields: `cache_creation_input_tokens`, `cache_read_input_tokens`. Cookbook: latency **&gt;2×** better and cost **up to 90%** on repetitive tasks ([docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching); [cookbook](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)).

**Design rule:** put **static** instructions, tools, and large corpus chunks **first**; **variable user query last**. Unstable JSON tool schemas between calls destroy hit rates.

**OpenAI.** Automatic for long prompts (classic: **≥1,024 tokens**, longest prefix match in **128-token** increments). `usage.prompt_tokens_details.cached_tokens` (Responses API: `input_tokens_details`). Caches typically **5–10 min** idle, gone within ~**1 hour**; **not shared across organizations**; eligible for ZDR narratives in OpenAI’s materials — **still read the current DPA**. Optional `prompt_cache_key` improves **routing stickiness** to the machine holding KV (cookbook: coding customer **60% → 87%** hits). Newer GPT-5.6+ families add explicit breakpoints / `prompt_cache_retention` (`in_memory` vs `24h`) — **LiteLLM passes these through**; re-fetch API names before teaching ([OpenAI guide](https://platform.openai.com/docs/guides/prompt-caching); [launch post](https://openai.com/index/api-prompt-caching/); [Prompt Caching 201](https://developers.openai.com/cookbook/examples/prompt_caching_201)).

**LiteLLM.** Normalizes cache usage across providers; `completion_cost()` includes cache-hit pricing ([prompt caching](https://docs.litellm.ai/docs/completion/prompt_caching)). Load-balanced Claude: `router_settings.optional_pre_call_checks: [prompt_caching]` so the **second** turn hits the **same deployment/account** that wrote the cache ([Claude Code routing](https://docs.litellm.ai/docs/tutorials/claude_code_prompt_cache_routing)). `cache_control_injection_points` can stamp system/trailing turns for clients that never set `cache_control`.

**Gemini / Vertex:** separate `cachedContents` APIs; min tokens (LiteLLM notes **1024**); do not assume Anthropic breakpoint semantics.

### Prompt compression

Shorten context **before** send. **LLMLingua** (Microsoft): small LM perplexity → drop low-information tokens; claimed **up to ~20×** with modest quality loss on their suites; compressed text is **ugly for humans**, OK for models ([arXiv:2310.05736](https://arxiv.org/abs/2310.05736); [MSR project](https://www.microsoft.com/en-us/research/project/llmlingua/llmlingua/)). **LongLLMLingua** for query-aware RAG compression. **LLMLingua-2**: BERT-sized keep/drop classifier, faster. **Prefer better retrieval / rerank (Phase 2)** over aggressive compression when citations matter. Compression **fights prompt caching** if it **permutes** a previously stable prefix — compress the **volatile retrieved docs**, not the static system prompt.

### Batching

**vLLM continuous batching + PagedAttention.** Scheduler admits/retires sequences **per token step**, not per whole batch. PagedAttention stores KV in **blocks** (OS paging analogy) → less fragmentation, larger batches, **2–4×** throughput vs prior SOTA in the SOSP paper; blog claimed up to **24×** vs HF Transformers in early serving numbers ([arXiv:2309.06180](https://arxiv.org/abs/2309.06180); [vLLM blog](https://blog.vllm.ai/2023/06/20/vllm.html); [SOSP talk](https://www.youtube.com/watch?v=UdNocRPQS3Y)). This is **self-hosted GPU $**, not provider invoice line items. Interactive SLOs: large batches can **hurt TTFT** if prefill is not isolated (chunked prefill / separate prefill workers — follow current vLLM docs).

**Provider Batch APIs.** Async, typically **~50%** off (OpenAI Batch is the usual citation — [Batch guide](https://platform.openai.com/docs/guides/batch)). For **offline** eval, embeddings backfill, nightly tagging. **Never** on the user chat path.

**Client micro-batching** of embeddings: higher throughput, worse tail latency; set a max wait (e.g. 5–20 ms) or you miss chat SLOs.

---

## Alternatives & Tradeoffs

| Technique | Saves | Risks |
|-----------|-------|--------|
| Prompt caching | Input $ + prefill TTFT on hits | Prefix discipline; write premium; TTL; load-balancer splitting the cache |
| Semantic response cache | **Full** output $ | Wrong hit (file [03](03-semantic-caching.md)) |
| Compression | Input tokens | Lost details / citations; cache-key churn |
| Batch API | $/throughput | Hours of lag |
| Continuous batching | GPU utilization | Queueing; not a provider discount |
| Smaller model / routing | Everywhere | Capability (files [01](01-model-routing.md)–[02](02-model-cascading-routellm.md)) |
| Session affinity for cache | Hit rate | Forfeits down-routing later turns |

---

## Necessity

RAG systems with **50k-token** system+tools payloads that **do not** use prompt caching **hemorrhage** money every turn.

Unstable tool JSON **between** calls destroys Anthropic/OpenAI prefix hits; you pay **write** rates in a loop.

Synchronous batching on a **user-facing** path destroys latency SLOs (you invented a Batch API with worse UX).

Compression without a **quality gate** drops the citation the lawyer needed.

Load-balancing Claude **without** prompt-cache affinity doubles cache writes (LiteLLM’s whole Claude Code tutorial exists because of this).

---

## Industry Practice

**Common:** Anthropic `cache_control` on the large system prompt; OpenAI “it just works” with no `cached_tokens` dashboard; Batch API unused; vLLM default args.

**Strong:**

1. Monitor **cache_read vs cache_write** ratios; alert on miss regressions after prompt edits.  
2. Version **tool schemas** separately; freeze them in the prefix.  
3. Automatic caching for multi-turn; **explicit** breakpoint at the end of the **static** prefix when the last block is a timestamp or per-request RAG blob.  
4. `prompt_cache_key` = hash(tenant + template_version + tool_schema_version) for OpenAI stickiness — **not** raw user_id unbounded cardinality if it fragments the cache.  
5. Batch API for nightly corpus tagging and Week 16/17 eval jobs.  
6. Compression only behind golden-set gates; never compress legal footnotes you must quote.  
7. vLLM: measure **tokens/s and TTFT p95**; do not cite 24× as your number.

---

## Concrete Scenario

Anthropic (mechanics, breakpoints, usage):  
https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  

OpenAI:  
https://platform.openai.com/docs/guides/prompt-caching  
https://openai.com/index/api-prompt-caching/  

LiteLLM cross-provider + Claude deployment pinning:  
https://docs.litellm.ai/docs/completion/prompt_caching  
https://docs.litellm.ai/docs/tutorials/claude_code_prompt_cache_routing  
https://docs.litellm.ai/docs/tutorials/prompt_caching  

vLLM / PagedAttention:  
https://blog.vllm.ai/2023/06/20/vllm.html  
https://arxiv.org/abs/2309.06180  
https://docs.vllm.ai/en/latest/  
https://www.youtube.com/watch?v=UdNocRPQS3Y  

LLMLingua:  
https://arxiv.org/abs/2310.05736  

OpenAI Batch:  
https://platform.openai.com/docs/guides/batch  

Walkthrough of Anthropic cache_control placement (public YouTube):  
https://www.youtube.com/watch?v=jQw3_6meUF8  

---

## Open Questions

- Prompt caches vs **ZDR / residency**: is KV state “processing” in a region you promised?  
- Is compression still worth it as **cached** long context gets cheaper?  
- Automatic vs explicit breakpoints for **agent transcripts** (Anthropic automatic vs 20-block lookback traps).  
- GPT-5.6+ `prompt_cache_retention: 24h` vs Anthropic `ttl: 1h` — one gateway policy or per-provider?  
- Should routers **avoid** switching models mid-session solely to protect prefix cache, or is LiteLLM’s “switch-back still warm” result enough?

---

## Sources

- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching  
- https://platform.openai.com/docs/guides/prompt-caching  
- https://openai.com/index/api-prompt-caching/  
- https://developers.openai.com/cookbook/examples/prompt_caching101  
- https://developers.openai.com/cookbook/examples/prompt_caching_201  
- https://docs.litellm.ai/docs/completion/prompt_caching  
- https://docs.litellm.ai/docs/tutorials/claude_code_prompt_cache_routing  
- https://docs.litellm.ai/docs/auto_router/prompt_caching  
- https://platform.openai.com/docs/guides/batch  
- https://arxiv.org/abs/2310.05736  
- https://www.microsoft.com/en-us/research/project/llmlingua/llmlingua/  
- https://arxiv.org/abs/2309.06180  
- https://blog.vllm.ai/2023/06/20/vllm.html  
- https://docs.vllm.ai/en/latest/  
- https://www.youtube.com/watch?v=UdNocRPQS3Y  
- https://www.youtube.com/watch?v=jQw3_6meUF8  
