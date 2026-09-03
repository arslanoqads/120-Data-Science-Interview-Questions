# 01 — Model routing: rule-based, embedding-based, ML classifier

> Week 20 — choosing a model **before** generation.  
> Research notes (raw). Cascading / RouteLLM quality curves are file [02](02-model-cascading-routellm.md). LiteLLM *load-balancing* Router is complementary, not a substitute for a quality router.

---

## Fundamentals

**Model routing** is a pre-call policy: given a request, pick a **model ID (or tier)** so easy work is cheap/fast and hard work is expensive/capable. If you pick *after* generating with the expensive model, you already paid.

Three engineering families. Latencies are **order-of-magnitude guidance for the router decision**, not the LLM:

| Router type | Typical decision latency | Mechanism |
|-------------|--------------------------|-----------|
| **Rule-based** | **&lt;1 ms** | If/else on metadata: HTTP path, tenant plan, prompt token length, presence of tools, language, `task_type` header, regex/keyword, time-of-day, eval-canary flag |
| **Embedding-based** | **~5 ms** (local/small embed; remote embed adds RTT) | Embed query (sometimes full `messages`); nearest-neighbor to labeled prototypes / clusters (“password reset” → Haiku) |
| **ML classifier** | **~50–100 ms** (BERT-base class); **higher** if causal-LLM router or remote GPU queue | Trained to predict whether strong beats weak (RouteLLM `bert`, `causal_llm`) or a discrete complexity class |

**Composition:** evaluate rules first (CPU, no model). If the request is in a **must-strong** set (legal, medical, named customer tier, tool-using refund), skip the learned router. If it is **must-cheap** (translation of UI strings, embed-only), skip frontier. Remaining mass goes to embed or classifier.

