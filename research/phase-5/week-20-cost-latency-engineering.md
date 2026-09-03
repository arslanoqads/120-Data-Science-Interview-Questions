# Week 20 — Cost and Latency Engineering for LLM Systems

> Phase 5 · Production, Cost, and Systems  
> Raw source material for FDE gate. Legal/public sources only.

---

## Concept: Model routing — rule-based, embedding-based, ML classifier

### Fundamentals
**Model routing** chooses which model handles a request *before* paying for a full generation. Goal: send easy/cheap tasks to small/fast models; reserve frontier models for hard tasks.

Three engineering families (latency is order-of-magnitude guidance for the *router decision*, not the LLM call):

| Router type | Typical decision latency | Mechanism |
|-------------|--------------------------|-----------|
| **Rule-based** | **&lt;1 ms** | If/else on metadata: path, user tier, prompt length, tool schema, language, `task_type` header, regex/keyword |
| **Embedding-based** | **~5 ms** (local/small embed; network embed can be higher) | Embed query; nearest-neighbor to labeled prototypes / clusters (“billing FAQ” → small model) |
| **ML classifier** | **~50–100 ms** (BERT-scale); more if LLM-as-router | Trained classifier predicts strong vs weak model win (RouteLLM `bert`, causal LLM router, etc.) |

Cascade these: rules first (free), then light embedding, then heavy classifier only when uncertain.

### Alternatives & Tradeoffs
| Approach | Cost save potential | Failure mode |
|----------|---------------------|--------------|
| Always frontier | Zero save | Budget blowups |
| Always small | Max save | Silent quality regressions |
| Rules only | Medium; predictable | Brittle; misses hard short prompts |
| Embedding similarity | Good for known intents | Threshold miss → wrong cluster |
| Learned router (preference data) | High when calibrated | OOD tasks look like random; needs monitoring |
| LLM-as-router | Flexible | Router can cost more than the savings |

Latency budget: a 100 ms classifier in front of a 2 s LLM call is fine; in front of a 150 ms classification model it may dominate. For chat UIs, router latency adds to time-to-first-token.

### Necessity
Without routing, unit economics kill margins on high-volume support/RAG. Without eval harnesses on the router, you “save 40%” while tanking CSAT. Without fallback when the small model fails confidence checks, users see bad answers with no recovery.

### Industry Practice
**Common:** hardcoded model per endpoint (`/summarize` → Haiku, `/analyze` → Sonnet).  
**Strong:** feature flags for model IDs; tiered routing by customer plan; shadow routing (log what a learned router *would* have done); online metrics: escalate-rate, user thumbs-down by route arm; LiteLLM Router / custom gateway with spend limits per model.

### Concrete Scenario
LMSYS RouteLLM blog — preference-trained routers between strong/weak models; matrix factorization / SW ranking / BERT / causal LLM classifiers:  
https://www.lmsys.org/blog/2024-07-01-routellm/  

arXiv paper:  
https://arxiv.org/abs/2406.18665  

GitHub:  
https://github.com/lm-sys/RouteLLM

### Open Questions
- Is ~50–100 ms still acceptable as TTFT budgets shrink with speculative decoding?
- Multi-model (&gt;2) routing: taxonomy explosion vs pairwise routers?
- Should routers optimize $ , latency, or energy — and who sets the utility function per tenant?

### Sources
- https://www.lmsys.org/blog/2024-07-01-routellm/
- https://arxiv.org/abs/2406.18665
- https://github.com/lm-sys/RouteLLM
- https://docs.litellm.ai/docs/routing

---

## Concept: Model cascading (RouteLLM-style) — ~15% expensive, ~95% quality

### Fundamentals
**Cascading / selective routing** to a strong model only when needed. RouteLLM (Ong et al., 2024) formalizes routing between a strong expensive model and a weak cheap model using preference data (Chatbot Arena votes + augmentation).

Headline results (from LMSYS blog / paper; GPT-4 Turbo vs Mixtral setup):

