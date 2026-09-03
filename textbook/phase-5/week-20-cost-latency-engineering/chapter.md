# Chapter 20 — Cost and latency engineering

> **Phase 5 — Production, Cost, and Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-5/week-20-cost-latency-engineering/`  
> **Syllabus Build:** You already have a **containerized, OIDC-gated, tenant-isolated LLM service** (Weeks 18–19). This week you **stop sending every request to the frontier model**. (1) **Route before you generate.** Rules first (&lt;1 ms): path, tier, `task_type`, tools, length. Uncertain traffic → embedding (~5 ms) or a trained classifier (50–100 ms). Never put an LLM-as-router on the hot path unless you measured that it still saves money. (2) **Calibrate a cascade, do not guess a percentage.** Plot quality vs % strong-model calls on *your* golden set. The RouteLLM public headline is **~95% of GPT-4 quality at ~14% GPT-4 calls on MT Bench** (matrix factorization + LLM-judge augmentation). Your production mix will differ; the *shape* of the curve is the deliverable. (3) **Cache in two layers.** Exact-match (hash) for deterministic FAQ; semantic (embedding + threshold) for paraphrases — **tenant in the key**, **off for agentic multi-turn**. Provider **prompt caching** for long static prefixes (system + tools + corpus). (4) **Structure prompts for prefix hits.** Static first, user query last. Monitor `cache_read` vs `cache_write`. Compression and Batch APIs are for the paths that cannot be prefix-cached or are offline. (5) **Attribute every dollar.** Gateway tags: tenant, feature, model, prompt version, router decision, cache class. Cost per **successful task**, not only cost per call. Hard budgets per tenant (Week 19 virtual keys).

---

## Chapter framing

Week 20 is the **which model, cache, and dollar** week of Phase 5. Week 19 shipped **who may call the gateway** and **where tenant data may live**. The typical remaining failure is economic: every authenticated request still hits the frontier model, semantic cache is off or global, and Finance sees one provider invoice.

This week answers five questions that unit economics, support-bot SLOs, and FDE interview whiteboards all treat as the minimum bar for an engineer who can land a production LLM product at scale:

1. **Which model should this request use?** (rule / embedding / classifier routing)  
2. **When is the expensive model worth it?** (cascading / RouteLLM-style selective routing)  
3. **Do we need a model at all?** (exact and semantic response caches)  
4. **If we generate, can we reuse prefix compute or shorten/batch work?** (prompt cache, compression, batching)  
5. **Who spent the money?** (tenant × feature × model attribution dashboards)

**Do not start Week 21 (legacy / messy integration) from this chapter** — this week ships **model routing**, **RouteLLM-style cascading**, **semantic caching**, **prompt cache + compression + batching**, and **cost-attribution dashboards**. Week 19 already isolated tenants and virtual keys; honor tenant/region in the router and keep caches tenant-keyed. HPA on gateway concurrency (Week 18) is a *capacity* lever, not a substitute for routing provider dollars. Eval flywheels (Weeks 16–17) appear here only as a dashboard dimension. Idempotency appears only as “don’t cache mutating tool results”; dual-write / ETL is Week 21.

**Design: router + cache in front of the LLM**

Router latencies below are for the **decision**, not LLM time-to-first-token:

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

LiteLLM’s **Router** is mostly **load-balancing and failover** across deployments of the *same* logical model (`simple-shuffle`, least-busy, latency-based, cost-based). RouteLLM is a **quality router** between a **strong expensive** and **weak cheap** model. Production gateways need **both**: pick capability tier, then pick a healthy deployment in that tier (and pin deployment when prompt-cache affinity matters).

**RouteLLM operating point you must be able to cite:** Ong et al. (2024), GPT-4 Turbo vs Mixtral 8x7B. On **MT Bench**, matrix factorization trained on Chatbot Arena **plus LLM-judge augmentation** reached **95% of GPT-4’s score with 14% of calls to GPT-4** (~85% cost reduction vs all-GPT-4; ~75% cheaper than a random router at the same quality point). Without augmentation, MF still hit 95% at **~26%** GPT-4 calls. On **MMLU** / **GSM8K**, cost cuts at 95% quality were smaller (~45% / ~35% vs all-GPT-4 in the LMSYS blog). Domain shift is the lesson: Arena-trained routers need **in-domain augmentation**. FDE translation: **design for ~10–20% frontier traffic** *if* you plot the curve on *your* traces. Do not put “15%” in an SLA.

**Cost-per-request before / after (spreadsheet shape)**

Prices move; use this as an **index**, then plug live list prices. Illustrative 2024-era **per-request** averages for a 2k-in / 400-out support turn (not a quote):

| Arm | Relative $ / request (index) |
|-----|------------------------------|
| Strong (frontier) | **100** |
| Weak (small / Mixtral-class API) | **5** |
| Semantic cache hit (embed + Redis) | **1** |
| Exact cache hit | **~0.1** |

| Scenario | Cost index | Notes |
|----------|------------|-------|
| **Before** — 100% strong | **100** | Quality = 100% of frontier by construction |
| **After A** — 14% strong / 86% weak (MT Bench 95% point) | **18.3** | ~82% $ reduction; your MMLU-like traffic will not get this |
| **After B** — same router + 30% semantic hits on LLM-bound traffic | **~13.1** | ~87% reduction; quality depends on **wrong-hit rate** |
| **After C** — add prompt caching on remaining LLM calls | Multiplies prefix savings | Track `cache_read` / `cached_tokens` or you never know |

**What to put on the interview whiteboard:** before = all-frontier $/request from a week of prod traces; after = the same traces **replayed** through the router (shadow) + cache hit log; quality = golden-set score and CSAT by route arm. If you only have public benches, say so and cite RouteLLM’s **14% / 95%** as the *existence proof*, not your SLA.

**Default path (synthesis)**

1. **Rules are free; classifiers are not.** Spend 50–100 ms only when the LLM call is seconds.  
2. **~15% / ~95% is a calibrated point, not a law.** MT Bench + Mixtral/GPT-4 Turbo + MF + judge data. MMLU/GSM8K savings were smaller.  
3. **Semantic cache is a product decision.** Uncalibrated cosine ≈ silent wrong answers. Agentic traffic → exact-match only.  
4. **Prompt cache is prefix discipline.** Anthropic `cache_control`; OpenAI automatic + `prompt_cache_key`.  
5. **If you cannot name the tenant and feature on yesterday’s spend, you cannot optimize.**  
6. **Self-hosted throughput ≠ interactive latency.** Continuous batching / PagedAttention for GPU utilization.

Interview artifact = **router decision tree with latency budgets** + **quality-vs-%-strong curve** (or RouteLLM-cited operating point plus “we would re-benchmark”) + **cost cube sketch** (tenant × model × feature) + **before/after $/request**.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) after Weeks 18–19 — now deciding **which model, cache, and dollar** each request consumes.

---

### Model routing (rule / embedding / classifier)

* **Fundamentals:**  
  **Model routing** is a pre-call policy: given a request, pick a **model ID (or tier)** so easy work is cheap/fast and hard work is expensive/capable. If you pick *after* generating with the expensive model, you already paid.

  Three engineering families. Latencies are **order-of-magnitude guidance for the router decision**, not the LLM:

  | Router type | Typical decision latency | Mechanism |
  |-------------|--------------------------|-----------|
  | **Rule-based** | **&lt;1 ms** | If/else on metadata: HTTP path, tenant plan, prompt token length, presence of tools, language, `task_type` header, regex/keyword, time-of-day, eval-canary flag |
  | **Embedding-based** | **~5 ms** (local/small embed; remote embed adds RTT) | Embed query (sometimes full `messages`); nearest-neighbor to labeled prototypes / clusters (“password reset” → Haiku) |
  | **ML classifier** | **~50–100 ms** (BERT-base class); **higher** if causal-LLM router or remote GPU queue | Trained to predict whether strong beats weak (RouteLLM `bert`, `causal_llm`) or a discrete complexity class |

  **Composition:** evaluate rules first (CPU, no model). If the request is in a **must-strong** set (legal, medical, named customer tier, tool-using refund), skip the learned router. If it is **must-cheap** (translation of UI strings, embed-only), skip frontier. Remaining mass goes to embed or classifier. Cascade the *routers* the same way you cascade *models*: rules → light embed → heavy classifier. A 100 ms BERT in front of a 2 s Sonnet call is noise. A 100 ms BERT in front of a 150 ms classifier model **is** the latency budget.

  RouteLLM’s four *learned* routers (preference data from Chatbot Arena ± augmentation):

  | Name | Idea | Serving cost |
  |------|------|----------------|
  | `sw_ranking` | Similarity-weighted Elo over past votes vs the new prompt | Needs embeddings + retrieval over vote set |
  | `mf` | Matrix factorization: bilinear score δ(model, query); **recommended default** in the repo | Embed query (`text-embedding-3-small` in the paper setup) + tiny MF |
  | `bert` | BERT-base classifier: P(strong better \| query) | Full BERT forward ~ tens of ms on CPU/GPU |
  | `causal_llm` | Causal LM classifier | Largest router; often not worth the router bill |

  Paper training detail: MF and SW ranking embed with OpenAI `text-embedding-3-small`; BERT and causal LLM are fully finetuned. That means **`mf`/`sw` inherit embedding latency (~5 ms local, more if you call a hosted embed API on the hot path)**. Do not advertise “MF is free.”

  **LiteLLM Router** answers a different question: given *one* `model_name` alias with **multiple deployments** (Azure east vs west, two API keys), which **endpoint** should get the call? Strategies: **simple-shuffle** (default, rpm/tpm/weight — recommended for production latency overhead), least-busy, latency-based, usage/rate-limit aware, lowest-cost. Use it **after** the quality router has chosen `haiku` vs `sonnet`. Also: retries, fallbacks, cooldown. LiteLLM **Auto Router** (complexity / semantic flavors in later docs) is closer to quality routing; treat vendor docs as evolving — `[NEEDS MORE RESEARCH]` for current Auto Router field names before a live lecture.

  **LLM-as-router:** send the user prompt to a cheap model with “reply WEAK or STRONG.” Flexible, language-native, and often **more expensive than the savings** plus extra TTFT. Use for offline labeling / augmentation (RouteLLM’s judge data), not as the default online router.

  **Multi-model (&gt;2):** pairwise strong/weak (RouteLLM) vs a taxonomy (`embed`, `classify`, `reason`, `code`). Taxonomy matches product endpoints; pairwise matches preference data. Hybrids: rules map to a pair, then MF inside the pair.

  **Latency budget rule:** router_ms ≪ expected_TTFT. Chat UIs: router adds to **time-to-first-token**. Speculative decoding and 100 ms SLOs make BERT routers look expensive — then **rules + local embed** win. **Shadow routing:** log `would_have_routed` without steering. Compare quality and $ for two weeks before flipping the flag.

* **The Alternatives:**  

  | Approach | Cost-save potential | Failure mode | Decision latency |
  |----------|---------------------|--------------|------------------|
  | Always frontier | Zero | Budget blowups | 0 |
  | Always small | Max | Silent quality regressions | 0 |
  | Rules only | Medium; **predictable** | Brittle; **hard short** prompts (“prove this lemma”) look cheap | **&lt;1 ms** |
  | Embedding similarity | Good for **known intents** | Threshold miss → wrong cluster; embed outage | **~5 ms** + timeout policy |
  | Learned router (preferences) | High when in-domain | OOD ≈ random; needs monitoring | MF/SW: embed; BERT: **50–100 ms** |
  | LLM-as-router | Situational | Router tokens dominate | 200 ms–2 s |
  | LiteLLM cost-based shuffle | Saves among **equivalent** deployments | Will not send hard math to a weak *model* | Sub-ms plus health checks |
  | Percentage canary | Useful for **rollout**, not optimization | Ignores query difficulty | 0 |

  The syllabus selects **rules first, then optional embed/classifier** because router decision latency must stay under the generation budget, and must-strong / must-cheap cases do not need a learned model. Prefer: rules trichotomy → local embed or RouteLLM `mf` on the uncertain mass → LiteLLM load-balancing *within* the chosen tier.

* **Failure Modes:**  
  - High-volume RAG/support unit economics die when every call is frontier.  
  - Teams celebrate “−40% spend” while CSAT and golden-set scores collapse on the weak arm — no eval harness on the router.  
  - No fallback when the weak model fails a confidence / verifier / user-retry check; users see a bad answer with no recovery.  
  - Feature flags absent on model IDs: a one-line prompt change plus silent model deprecation becomes an incident.  
  - OOD traffic (Arena-trained router on MMLU-like work) behaves like random routing.  
  - LLM-as-router on the hot path: router bill exceeds savings; TTFT spikes.

* **Average vs. Strong Engineer:**  
  **Average:** `MODEL_CHAT=claude-sonnet-…` in env; `/embed` always small; LiteLLM `simple-shuffle` across two Azure deployments of the same GPT; no quality router.  
  **Strong:** **Must-strong / must-weak / learn** trichotomy in rules; local embedding model (or gateway embed with tight timeout) for both intent routing and semantic cache — **same model version** if you share space; RouteLLM `mf` or an in-house BERT with **your** preference labels (thumbs, LLM-judge on traces); online metrics: **escalate-rate**, thumbs-down **by route arm**, p95 TTFT **including router**, spend per arm; retrain/calibrate when the **model pair** changes; LiteLLM spend limits and fallbacks **per virtual key** so a bad router cannot drain one tenant. RouteLLM reports **some** zero-shot pair transfer (Claude 3 Opus / Llama 3 8B without retraining on those responses) — **verify on your golden set**.

* **Worked Example:**  
  Deployment Copilot’s gateway after Week 19 has virtual keys per tenant. Path `/classify-intent` is rule-forced to a small model (&lt;1 ms). Remaining chat: rules mark `must-strong` for tool-using refund and premium-tier tenants; FAQ-shaped paths are `must-cheap`. Uncertain chat goes through RouteLLM `mf` (or a BERT router hosted next to the gateway). LiteLLM then `simple-shuffle`s across healthy Azure deployments of the *chosen* model. Shadow mode logs `would_have_routed` for two weeks before the feature flag steers traffic. Online panels show spend and thumbs-down **by arm**.

* **Apply It:**  
  1. Write the must-strong / must-weak / learn rule table for every product surface.  
  2. Budget router latency: rules &lt;1 ms always; embed ~5 ms; BERT only if generation is seconds.  
  3. Separate **quality** routing (tier) from LiteLLM **deployment** routing (shuffle / least-busy / cost).  
  4. Enable shadow routing; compare quality and $ before cutover.  
  5. Instrument escalate-rate, thumbs by arm, p95 TTFT including router_ms.  
  6. Ban LLM-as-router on the hot path unless measured savings remain positive.

---

### Model cascading and RouteLLM (~15% / ~95%)

* **Fundamentals:**  
  **Cascading / selective routing** sends a query to a **strong expensive** model only when a **weak cheap** model is predicted to lose. RouteLLM (Ong, Almahairi, et al., 2024) formalizes two-model routing from **preference data** (Chatbot Arena votes + optional gold or LLM-judge augmentation) and releases serving + eval code.

  **Route-once (RouteLLM default):** one router decision → **one** LLM call. The paper argues this matches an “ideal” router: quality without the extra latency of multi-LLM methods (LLM-Blender ensembles, FrugalGPT sequential cascade, AutoMix self-verify-then-escalate).

  **Headline numbers (GPT-4 Turbo strong / Mixtral 8x7B weak — LMSYS blog + paper):**

  | Setting | Quality target | Strong-model call share | Notes |
  |---------|----------------|-------------------------|--------|
  | MT Bench, MF, Arena **+ LLM judge** | **95% of GPT-4** | **~14%** GPT-4 calls | Blog: ~85% $ cut vs all-GPT-4; **~75% cheaper than random** at that quality |
  | MT Bench, MF, Arena **only** | 95% of GPT-4 | **~26%** GPT-4 calls | ~48% cheaper than random at that point |
  | MMLU, Arena only | — | ~random | OOD vs Arena chat |
  | MMLU, Arena + **gold** val split (~1500 samples, &lt;2% of train) | 95% of GPT-4 | **~54%** GPT-4 (causal LLM best in blog narrative) | ~45% $ cut vs all-GPT-4 (blog) |
  | GSM8K | 95% of GPT-4 | higher than MT Bench | Blog: ~35% $ cut vs all-GPT-4 |

  **FDE mnemonic:** **~15% expensive / ~95% quality** refers to the **MT Bench + MF + judge-augmented** operating point (~14%, rounded). It is **not** universal. Put the **curve** (quality vs % strong) in the design doc.

  **Cost threshold:** RouteLLM exposes a threshold that trades more weak traffic vs more strong. Production: sweep threshold on a **held-out golden set**; pick the point on the Pareto front that hits the product SLO.

  **Deferred cascade (not RouteLLM’s main eval):** try weak → **quality/confidence check** → escalate to strong. Higher safety; **adds a full generation** (and TTFT) on hard queries. FrugalGPT (Chen et al., 2023) is the classic **LLM cascade**: sequentially query APIs until a reliability score is met; reported **50–98%** cost cut vs the best single API **on their tasks**, or **+4%** accuracy at same cost. Different methodology than RouteLLM; do not mix the percentages in one sentence without labeling.

  **Commercial snapshot (blog Figure 6):** open routers matched Martian / Unify quality points at **&gt;40% cheaper** on their MT Bench setup (GPT-4 Turbo + Llama-2-70B or Mixtral). Treat as **2024 research snapshot**; re-benchmark. **Zero-shot pair transfer:** same routers, no retraining, Claude 3 Opus vs Llama 3 8B on MT Bench — blog reports strong results. Still **re-validate** when you change providers.

  **Judge-in-the-loop escalation:** an LLM-as-judge on every weak answer can **eat the savings**. Use cheap heuristics first (logprob, length, “I don’t know”, schema fail), sample judge, or escalate on user retry. **Tool-using agents:** cascading **per step** vs **per session**. Per-step saves $ on easy lookups; per-session avoids mixing model families in one transcript. LiteLLM documents that **session_affinity** is off by default for cost routing, and that returning to a model often still finds a **warm prompt cache**.

* **The Alternatives:**  

  | Design | Quality control | Latency | $ |
  |--------|-----------------|---------|---|
  | **Route-once (RouteLLM)** | Router calibration + golden set | +router only | Best when router is accurate |
  | Try-weak-then-escalate (FrugalGPT / AutoMix-like) | Verifier / judge / self-check | **2× generation** on escalations | Pays weak **and** strong on hard tail |
  | Speculative parallel (race small+large) | Fast when small would have won | Always pay **both** unless you cancel | Worst $ ; best p50 latency |
  | Random / % canary | None | 0 | RouteLLM baseline |
  | Always-strong for “premium” SKU | Contractual | 0 extra | Simple packaging |
  | Ensemble / LLM-Blender | High | Multi-call | Usually loses the cost plot |

  The syllabus selects **route-once with a calibrated curve** as the default interview design, with deferred escalate as a safety overlay for high-risk intents. Prefer: plot quality vs % strong on *your* golden set; cite RouteLLM’s 14%/95% as existence proof; do not put that percentage in a customer SLA.

* **Failure Modes:**  
  - All-frontier default does not survive scale; naive “mini everywhere” fails on hard reasoning and on **trust**.  
  - Cascading **without** an offline curve means the threshold is folklore — Finance picks 5% strong; Support picks 80%.  
  - Citing **95%@15%** in a customer SLA creates a **legal metric** you cannot operationalize (which bench? which judge? which week’s models?).  
  - When the **model pair** changes, the curve moves and nobody budgets a recalibration sprint.  
  - Judge-on-every-weak-answer eats the Mixtral savings.  
  - Mixing FrugalGPT’s 50–98% with RouteLLM’s 14%/95% in one sentence without labeling methodologies.

* **Average vs. Strong Engineer:**  
  **Average:** two model IDs in config + a **manual percentage** (`STRONG_PCT=0.2`) that is not query-aware.  
  **Strong:** Weekly plot: x = % strong calls, y = quality (judge or gold), with **random** and **all-strong** reference lines (RouteLLM Figure 2 style); auto-tune threshold under a **min quality** constraint; SKUs: `premium` force-strong, `balanced` routed, `economy` weak+cache only; log **router score**, chosen arm, tokens, $, user feedback; shadow mode before cutover; separate **eval traffic** so the cascade is not trained on its own production hacks; when using LiteLLM load balancing **and** Anthropic prompt cache, pin **deployment** after first cache write (`prompt_caching` pre-call check).

* **Worked Example:**  
  Reproduce the public point, then distrust it. Run RouteLLM eval comparing `random`, `mf`, `bert` on `mt-bench` with Arena+judge training; record the 95%-quality call fraction. Then **replay 500 labeled Deployment Copilot tickets** and draw the same axes. If in-domain data is tiny, RouteLLM’s lesson is **augment** (gold or judge) rather than ship Arena weights blindly — MMLU was random until ~1500 in-domain labels. Productize `premium` (always strong) vs `balanced` (routed at the calibrated threshold). Cost index for After A from the chapter framing: `0.14×100 + 0.86×5 = 18.3`.

* **Apply It:**  
  1. Plot quality vs % strong on a frozen golden set; include random and all-strong baselines.  
  2. Sweep the RouteLLM (or in-house) threshold; pick the Pareto point that hits your SLO.  
  3. Cite ~14%/95% only as the MT Bench MF+judge public point — never as an SLA.  
  4. Shadow-route before cutover; log router score and arm.  
  5. Recalibrate when the strong/weak pair or prompt version changes.  
  6. Prefer cheap escalate heuristics before an always-on LLM judge.

---

### Semantic caching (exact vs semantic)

* **Fundamentals:**  
  Two **response caches** (store **outputs**, not KV tensors):

  **Exact-match cache.** Hash the full request that affects generation: model (or routed model), `messages`, tools, temperature, seed, response format, **tenant_id**, prompt version. Store in Redis/disk/S3. Hit only on identical prompts. Lookup is sub-ms after the hash. Safe for **temperature=0** FAQ and idempotent classify endpoints.

  LiteLLM exact cache types: in-memory, disk, Redis, Valkey, S3, GCS. Dynamic per-request controls: `ttl`, `s-maxage`, `no-cache`, `no-store`, `namespace`. Response header `x-litellm-cache-key` on hits. `/cache/ping`, `/cache/delete` for ops.

  **Semantic cache.** Embed the prompt (LiteLLM: **entire `messages` array**, system included). Return the nearest prior **response** if cosine similarity ≥ `similarity_threshold`. Hits paraphrases (“reset password” ≈ “how do I change my pwd?”). Backends: **Redis semantic**, **Qdrant semantic**, **Valkey semantic**.

  **Inline embedding tax:** LiteLLM runs the embedding **before** the LLM; default cap **5 seconds**. On timeout: miss, header `x-litellm-semantic-similarity: 0.0`, proceed to the model. Tune `semantic_cache_embedding_timeout` / `SEMANTIC_CACHE_EMBEDDING_TIMEOUT_SECONDS`. A hanging embedder therefore adds seconds to **every** request — budget this like a router.

  **Threshold calibration.** Too low (e.g. 0.7) → **wrong-answer reuse** (silent corruption). Too high (e.g. 0.98) → few hits (you paid for embeddings and got nothing). Procedure: (1) Build labeled pairs: paraphrase / same intent / **same gold answer** vs similar-but-different (refund vs cancel). (2) Plot **precision of “safe to reuse”** vs threshold; optionally recall (hit rate). (3) Pick operating point from product risk (support macros: high precision; trivia: looser). (4) Re-calibrate when embedding **model** or prompt **template** changes.

  **Tenant-scope is not optional.** Cache key / vector filter **must** include `tenant_id` (and often `user_id` if answers are personalized). Cross-tenant semantic hit = data leak. Week 19 PEP applies to Redis as much as Postgres.

  **Agentic / multi-turn (LiteLLM explicit warning).** Consecutive agent turns are previous messages **plus a small delta**; embeddings sit at **~0.99**. Any practical τ replays the **previous turn’s** reply → repeated **tool calls**. Raising τ does not reliably fix it. `tool_calls` are **not** in the embedded text, so the cache cannot see “we already called `create_ticket`.” **Recommendation:** semantic cache for **single-shot**; exact-match (full-request hash) for agents. Mitigations: virtual-key `metadata.cache.no-cache`, `mode: default_off` + opt-in, or per-request `no-cache`. Anthropic `/v1/messages` and passthrough routes **skip** LiteLLM response cache entirely.

  **Never cache** authorized, personalized, or **post-mutation** answers without authz context in the key (and usually `no-store` after tools that changed CRM state). Usually **include model ID** in the key (Haiku wording ≠ Sonnet). Shared embedding model with an embedding **router** is attractive but conflates “similar question” with “similar difficulty.”

* **The Alternatives:**  

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

  The syllabus selects **exact-match for deterministic and agentic paths; calibrated semantic for single-shot FAQ**, always tenant-scoped. Prefer: calibrate τ on labeled pairs; kill switch; never global namespace.

* **Failure Modes:**  
  - Skipping cache leaves easy money on support bots with repeated intents.  
  - Uncalibrated semantic cache creates **confident wrong** replies; exact-prompt eval suites never paraphrase and will not catch this.  
  - Global (no tenant) semantic cache is a **SEV-0 class leak**.  
  - Semantic cache on a **coding agent** looks like a “stuck loop” bug and will be mis-attributed to the model.  
  - Embed timeout without a **miss-and-proceed** policy turns an embed outage into a **full gateway outage**.  
  - Caching post-mutation / personalized answers without authz in the key.

* **Average vs. Strong Engineer:**  
  **Average:** Redis exact cache on temperature-0 classify/summarize; semantic off; one global namespace.  
  **Strong:** Separate caches **per task type** (FAQ vs RAG vs agent) with different τ and TTLs; TTL by **content volatility** (tax policy: hours; math identity: days); key includes **model ID + prompt version + tenant**; dashboards: hit rate, embed latency, similarity **of accepted hits**, wrong-hit rate from sampled review; kill switch (`mode: default_off` or key `no-cache`); exclude PII-heavy traffic; bypass when tools already mutated state; `/cache/ping` in readiness (Week 18 `/ready` should not require cache for liveness, but degraded mode should be visible). Virtual-key auth cache (`enable_redis_auth_cache`) is **not** a response cache — do not confuse the two LiteLLM Redis uses.

* **Worked Example:**  
  Deployment Copilot FAQ paraphrases: 1,000 labeled pairs. At τ=0.92, precision 99%, hit rate 18%. At τ=0.80, precision 91%, hit rate 41%. Legal/refund intents stay on exact-match or no-cache. LiteLLM config sketch (field names — verify live):

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

  Tenant id is in the key/filter. Agent tool loops use exact-match only (or `no-cache`). After B in the chapter framing: 30% semantic hits on LLM-bound traffic → cost index ≈ **13.1** vs 100 — but only if wrong-hit rate is measured.

* **Apply It:**  
  1. Exact-match Redis for T=0 FAQ and classify; include tenant + model + prompt version in the hash.  
  2. Build labeled paraphrase pairs; pick τ from precision-vs-threshold, not a blog default.  
  3. Semantic for single-shot only; exact-match or `no-cache` for multi-turn agents.  
  4. Set embed timeout with miss-and-proceed; never let embed hang the gateway.  
  5. Dashboards: hit rate, wrong-hit samples, embed latency; kill switch.  
  6. Never enable a global (cross-tenant) semantic namespace.

---

### Prompt caching, compression, and batching

* **Fundamentals:**  
  Three different “batch/cache/compress” ideas get mixed in slides. Keep them separate:

  | Layer | What is reused | Interactive? |
  |-------|----------------|--------------|
  | **Provider prompt / prefix / KV cache** | Attention state for a **byte-identical prefix** | Yes — faster prefill, cheaper input tokens on hits |
  | **Prompt compression** | Shorter **text** sent to the API | Yes — quality risk |
  | **Continuous batching** (self-hosted) | GPU timesteps across **many users** | Yes — throughput; can add queueing latency |
  | **Provider Batch API** | Offline job discount | **No** — hours of lag |

  **Anthropic prompt caching.** Explicit `cache_control` (`type: ephemeral`). **Automatic** (top-level `cache_control`; breakpoint on last cacheable block, moves as the conversation grows) vs **explicit** breakpoints on blocks (up to **4**; automatic uses one slot). Prefix order: **`tools` → `system` → `messages`**. Writes happen **at breakpoints**; reads look back (on the order of **20 blocks**) for a prior write — a breakpoint on a **changing** suffix (timestamps) never hits. Default TTL **5 minutes**, refreshed on hit; **1-hour** TTL exists at higher **write** price. Pricing pattern (confirm live — prices move): 5-minute **writes ~1.25×** base input; **1h writes ~2×**; **reads ~0.1×** (90% off). Minimum tokens: **1,024** for many Sonnet-class models; **4,096** for some Opus/Haiku SKUs — below min, no error, usage shows zeros. Usage fields: `cache_creation_input_tokens`, `cache_read_input_tokens`. Cookbook: latency **&gt;2×** better and cost **up to 90%** on repetitive tasks. **Design rule:** put **static** instructions, tools, and large corpus chunks **first**; **variable user query last**. Unstable JSON tool schemas between calls destroy hit rates.

  **OpenAI prompt caching.** Automatic for long prompts (classic: **≥1,024 tokens**, longest prefix match in **128-token** increments). `usage.prompt_tokens_details.cached_tokens` (Responses API: `input_tokens_details`). Caches typically **5–10 min** idle, gone within ~**1 hour**; **not shared across organizations**; eligible for ZDR narratives in OpenAI’s materials — **still read the current DPA**. Optional `prompt_cache_key` improves **routing stickiness** to the machine holding KV (cookbook: coding customer **60% → 87%** hits). Newer GPT-5.6+ families add explicit breakpoints / `prompt_cache_retention` (`in_memory` vs `24h`) — LiteLLM passes these through; **`[NEEDS MORE RESEARCH]`** for current API field names before teaching a live lecture (re-fetch OpenAI docs).

  **LiteLLM.** Normalizes cache usage across providers; `completion_cost()` includes cache-hit pricing. Load-balanced Claude: `router_settings.optional_pre_call_checks: [prompt_caching]` so the **second** turn hits the **same deployment/account** that wrote the cache. `cache_control_injection_points` can stamp system/trailing turns for clients that never set `cache_control`. **Gemini / Vertex:** separate `cachedContents` APIs; min tokens (LiteLLM notes **1024**); do not assume Anthropic breakpoint semantics.

  **Prompt compression.** Shorten context **before** send. **LLMLingua** (Microsoft): small LM perplexity → drop low-information tokens; claimed **up to ~20×** with modest quality loss on their suites; compressed text is **ugly for humans**, OK for models. **LongLLMLingua** for query-aware RAG compression. **LLMLingua-2**: BERT-sized keep/drop classifier, faster. **Prefer better retrieval / rerank (Phase 2)** over aggressive compression when citations matter. Compression **fights prompt caching** if it **permutes** a previously stable prefix — compress the **volatile retrieved docs**, not the static system prompt.

  **Batching.** **vLLM continuous batching + PagedAttention:** scheduler admits/retires sequences **per token step**, not per whole batch. PagedAttention stores KV in **blocks** (OS paging analogy) → less fragmentation, larger batches, **2–4×** throughput vs prior SOTA in the SOSP paper; blog claimed up to **24×** vs HF Transformers in early serving numbers. This is **self-hosted GPU $**, not provider invoice line items. Interactive SLOs: large batches can **hurt TTFT** if prefill is not isolated (chunked prefill / separate prefill workers — follow current vLLM docs). **Provider Batch APIs:** async, typically **~50%** off (OpenAI Batch is the usual citation). For **offline** eval, embeddings backfill, nightly tagging. **Never** on the user chat path. **Client micro-batching** of embeddings: higher throughput, worse tail latency; set a max wait (e.g. 5–20 ms) or you miss chat SLOs.

* **The Alternatives:**  

  | Technique | Saves | Risks |
  |-----------|-------|--------|
  | Prompt caching | Input $ + prefill TTFT on hits | Prefix discipline; write premium; TTL; load-balancer splitting the cache |
  | Semantic response cache | **Full** output $ | Wrong hit (semantic caching section) |
  | Compression | Input tokens | Lost details / citations; cache-key churn |
  | Batch API | $/throughput | Hours of lag |
  | Continuous batching | GPU utilization | Queueing; not a provider discount |
  | Smaller model / routing | Everywhere | Capability (routing / cascading sections) |
  | Session affinity for cache | Hit rate | Forfeits down-routing later turns |

  The syllabus selects **prefix-stable prompt caching on interactive paths**, Batch API for offline eval, continuous batching only for self-hosted GPU economics, and compression behind golden-set gates on volatile retrieved context — not the static system prefix.

* **Failure Modes:**  
  - RAG systems with **50k-token** system+tools payloads that do not use prompt caching hemorrhage money every turn.  
  - Unstable tool JSON **between** calls destroys Anthropic/OpenAI prefix hits; you pay **write** rates in a loop.  
  - Synchronous batching on a **user-facing** path destroys latency SLOs.  
  - Compression without a **quality gate** drops the citation the lawyer needed.  
  - Load-balancing Claude **without** prompt-cache affinity doubles cache writes.  
  - “Enable caching” with no `cache_read` / `cached_tokens` dashboard — no proof of ROI.

* **Average vs. Strong Engineer:**  
  **Average:** Anthropic `cache_control` on the large system prompt; OpenAI “it just works” with no `cached_tokens` dashboard; Batch API unused; vLLM default args.  
  **Strong:** Monitor **cache_read vs cache_write** ratios; alert on miss regressions after prompt edits; version **tool schemas** separately and freeze them in the prefix; automatic caching for multi-turn; **explicit** breakpoint at the end of the **static** prefix when the last block is a timestamp or per-request RAG blob; `prompt_cache_key` = hash(tenant + template_version + tool_schema_version) for OpenAI stickiness — **not** raw user_id unbounded cardinality if it fragments the cache; Batch API for nightly corpus tagging and Week 16/17 eval jobs; compression only behind golden-set gates; never compress legal footnotes you must quote; vLLM: measure **tokens/s and TTFT p95**; do not cite 24× as your number; `optional_pre_call_checks: prompt_caching` on load-balanced Claude.

* **Worked Example:**  
  Deployment Copilot’s Sonnet path: tools + system + static policy corpus first (`cache_control` / automatic breakpoint); user ticket text last. After a prompt-template bump, Grafana shows `cache_write` spike and `cache_read` cliff — alert fires; the team froze the tool schema version in the prefix. OpenAI coding surface uses `prompt_cache_key` = hash(tenant + template + tools) and lifts hit rate toward the cookbook’s 60%→87% shape. Nightly golden-set eval jobs go through the Batch API (~50% off), not the interactive path. Self-hosted embed/rerank workers run vLLM with continuous batching; chat TTFT p95 is watched separately from tokens/s. After C in the framing: prompt-cache reads multiply savings on the remaining LLM calls (Anthropic commonly **0.1×** input for reads — **verify live docs**).

* **Apply It:**  
  1. Structure prompts: static tools/system/corpus first; variable user content last.  
  2. Emit and dashboard `cache_read` / `cache_write` (or `cached_tokens`) on every call.  
  3. Pin Claude deployments with LiteLLM `optional_pre_call_checks: [prompt_caching]`.  
  4. Use Batch API only for offline eval / tagging — never chat.  
  5. Compress volatile retrieved docs behind a golden-set gate; do not permute the static prefix.  
  6. For self-hosted: measure tokens/s **and** TTFT p95; isolate prefill if batches hurt interactive latency.

---

### Cost-attribution dashboards

* **Fundamentals:**  
  **Cost attribution** is labeling every LLM (and embedding) call so spend can be sliced. Provider consoles show **API keys and models**, not your product. If you cannot say **which tenant, feature, model, and prompt version spent $X yesterday**, you cannot optimize or invoice.

  **Minimum dimensions** (gateway tags / span attributes on every call):

  | Dimension | Why |
  |-----------|-----|
  | `tenant_id` / `customer_id` | Chargeback; noisy-neighbor; Week 19 isolation |
  | `product_surface` / `endpoint` / `agent_name` | Which feature to fix |
  | `model` / `provider` / `deployment_id` | Routing + prompt-cache affinity |
  | `prompt_version` | Cache-miss cliffs after edits |
  | `router_decision` | strong / weak / rule-forced / shadow |
  | `cache_hit` | `exact` \| `semantic` \| `prompt_read` \| `none` |
  | `environment` | dev / staging / prod / **eval** |
  | Tokens | input, output, **cache_read**, **cache_write** |
  | Latency | TTFT, total, **router_ms**, **embed_ms** |
  | Outcome | success, user_feedback, sampled eval_score |

  **Unit of optimization:** **cost per successful task** (ticket resolved, citation-correct RAG answer), not cost per HTTP 200. Join gateway logs to product analytics.

  **Implementation paths:**  
  1. **LLM gateway** — LiteLLM spend logs, virtual keys, teams, budgets. `completion_cost()` applies the **model cost map**, including **provider cache token** categories. Spend updates are designed to run **after** the response (async) so the DB write is not on the hot path.  
  2. **OpenTelemetry** — spans with the attributes above; metrics with **bounded** cardinality; traces for drill-down.  
  3. **Warehouse ETL** — provider usage exports → BigQuery/Snowflake + dbt. Rich joins, **hours of lag**.

  **LiteLLM specifics FDEs hit:** Track spend at **key / user / team**; end-user `user` field in the body can **mis-attribute** if clients self-declare — set `user_id` on the virtual key and force identity if needed. Default **User-Agent** tag (Claude Code, Gemini CLI, etc.). Virtual keys: model allowlists + **max_budget** / rate limits — the dashboard without a **kill switch** is a report, not a control. Debug cost discrepancies: align time ranges, compare **token categories including cache**, then formula vs model-map.

  **Cardinality:** do **not** put raw `user_id` × `prompt_hash` on **metrics**. Use exemplars/traces. `prompt_version` (semver) is fine; full prompt text is not a Prometheus label.

  **Cascade accounting:** weak attempt + strong escalate = **two** generations, one user-visible answer. Decide: bill the **feature** the sum; show a `cascade_extra_usd` column so routing quality is visible. **Cache credits:** a semantic hit is “free” generation but **used** someone else’s answer — optional credit to originating team; usually skip until chargeback fights start. **Eval vs prod:** Week 16/17 flywheels can dominate spend if judges run on every trace — tag `environment=eval` or a dedicated virtual key.

  AWS **GenAI Lens** multi-tenant scenario treats usage analytics and cost tracking as first-class for a multi-tenant GenAI platform.

* **The Alternatives:**  

  | Approach | Pros | Cons |
  |----------|------|------|
  | Provider console only | Free | No tenant/feature split |
  | Gateway virtual keys per tenant | Natural spend walls | Coarse if one key, many features — add `metadata` tags |
  | Span attributes → metrics | Flexible, real-time | High-cardinality pitfalls; you must maintain the schema |
  | FinOps warehouse | Rich joins, invoices | Lag; engineering cost |
  | Spreadsheet monthly CSV | Honest start | Too late for scrapers |
  | Always-on LLM judge for quality×cost | Causal | Judge $ can dwarf savings |

  The syllabus selects **gateway tags + virtual-key budgets + a real-time cube**, with warehouse ETL as the invoice reconciliation layer. Prefer: cost per successful task; separate eval spend; hard limits that can kill a scraper.

* **Failure Modes:**  
  - Without attribution, routing and caching wins are **anecdotal** (“feels cheaper”).  
  - Without **budgets/hard limits** per tenant, one scraper or leaked virtual key exhausts the **org** provider bill (Week 19 isolation without $ isolation).  
  - Without linking **cost to quality**, teams cut the **wrong** model (the cheap arm that was already failing).  
  - Without **cache_read** in the cube, prompt-caching projects cannot prove ROI and will be reverted after a scary invoice (writes are **premium**).  
  - Without separating **eval** spend, the research org looks like a product outage.  
  - High-cardinality metrics (`user_id` × `prompt_hash`) blow up Prometheus.

* **Average vs. Strong Engineer:**  
  **Average:** monthly invoice; one shared key; “the AI budget”; LiteLLM UI glanced at after an incident.  
  **Strong:** Real-time gateway dashboards (LiteLLM + Grafana/Datadog/Langfuse); per-tenant **soft then hard** budget; webhook / Slack at 70/90/100%; anomaly detection (spend z-score by tenant×surface); weekly FinOps review **tied to router threshold**; chargeback to internal LOBs; cost of **eval** and **shadow routing** tracked separately; canary abort includes **spend spike** (Week 18) — a bad prompt version that doubles output tokens is a deploy incident; document who **owns** the dashboard (platform vs FinOps vs each squad) so it does not rot.

* **Worked Example:**  
  Deployment Copilot interview cube: rows = tenants; columns = (`router=strong`, `router=weak`, `cache=semantic`, `cache=exact`); cell = USD and request count; extra sheet = p95 TTFT. Overlay golden-set score by arm. Before/after from the chapter framing is this cube **summed**. LiteLLM virtual keys enforce `max_budget` per tenant; metadata tags carry `product_surface`, `prompt_version`, `router_decision`, `cache_hit`. Cascade escalations show `cascade_extra_usd`. Eval judges use a dedicated key with `environment=eval`. A prompt-version bump that doubles output tokens trips the Week 18 canary spend abort.

* **Apply It:**  
  1. Tag every call with tenant, surface, model, prompt version, router arm, cache class, environment.  
  2. Dashboard tokens including **cache_read** / **cache_write**; cost per **successful task**.  
  3. Soft then hard budgets per virtual key; alert at 70/90/100%.  
  4. Separate eval and shadow-routing spend from prod.  
  5. Keep metrics cardinality bounded; put high-card fields on traces only.  
  6. Tie weekly FinOps review to the router quality-vs-%-strong curve.

---

## Week 20 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Rules first:** Must-strong / must-weak / learn table with &lt;1 ms decisions on path, tier, `task_type`, tools, length.  
2. **Quality router:** Shadow then steer; embed (~5 ms) or classifier (50–100 ms) only on uncertain mass; LiteLLM load-balance *within* tier.  
3. **Calibrate cascade:** Quality vs % strong on *your* golden set; cite RouteLLM 14%/95% as existence proof, not SLA.  
4. **Response caches:** Exact-match for FAQ/agents; semantic for single-shot paraphrases; **tenant in every key**; calibrate τ; kill switch.  
5. **Prompt cache:** Static prefix first; monitor cache_read vs cache_write; pin Claude deployments for affinity.  
6. **Compression / batch:** Compress volatile retrieval behind gates; Batch API for offline only; vLLM continuous batching for self-hosted GPU $.  
7. **Attribution:** Gateway cube tenant × surface × model × cache/router; hard budgets; cost per successful task; eval spend tagged.

When those seven steps are true, Week 20 is done in the syllabus sense: Deployment Copilot no longer sends every authenticated request to the frontier, and Finance can name which tenant and feature spent yesterday’s dollars.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-5/week-20-cost-latency-engineering/` (`00`–`05`, README).  
- `[NEEDS MORE RESEARCH]` appears where research itself flags evolving vendor surfaces: LiteLLM Auto Router field names, and OpenAI GPT-5.6+ `prompt_cache_retention` / breakpoint API names before a live lecture. Live list prices and Anthropic/OpenAI cache write/read multipliers must be re-fetched before quoting customers (research treats them as patterns, not fixed quotes).  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.
