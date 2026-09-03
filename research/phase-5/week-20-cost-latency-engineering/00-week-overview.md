# 00 — Week overview: router + semantic cache, cost-per-request before/after

> Week 20 — Cost and latency engineering  
> Research notes (raw). Phase 5 week after auth / identity / enterprise (Week 19). Next: legacy messy integration (Week 21). Do not start ETL/idempotent side-effects from this corpus.

This file is the **design document** for the two FDE interview artifacts: (1) a **pre-generation path** (rules → optional embed/classifier → cache → model), (2) a **cost-per-request before/after** you can defend with RouteLLM-style calibration, not a slide that says “we’ll just use Haiku.”

---

## Fundamentals

Week 19 shipped **who may call the gateway** and **where tenant data may live**. The typical remaining failure is economic: every authenticated request still hits the frontier model, semantic cache is off or global, and Finance sees one OpenAI invoice.

This week answers:

1. **Which model should this request use?** Routing (file [01](01-model-routing.md)) and cascading (file [02](02-model-cascading-routellm.md)).  
2. **Do we need a model at all?** Semantic / exact response cache (file [03](03-semantic-caching.md)).  
3. **If we do generate, can we reuse prefix compute?** Prompt caching, plus compression and batching (file [04](04-prompt-cache-compression-batching.md)).  
4. **Who spent the money?** Attribution dashboards (file [05](05-cost-attribution-dashboards.md)).

### Design: router in front of the LLM (decision latency vs generation latency)

**Model routing** chooses a deployment *before* paying for a full generation. The latency numbers below are for the **router decision**, not time-to-first-token of the LLM:

| Stage | Typical decision latency | What it looks at | When to run |
|-------|--------------------------|------------------|-------------|
| **Rule-based** | **&lt;1 ms** | Path, tenant tier, `task_type`, prompt length, tool schema present, language, regex | Always first; free |
| **Embedding-based** | **~5 ms** local/small embed (network embed higher) | Nearest prototype / cluster (“billing FAQ” → weak model) | After rules miss |
| **ML classifier** | **~50–100 ms** BERT-scale; more if LLM-as-router | P(strong wins \| query) from preference data | Only if still uncertain |

Cascade the *routers* the same way you cascade *models*: rules → light embed → heavy classifier. A 100 ms BERT in front of a 2 s Sonnet call is noise. A 100 ms BERT in front of a 150 ms classifier model **is** the latency budget.