- On **MT Bench**, matrix factorization router with LLM-judge-augmented training achieved **95% of GPT-4 performance with ~14% of calls to GPT-4** (~85% cost reduction vs all GPT-4; ~75% cheaper than random routing baseline at same quality point).
- Without augmentation, MF still hit 95% GPT-4 quality at **~26%** GPT-4 calls on MT Bench.
- On **MMLU** / **GSM8K**, savings were smaller (blog: ~45% / ~35% cost reduction at 95% quality) — domain shift matters; Arena-trained routers need in-domain augmentation.

Operational reading for FDEs: **plan designs where ~10–20% of traffic hits the frontier model** and still hits quality SLOs — *if* you calibrate on *your* traces, not only public benches.

Cost threshold parameter in RouteLLM controls aggressiveness (higher threshold → more weak-model traffic). Production systems also add **deferred cascade**: try weak model → quality/confidence check → escalate to strong (adds latency on hard queries only).

### Alternatives & Tradeoffs
| Design | Quality control | Latency |
|--------|-----------------|---------|
| Route-once (RouteLLM style) | Depends on router calibration | +router only |
| Try-small-then-escalate | Higher safety | 2× latency on escalations |
| Speculative parallel (small+large race) | Fast when small wins | Waste $ when both run |
| Random / percentage canary | Useless for $ opt | Baseline only |

### Necessity
All-frontier default does not survive scale. Naive “use GPT-4o-mini everywhere” fails hard reasoning/customer trust. Cascading without an offline curve (quality vs % strong calls) means you are guessing the threshold.

### Industry Practice
**Common:** two model IDs in config + manual percentage.  
**Strong:** plot quality vs strong-call % on a golden set weekly; auto-tune threshold; productize “premium always strong” vs “balanced”; log router score; retrain/calibrate when model pairs change (GPT-4→Claude, etc. — RouteLLM claims some zero-shot pair transfer but you must verify).

### Concrete Scenario
Primary numbers and methodology:  
https://www.lmsys.org/blog/2024-07-01-routellm/  
https://arxiv.org/abs/2406.18665  

Commercial comparison claim in blog: open routers matched Martian/Unify quality points at **&gt;40% cheaper** on their MT Bench setup — treat as research snapshot, re-benchmark yourself.

### Open Questions
- Escalation classifiers vs answer-quality LLM judges — cost of the judge eating the savings?
- Cascading tool-using agents (router per step vs per session)?
- How to present cascade behavior in enterprise SLAs (“95% of GPT-4” is not a legal metric)?

### Sources
- https://www.lmsys.org/blog/2024-07-01-routellm/
- https://arxiv.org/abs/2406.18665
- https://github.com/lm-sys/RouteLLM

---

## Concept: Semantic caching — embedding similarity vs exact-match; threshold calibration

### Fundamentals
**Exact-match cache:** hash the full request (model, messages, params) → Redis/disk. Hit only on identical prompts. Latency: sub-ms after lookup. Safe for deterministic temperature=0 FAQ traffic.

**Semantic cache:** embed the prompt (often entire `messages` array); return nearest prior response if cosine similarity ≥ `similarity_threshold`. Hits paraphrases (“reset password” ≈ “how do I change my pwd?”).

LiteLLM supports Redis / Qdrant / Valkey semantic caches and documents that semantic lookup runs **inline** before the LLM call (embedding timeout default ~5s; failure → miss, proceed):  
https://docs.litellm.ai/docs/proxy/caching  

**Threshold calibration:** too low (e.g. 0.7) → wrong-answer reuse (silent corruption); too high (e.g. 0.98) → few hits. Calibrate on labeled pairs: plot precision of “same intent / same gold answer” vs threshold; pick operating point. **Tenant-scope** cache keys mandatory.

LiteLLM guidance: prefer semantic cache for **single-shot** traffic; for multi-turn agentic traffic use exact-match — semantic replay can return answers from a different conversation state.

