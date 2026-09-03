# Week 20 Research Corpus — Cost and latency engineering

> Phase 5 — Production, Cost, and Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (LMSYS RouteLLM blog + arXiv + GitHub, LiteLLM docs, Anthropic/OpenAI prompt-caching docs, vLLM/SOSP, FrugalGPT, LLMLingua, AWS GenAI Lens, OpenTelemetry, YouTube from SOSP / RouteLLM walkthroughs). **No pirate PDFs, no libgen/pdfcoffee, no unauthorized course decks.**

This directory is the Week 20 research repository. Read concept files in order, then the source map. **Do not start Week 21 (legacy / messy integration) from this corpus** — this week ships **model routing**, **RouteLLM-style cascading (~15% expensive / ~95% quality)**, **semantic caching**, **prompt cache + compression + batching**, and **cost-attribution dashboards**. Week 19 already isolated tenants and virtual keys; this week decides **which model, cache, and dollar** each request consumes.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Design doc: router + semantic cache; cost-per-request before/after |
| 01 | [01-model-routing.md](01-model-routing.md) | Rule / embedding / classifier routers; decision latency &lt;1 ms / ~5 ms / 50–100 ms |
| 02 | [02-model-cascading-routellm.md](02-model-cascading-routellm.md) | Route-once vs escalate; ~15% strong calls, ~95% quality |
| 03 | [03-semantic-caching.md](03-semantic-caching.md) | Exact vs semantic cache; threshold calibration; tenant keys |
| 04 | [04-prompt-cache-compression-batching.md](04-prompt-cache-compression-batching.md) | Provider KV/prefix cache, LLMLingua, batch APIs, vLLM continuous batching |
| 05 | [05-cost-attribution-dashboards.md](05-cost-attribution-dashboards.md) | Tenant × feature × model cube; LiteLLM spend; FinOps |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / vendor / YouTube index |

## Completeness checklist (Week 20)

- [x] All syllabus Week 20 concepts covered with **7 required fields**  
- [x] **Router + semantic cache** design in the week overview (not only per-concept notes)  
- [x] **Cost-per-request before/after** worked example (all-frontier vs routed + cached)  
- [x] Rule-based routing **&lt;1 ms**; embedding-based **~5 ms**; ML classifier **50–100 ms** (router decision, not LLM TTFT)  
- [x] Cascade / RouteLLM: **~15% expensive model, ~95% quality** (MT Bench MF + judge augmentation; cite paper/blog, not folklore)  
- [x] RouteLLM routers: SW ranking, matrix factorization, BERT, causal LLM; `mf` recommended in repo  
- [x] Route-once vs try-small-then-escalate vs speculative parallel vs FrugalGPT cascade  
- [x] LiteLLM Router strategies (simple-shuffle / least-busy / latency / cost) vs *quality* routers  
- [x] Semantic vs exact-match cache; cosine threshold calibration; LiteLLM Redis/Qdrant/Valkey  
- [x] LiteLLM agentic warning: semantic cache unsafe for multi-turn tool loops  
- [x] Tenant-scoped cache keys (Week 19 isolation constraint)  
- [x] Anthropic prompt caching: `cache_control`, TTL, write vs read rates, prefix order (tools → system → messages)  
- [x] OpenAI prompt caching: automatic ≥1024 tokens, `cached_tokens`, `prompt_cache_key`  
- [x] LiteLLM prompt-caching normalization + `optional_pre_call_checks: prompt_caching`  
- [x] Prompt compression (LLMLingua / LongLLMLingua) vs better retrieval  
- [x] Batching: provider Batch API vs vLLM continuous batching vs client micro-batch  
- [x] Cost dashboards: tenant, surface, model, prompt version, router arm, cache hit type, cache_read/write tokens  
- [x] LiteLLM spend tracking / virtual keys / budgets  
- [x] YouTube: RouteLLM walkthrough + SOSP ’23 PagedAttention (vLLM)  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 20)

You already have a **containerized, OIDC-gated, tenant-isolated LLM service** (Weeks 18–19). This week you **stop sending every request to the frontier model**.

1. **Route before you generate.** Rules first (&lt;1 ms): path, tier, `task_type`, tools, length. Uncertain traffic → embedding (~5 ms) or a trained classifier (50–100 ms). Never put an LLM-as-router on the hot path unless you measured that it still saves money.  
2. **Calibrate a cascade, do not guess a percentage.** Plot quality vs % strong-model calls on *your* golden set. The RouteLLM public headline is **~95% of GPT-4 quality at ~14% GPT-4 calls on MT Bench** (matrix factorization + LLM-judge augmentation). Your production mix will differ; the *shape* of the curve is the deliverable.  
3. **Cache in two layers.** Exact-match (hash) for deterministic FAQ; semantic (embedding + threshold) for paraphrases — **tenant in the key**, **off for agentic multi-turn**. Provider **prompt caching** for long static prefixes (system + tools + corpus).  
4. **Structure prompts for prefix hits.** Static first, user query last. Monitor `cache_read` vs `cache_write`. Compression and Batch APIs are for the paths that cannot be prefix-cached or are offline.  
5. **Attribute every dollar.** Gateway tags: tenant, feature, model, prompt version, router decision, cache class. Cost per **successful task**, not only cost per call. Hard budgets per tenant (Week 19 virtual keys).

Interview artifact = **router decision tree with latency budgets** + **quality-vs-%-strong curve** (or RouteLLM-cited operating point plus “we would re-benchmark”) + **cost cube sketch** (tenant × model × feature) + **before/after $/request**.

## Default path (synthesis)

1. **Rules are free; classifiers are not.** Spend 50–100 ms only when the LLM call is seconds ([RouteLLM paper](https://arxiv.org/abs/2406.18665); [LiteLLM routing](https://docs.litellm.ai/docs/routing)).  
2. **~15% / ~95% is a calibrated point, not a law.** MT Bench + Mixtral/GPT-4 Turbo + MF + judge data ([LMSYS blog](https://www.lmsys.org/blog/2024-07-01-routellm/); [GitHub](https://github.com/lm-sys/RouteLLM)). MMLU/GSM8K savings were smaller.  
3. **Semantic cache is a product decision.** Uncalibrated cosine ≈ silent wrong answers. Agentic traffic → exact-match only ([LiteLLM caching](https://docs.litellm.ai/docs/proxy/caching)).  
4. **Prompt cache is prefix discipline.** Anthropic `cache_control`; OpenAI automatic + `prompt_cache_key` ([Anthropic](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching); [OpenAI](https://platform.openai.com/docs/guides/prompt-caching)).  
5. **If you cannot name the tenant and feature on yesterday’s spend, you cannot optimize.** ([LiteLLM cost tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)).  
6. **Self-hosted throughput ≠ interactive latency.** Continuous batching / PagedAttention for GPU utilization ([vLLM blog](https://blog.vllm.ai/2023/06/20/vllm.html); [SOSP talk](https://www.youtube.com/watch?v=UdNocRPQS3Y)).  