RouteLLM’s four *learned* routers (preference data from Chatbot Arena ± augmentation) ([blog](https://www.lmsys.org/blog/2024-07-01-routellm/); [GitHub](https://github.com/lm-sys/RouteLLM)):

| Name | Idea | Serving cost |
|------|------|----------------|
| `sw_ranking` | Similarity-weighted Elo over past votes vs the new prompt | Needs embeddings + retrieval over vote set |
| `mf` | Matrix factorization: bilinear score δ(model, query); **recommended default** in the repo | Embed query (`text-embedding-3-small` in the paper setup) + tiny MF |
| `bert` | BERT-base classifier: P(strong better \| query) | Full BERT forward ~ tens of ms on CPU/GPU |
| `causal_llm` | Causal LM classifier | Largest router; often not worth the router bill |

Paper training detail: MF and SW ranking embed with OpenAI `text-embedding-3-small`; BERT and causal LLM are fully finetuned ([arXiv:2406.18665](https://arxiv.org/abs/2406.18665)). That means **`mf`/`sw` inherit embedding latency (~5 ms local, more if you call a hosted embed API on the hot path)**. Do not advertise “MF is free.”

**LiteLLM Router** ([docs](https://docs.litellm.ai/docs/routing)) answers a different question: given *one* `model_name` alias with **multiple deployments** (Azure east vs west, two API keys), which **endpoint** should get the call? Strategies: **simple-shuffle** (default, rpm/tpm/weight — recommended for production latency overhead), least-busy, latency-based, usage/rate-limit aware, lowest-cost. Use it **after** the quality router has chosen `haiku` vs `sonnet`. Also: retries, fallbacks, cooldown.

LiteLLM **Auto Router** (complexity / semantic flavors in later docs) is closer to quality routing; treat vendor docs as evolving — re-fetch before lecture.

**LLM-as-router:** send the user prompt to a cheap model with “reply WEAK or STRONG.” Flexible, language-native, and often **more expensive than the savings** plus extra TTFT. Use for offline labeling / augmentation (RouteLLM’s judge data), not as the default online router.

**Multi-model (&gt;2):** pairwise strong/weak (RouteLLM) vs a taxonomy (`embed`, `classify`, `reason`, `code`). Taxonomy matches product endpoints; pairwise matches preference data. Hybrids: rules map to a pair, then MF inside the pair.

---

## Alternatives & Tradeoffs

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

**Latency budget rule:** router_ms ≪ expected_TTFT. Chat UIs: router adds to **time-to-first-token**. Speculative decoding and 100 ms SLOs make BERT routers look expensive — then **rules + local embed** win.

**Shadow routing:** log `would_have_routed` without steering. Compare quality and $ for two weeks before flipping the flag.

---

## Necessity

Without routing, **unit economics** kill high-volume support/RAG: you are selling GPT-4 minutes at GPT-4-mini prices.

Without an **eval harness on the router**, teams celebrate “−40% spend” while CSAT and golden-set scores collapse on the weak arm.

Without **fallback** when the weak model fails a confidence / verifier / user-retry check, users see a bad answer with no recovery (escalation is file [02](02-model-cascading-routellm.md)).

Without **feature flags** on model IDs, a one-line prompt change plus a silent model deprecation is an incident (Week 18 digest idea applied to **model strings**).

---

## Industry Practice

**Common:** `MODEL_CHAT=claude-sonnet-…` in env; `/embed` always small; LiteLLM `simple-shuffle` across two Azure deployments of the same GPT; no quality router.

**Strong:**

1. **Must-strong / must-weak / learn** trichotomy in rules.  
2. Local embedding model (or gateway embed with tight timeout) for both intent routing and semantic cache — **same model version** if you share space.  
3. RouteLLM `mf` or an in-house BERT with **your** preference labels (thumbs, LLM-judge on traces).  
4. Online metrics: **escalate-rate**, thumbs-down **by route arm**, p95 TTFT **including router**, spend per arm.  
5. Retrain/calibrate when the **model pair** changes (GPT-4 → Claude). RouteLLM reports **some** zero-shot pair transfer (Claude 3 Opus / Llama 3 8B without retraining on those responses) — **verify on your golden set** ([blog Figure 7](https://www.lmsys.org/blog/2024-07-01-routellm/)).  
6. LiteLLM spend limits and fallbacks **per virtual key** so a bad router cannot drain one tenant (Week 19 + file [05](05-cost-attribution-dashboards.md)).

---

## Concrete Scenario

LMSYS RouteLLM (July 2024): preference-trained routers; public code as OpenAI-client drop-in / compatible server. Repo recommends **`mf`**. Eval entrypoint compares `random`, `sw_ranking`, `bert` on `mt-bench`, `mmlu`, `gsm8k` ([GitHub](https://github.com/lm-sys/RouteLLM)).

Walkthrough (implementation-level, not the paper):  
https://www.youtube.com/watch?v=mcZKQe2pUA0  

LiteLLM production load-balancing (not quality routing):  
https://docs.litellm.ai/docs/routing  

Hybrid-LLM (Ding et al., 2024) is a BERT-only cousin with synthetic MixInstruct labels — cite as related work, weaker OOD story than RouteLLM’s Arena + multi-bench protocol ([paper related-work section](https://arxiv.org/abs/2406.18665)).

---

## Open Questions

- Should routers optimize **$**, **TTFT**, **energy**, or a tenant-specific utility? Who owns the weights?  
- Shared embedding space with semantic cache: one ANN index for “same answer” vs “needs strong model”?  
- BERT-on-CPU vs tiny distilled router vs rules-only as TTFT budgets shrink.  
- Per-**step** routing in tool agents vs per-**session** (history produced by Haiku may be illegal on another provider — LiteLLM `session_affinity`).  
- Multi-tenant: one global router vs per-tenant calibration (legal FAQ vs coding copilot).

---

## Sources

- https://www.lmsys.org/blog/2024-07-01-routellm/  
- https://arxiv.org/abs/2406.18665  
- https://github.com/lm-sys/RouteLLM  
- https://huggingface.co/routellm  
- https://docs.litellm.ai/docs/routing  
- https://docs.litellm.ai/docs/auto_router/prompt_caching  
- https://www.youtube.com/watch?v=mcZKQe2pUA0  