### Alternatives & Tradeoffs
| Cache | Hit rate | Risk | Extra latency |
|-------|----------|------|---------------|
| Exact | Low–medium | Low | Minimal |
| Semantic | Higher on FAQ | Stale / wrong-intent | Embed cost every request |
| Prompt/KV cache (provider) | Reuses prefix compute | Provider-specific | None to app if hit |
| No cache | Zero risk | Max $ | — |

Never cache authorized, personalized, or post-tool-mutation answers without including authz context in the key.

### Necessity
Skipping cache leaves easy money on the table for support bots. Uncalibrated semantic cache creates **confident wrong** replies that eval suites may not catch if they only test exact prompts. Cross-tenant semantic hits are a data-leak bug.

### Industry Practice
**Common:** Redis exact cache on temperature 0 endpoints.  
**Strong:** separate caches per task type; TTL by content volatility; store model ID + prompt version in key; dashboards for hit rate, embedding latency, similarity of hits; kill switch; exclude PII-heavy traffic; bypass cache when tools already mutated state.

### Concrete Scenario
LiteLLM caching docs (exact + semantic, similarity threshold, agentic warning):  
https://docs.litellm.ai/docs/proxy/caching  
https://docs.litellm.ai/docs/caching/all_caches

### Open Questions
- Can learned routers and semantic caches share the same embedding space?
- Legal status of caching customer prompts in EU residency setups?
- Optimal similarity metric beyond cosine for short noisy queries?

### Sources
- https://docs.litellm.ai/docs/proxy/caching
- https://docs.litellm.ai/docs/caching/all_caches
- https://docs.litellm.ai/docs/completion/prompt_caching

---

## Concept: Prompt caching mechanics, prompt compression, and batching

### Fundamentals

**Provider prompt caching (KV / prefix cache):**
- Reuse computation for long identical prefixes (system prompt, tools, large docs).
- **Anthropic:** explicit `cache_control` breakpoints (automatic or per-block); billed distinct rates for cache write vs cache read; minimum token thresholds apply; see current docs for TTL (`ephemeral`) and limits:  
  https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- **OpenAI:** largely automatic for long prompts; optional `prompt_cache_key` / retention hints in newer APIs; check usage for `cached_tokens`.
- **LiteLLM:** normalizes caching usage across providers:  
  https://docs.litellm.ai/docs/completion/prompt_caching

Design prompts **prefix-stable**: put static instructions + tools + large corpus chunks first; variable user query last — otherwise you break the prefix and lose hits.

**Prompt compression:** shorten context before send (LLMLingua-style, summarization, drop low-retrieval chunks). Trades quality risk for $ / latency. Prefer better retrieval over aggressive compression when quality-sensitive.

**Batching:**
- **Server-side continuous batching** (vLLM etc.) for self-hosted inference — throughput win.
- **Provider batch APIs** (async, cheaper, higher latency) for offline eval / enrichment.
- **Client micro-batching** of embeddings — careful with latency SLOs.

### Alternatives & Tradeoffs
| Technique | Saves | Risks |
|-----------|-------|-------|
| Prompt caching | Input token $ + TTFT on hits | Prefix discipline; cache miss cliffs |
| Semantic response cache | Full output $ | Wrong hit |
| Compression | Input tokens | Lost details / citations |
| Batch API | $/throughput | Hours of lag; not interactive |
| Smaller model | Everywhere | Capability |

### Necessity
RAG systems with 50k-token system+tools payloads that do *not* use prompt caching hemorrhage money. Unstable JSON tool schemas between calls destroy cache hit rates. Synchronous batching in a user-facing path destroys latency SLOs.

### Industry Practice
**Common:** turn on Anthropic cache_control on large system prompts.  
**Strong:** monitor `cache_read` vs `cache_write` ratios; structure templates for hit rate; separate “static tool schema” versioning; use Batch API for nightly corpus tagging; compression only behind quality gates; budget alerts on cache miss regressions after prompt edits.