LiteLLM’s **Router** is mostly **load-balancing and failover** across deployments of the *same* logical model (`simple-shuffle`, least-busy, latency-based, cost-based) ([routing docs](https://docs.litellm.ai/docs/routing)). RouteLLM is a **quality router** between a **strong expensive** and **weak cheap** model ([blog](https://www.lmsys.org/blog/2024-07-01-routellm/); [repo](https://github.com/lm-sys/RouteLLM)). Production gateways need **both**: pick capability tier, then pick a healthy deployment in that tier (and pin deployment when prompt-cache affinity matters — file [04](04-prompt-cache-compression-batching.md)).

**RouteLLM operating point you must be able to cite:** Ong et al. (2024), GPT-4 Turbo vs Mixtral 8x7B. On **MT Bench**, matrix factorization trained on Chatbot Arena **plus LLM-judge augmentation** reached **95% of GPT-4’s score with 14% of calls to GPT-4** (~85% cost reduction vs all-GPT-4; ~75% cheaper than a random router at the same quality point). Without augmentation, MF still hit 95% at **~26%** GPT-4 calls. On **MMLU** / **GSM8K**, cost cuts at 95% quality were smaller (~45% / ~35% vs all-GPT-4 in the LMSYS blog). Domain shift is the lesson: Arena-trained routers need **in-domain augmentation** ([blog](https://www.lmsys.org/blog/2024-07-01-routellm/); [arXiv:2406.18665](https://arxiv.org/abs/2406.18665)).

FDE translation: **design for ~10–20% frontier traffic** *if* you plot the curve on *your* traces. Do not put “15%” in an SLA.

### Design: semantic cache beside the router

```
request (tenant, messages, model hint, tools)
    │
    ├─► rules  (<1 ms) ── known cheap / known must-strong / cache-bypass (PII, mutating tools)
    │
    ├─► exact cache  (hash of model + messages + params + tenant)  ── hit → return
    │
    ├─► semantic cache (embed messages; cosine ≥ τ; same tenant)  ── hit → return
    │         embedding is INLINE; LiteLLM default timeout ~5 s then miss
    │
    ├─► quality router (embed ~5 ms or BERT 50–100 ms) → weak | strong
    │
    └─► provider call (prompt cache on stable prefix)
              usage: input, output, cache_read, cache_write
```

**Exact-match** is safe for temperature-0 FAQs. **Semantic** hits paraphrases; **τ too low** reuses the wrong answer; **τ too high** never hits. Calibrate on labeled pairs (same intent / same gold answer). **Tenant must be in the key** — a global semantic cache is a Week 19 isolation bug.

LiteLLM: Redis / Qdrant / Valkey semantic caches; **prefer semantic for single-shot**; **exact-match for multi-turn agents** (consecutive turns embed ~0.99 similar and replay stale tool calls) ([proxy caching](https://docs.litellm.ai/docs/proxy/caching)).

### Cost-per-request before / after (worked example)

Prices move; **use this as a spreadsheet shape**, then plug live list prices. Illustrative 2024-era **per-request** averages for a 2k-in / 400-out support turn (not a quote):

| Arm | Relative $ / request (index) |
|-----|------------------------------|
| Strong (frontier) | **100** |
| Weak (small / Mixtral-class API) | **5** |
| Semantic cache hit (embed + Redis) | **1** (embed + lookup; no generation) |
| Exact cache hit | **~0.1** |

**Before (common demo):** 100% strong. Cost index = **100** per request. Quality = 100% of frontier on your golden set (by construction).

**After A — RouteLLM-shaped cascade only (no response cache):** 14% strong / 86% weak, matching the **MT Bench 95%-quality** public point.  
Cost index = `0.14×100 + 0.86×5` = **18.3** → **~82% $ reduction**, quality target **~95%** of frontier *on that bench*. Your MMLU-like traffic will not get this.

**After B — same router + 30% semantic hits on the traffic that would have called an LLM** (FAQ-heavy support; calibrated τ; tenant-scoped):  
LLM calls = 70% of requests; of those, 14% of LLM calls still strong.  
- Cache hits: 30% × 1 = 0.30  
- Strong: 0.70 × 0.14 × 100 = 9.8  
- Weak: 0.70 × 0.86 × 5 = 3.01  
Cost index ≈ **13.1** vs 100 (**~87% reduction**). Quality now depends on cache precision — measure **wrong-hit rate**, not only $ .

**After C — add Anthropic/OpenAI prompt caching** on the remaining LLM calls with a stable 8k-token system+tools prefix: cache **reads** are billed at a fraction of input (Anthropic commonly **0.1×** input for reads, **1.25×** for 5-minute writes; OpenAI automatic prefix discount — **verify live docs**). This does **not** replace routing; it multiplies savings on the long prefix. Track `cache_read_input_tokens` / `cached_tokens` or you will “enable caching” and never know.

**What to put on the interview whiteboard:** before = all-frontier $/request from a week of prod traces; after = the same traces **replayed** through the router (shadow) + cache hit log; quality = golden-set score and CSAT by route arm. If you only have public benches, say so and cite RouteLLM’s **14% / 95%** as the *existence proof*, not your SLA.

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| Quality routing, cascading, caches, compression, cost cube | OIDC/SAML, residency *policy* (Week 19) — still **honor** tenant/region in the router |
| Cache **as latency/$** | Cache **as isolation** (must still be tenant-keyed — Week 19) |
| HPA on gateway concurrency (Week 18) as a *capacity* lever | Choosing replica count instead of routing (wrong lever for provider $) |
| Cost of eval traffic as a dashboard dimension | Building the eval flywheel (Weeks 16–17 already) |
| Idempotency only as “don’t cache mutating tool results” | Messy dual-write / ETL (Week 21) |

---

## Alternatives & Tradeoffs

| Approach | $ | Quality control | Latency |
|----------|---|-----------------|---------|
| **Rules + optional MF/BERT router + tenant semantic cache + prefix-stable prompt cache + spend cube** | High save when traffic is mixed-difficulty | Requires golden set + τ calibration + shadow routing | Router &lt;100 ms; cache hits skip generation |
| Always frontier | Zero save | Simple | Best TTFT variance if one model |
| Always small | Max save | Silent regressions | Fast, wrong |
| Random % to GPT-4 | Predictable invoice | Not a quality optimizer | RouteLLM’s baseline to beat |
| LLM-as-router | Often negative | Flexible | Can exceed savings |
| Semantic cache only, no router | FAQ wins | Wrong-intent hits | Embed on every miss path |
| Prompt cache only | Wins on long prefixes | No help if every prompt is unique | TTFT down on hits |
| FrugalGPT-style **sequential** cascade (call weak, then strong) | High quality safety | **Adds a full generation** on hard queries | File [02](02-model-cascading-routellm.md) |

---

## Necessity

If you skip **routing:** high-volume RAG/support unit economics die; or you “save 40%” with a small model and tank CSAT with no escalate path.

If you skip **calibration:** a threshold copied from a blog (0.8 cosine, 0.5 RouteLLM cost threshold) is not your operating point. MMLU-like OOD traffic looks like random routing ([LMSYS blog](https://www.lmsys.org/blog/2024-07-01-routellm/)).

If you skip **semantic-cache discipline:** cross-tenant hits (leak); agent loops replay the same tool call ([LiteLLM](https://docs.litellm.ai/docs/proxy/caching)); τ=0.7 serves a confident wrong refund policy.

If you skip **prompt-cache prefix hygiene:** 50k-token tool schemas rewritten every call; you pay cache **writes** forever.

If you skip **attribution:** routing “wins” are anecdotal; one scraper tenant burns the org key; eval traffic looks like prod spend.

---

## Industry Practice

**Common:** hardcoded model per endpoint (`/summarize` → Haiku); Redis exact cache on T=0; Anthropic `cache_control` on the system prompt; monthly CSV from the provider; LiteLLM `simple-shuffle` across Azure deployments.

**Strong / senior:**

1. Feature-flagged model IDs; **shadow** learned router (log decision, do not yet steer).  
2. Weekly **quality vs % strong** plot on a frozen golden set; auto-tune RouteLLM `threshold`.  
3. Productize **premium = always strong** vs **balanced**.  
4. Semantic cache **per task type**, TTL by volatility, kill switch, exclude PII.  
5. Prompt templates **versioned**; cache-hit regression alerts after prompt edits.  
6. `optional_pre_call_checks: prompt_caching` so load-balanced Claude deployments do not split the KV prefix ([LiteLLM Claude Code caching](https://docs.litellm.ai/docs/tutorials/claude_code_prompt_cache_routing)).  
7. Real-time gateway dashboards; per-tenant soft/hard budget; cost of eval vs prod tagged.

YouTube: practical RouteLLM client walkthrough ([RouteLLM tutorial](https://www.youtube.com/watch?v=mcZKQe2pUA0)); serving-side batching/KV ([SOSP ’23 PagedAttention](https://www.youtube.com/watch?v=UdNocRPQS3Y)).

---

## Concrete Scenario (URL)

**Support copilot, 10 M requests/month.** Before: `gpt-4-turbo` on every ticket. After: LiteLLM proxy with virtual keys per tenant (Week 19); rules send `/classify-intent` to a small model; remaining chat goes through RouteLLM `mf` (or a BERT router hosted next to the gateway); Redis exact cache for canned macros; Qdrant semantic cache for FAQ paraphrases with τ chosen on a 2k labeled pair set; Claude/Sonnet path uses `cache_control` on tools+system; Grafana cube: `tenant × product_surface × model × cache_hit`.

Primary routing numbers:  
https://www.lmsys.org/blog/2024-07-01-routellm/  
https://arxiv.org/abs/2406.18665  
https://github.com/lm-sys/RouteLLM  

Gateway routing / cache / spend:  
https://docs.litellm.ai/docs/routing  
https://docs.litellm.ai/docs/proxy/caching  
https://docs.litellm.ai/docs/proxy/cost_tracking  

Prompt caching:  
https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  
https://platform.openai.com/docs/guides/prompt-caching  

YouTube:  
https://www.youtube.com/watch?v=mcZKQe2pUA0  
https://www.youtube.com/watch?v=UdNocRPQS3Y  

---

## Open Questions

- As speculative decoding and fast small models shrink TTFT, is a **50–100 ms** classifier still acceptable, or do rules+embed win by default?  
- Multi-model (&gt;2) routing: taxonomy explosion vs pairwise routers vs LiteLLM Auto Router complexity tiers?  
- Who sets the utility function per tenant — $ , latency, energy, or “never wrong on refunds”?  
- Should semantic cache and embedding routers **share one embedding space**?  
- How do prompt caches interact with **ZDR / residency** contracts (Week 19)?  
- Fair chargeback for **weak attempt + strong escalate** (two generations, one user-visible answer)?

---

## Sources

- https://www.lmsys.org/blog/2024-07-01-routellm/  
- https://arxiv.org/abs/2406.18665  
- https://github.com/lm-sys/RouteLLM  
- https://docs.litellm.ai/docs/routing  
- https://docs.litellm.ai/docs/proxy/caching  
- https://docs.litellm.ai/docs/completion/prompt_caching  
- https://docs.litellm.ai/docs/proxy/cost_tracking  
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  
- https://platform.openai.com/docs/guides/prompt-caching  
- https://arxiv.org/abs/2305.05176  
- https://www.youtube.com/watch?v=mcZKQe2pUA0  
- https://www.youtube.com/watch?v=UdNocRPQS3Y  