### Concrete Scenario
Anthropic prompt caching documentation (mechanics, breakpoints, usage fields):  
https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  

OpenAI prompt caching docs (verify current API names):  
https://platform.openai.com/docs/guides/prompt-caching  

LiteLLM cross-provider prompt caching:  
https://docs.litellm.ai/docs/completion/prompt_caching

### Open Questions
- How do prompt caches interact with ZDR / residency contracts?
- Is compression still worth it as context windows get cheaper?
- Should agent transcripts be cached as prefixes across turns automatically (Anthropic automatic caching) vs explicit breakpoints?

### Sources
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- https://platform.openai.com/docs/guides/prompt-caching
- https://docs.litellm.ai/docs/completion/prompt_caching
- https://docs.vllm.ai/en/latest/ (continuous batching / serving — self-hosted)

---

## Concept: Cost-attribution dashboards

### Fundamentals
If you cannot answer **“which tenant, feature, model, and prompt version spent $X yesterday?”** you cannot optimize or invoice.

Minimum attribution dimensions (labels/tags on every LLM call):

- `tenant_id` / `customer_id`
- `product_surface` / `endpoint` / `agent_name`
- `model` / `provider`
- `prompt_version` / `router_decision` / `cache_hit` (exact|semantic|prompt|none)
- `environment` (dev/staging/prod)
- tokens: input, output, cache_read, cache_write
- latency: TTFT, total
- outcome: success, user_feedback, eval_score (sampled)

Implement via gateway (LiteLLM spend logs / budgets), OpenTelemetry spans + metrics, or warehouse ETL from provider usage exports. Join to product analytics for **cost per successful task**, not just cost per call.

### Alternatives & Tradeoffs
| Approach | Pros | Cons |
|----------|------|------|
| Provider console only | Free | No tenant/feature split |
| Gateway virtual keys per tenant | Natural spend walls | Coarse if one key many features |
| Span attributes → metrics | Flexible | High cardinality pitfalls |
| FinOps warehouse (Snowflake/BQ) | Rich joins | Lag; engineering cost |

Cardinality warning: do not label metrics with raw `user_id` × `prompt_hash` unbounded — use exemplars/traces for drill-down.

### Necessity
Without attribution, routing and caching wins are anecdotal. Without budgets/hard limits per tenant, one scraper customer exhausts the org’s OpenAI bill. Without linking cost to quality, teams cut the wrong model.

### Industry Practice
**Common:** monthly CSV from provider; spreadsheet by key.  
**Strong:** real-time gateway dashboards; per-tenant soft/hard budget; anomaly detection (spend z-score); weekly FinOps review tied to router thresholds; chargeback to internal LOBs; cost of eval traffic tracked separately from production.

### Concrete Scenario
LiteLLM budgets / spend tracking / virtual keys (gateway-level attribution):  
https://docs.litellm.ai/docs/proxy/cost_tracking  
https://docs.litellm.ai/docs/proxy/users  

AWS GenAI Lens multi-tenant scenario calls out usage analytics and cost tracking as first-class:  
https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html

### Open Questions
- Who owns the cost dashboard — platform eng, FinOps, or each product squad?
- How to attribute shared cascade costs (weak attempt + strong escalate) to features fairly?
- Should semantic cache hits “credit” the team that paid for the original generation?

### Sources
- https://docs.litellm.ai/docs/proxy/cost_tracking
- https://docs.litellm.ai/docs/proxy/users
- https://docs.litellm.ai/docs/proxy/virtual_keys
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html
- https://opentelemetry.io/docs/

---

## Week 20 synthesis notes (for later curriculum writing)

- FDE bar: sketch a router with &lt;1 ms rules + optional embed/classifier; cite RouteLLM-style 95%@~15% strong; calibrate semantic threshold; enable Anthropic prompt caching with prefix-stable templates; show a cost cube by tenant×model×feature.
- Pair with Week 18 (HPA on gateway concurrency) and Week 19 (per-tenant virtual keys + residency-aware provider routing).
