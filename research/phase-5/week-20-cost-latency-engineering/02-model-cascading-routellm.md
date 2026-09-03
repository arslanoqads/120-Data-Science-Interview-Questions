# 02 — Model cascading (RouteLLM-style): ~15% expensive, ~95% quality

> Week 20 — selective use of a **strong** model.  
> Research notes (raw). Router *mechanisms* and latency families are file [01](01-model-routing.md).

---

## Fundamentals

**Cascading / selective routing** sends a query to a **strong expensive** model only when a **weak cheap** model is predicted to lose. RouteLLM (Ong, Almahairi, et al., 2024) formalizes two-model routing from **preference data** (Chatbot Arena votes + optional gold or LLM-judge augmentation) and releases serving + eval code ([blog](https://www.lmsys.org/blog/2024-07-01-routellm/); [arXiv:2406.18665](https://arxiv.org/abs/2406.18665); [GitHub](https://github.com/lm-sys/RouteLLM)).

**Route-once (RouteLLM default):** one router decision → **one** LLM call. The paper argues this matches an “ideal” router: quality without the extra latency of multi-LLM methods (LLM-Blender ensembles, FrugalGPT sequential cascade, AutoMix self-verify-then-escalate).

**Headline numbers (GPT-4 Turbo strong / Mixtral 8x7B weak — blog + paper):**

| Setting | Quality target | Strong-model call share | Notes |
|---------|----------------|-------------------------|--------|
| MT Bench, MF, Arena **+ LLM judge** | **95% of GPT-4** (CPT 50% in Table 1 language: MT Bench 8.8 is 95% of 9.3) | **~14%** GPT-4 calls | Blog: ~85% $ cut vs all-GPT-4; **~75% cheaper than random** at that quality |
| MT Bench, MF, Arena **only** | 95% of GPT-4 | **~26%** GPT-4 calls | ~48% cheaper than random at that point |
| MMLU, Arena only | — | ~random | OOD vs Arena chat |
| MMLU, Arena + **gold** val split (~1500 samples, &lt;2% of train) | 95% of GPT-4 | **~54%** GPT-4 (causal LLM best in blog narrative) | ~45% $ cut vs all-GPT-4 (blog) |
| GSM8K | 95% of GPT-4 | higher than MT Bench | Blog: ~35% $ cut vs all-GPT-4 |

**FDE mnemonic:** **~15% expensive / ~95% quality** refers to the **MT Bench + MF + judge-augmented** operating point (~14%, rounded). It is **not** universal. Put the **curve** (quality vs % strong) in the design doc.

**Cost threshold:** RouteLLM exposes a threshold that trades more weak traffic vs more strong. Production: sweep threshold on a **held-out golden set**; pick the point on the Pareto front that hits the product SLO.

**Deferred cascade (not RouteLLM’s main eval):** try weak → **quality/confidence check** → escalate to strong. Higher safety; **adds a full generation** (and TTFT) on hard queries. FrugalGPT (Chen et al., 2023) is the classic **LLM cascade**: sequentially query APIs until a reliability score is met; reported **50–98%** cost cut vs the best single API **on their tasks**, or **+4%** accuracy at same cost ([arXiv:2305.05176](https://arxiv.org/abs/2305.05176)). Different methodology than RouteLLM; do not mix the percentages in one sentence without labeling.

**Commercial snapshot (blog Figure 6):** open routers matched Martian / Unify quality points at **&gt;40% cheaper** on their MT Bench setup (GPT-4 Turbo + Llama-2-70B or Mixtral). Treat as **2024 research snapshot**; re-benchmark.

**Zero-shot pair transfer:** same routers, no retraining, Claude 3 Opus vs Llama 3 8B on MT Bench — blog reports strong results. Still **re-validate** when you change providers.

---

## Alternatives & Tradeoffs

| Design | Quality control | Latency | $ |
|--------|-----------------|---------|---|
| **Route-once (RouteLLM)** | Router calibration + golden set | +router only | Best when router is accurate |
| Try-weak-then-escalate (FrugalGPT / AutoMix-like) | Verifier / judge / self-check | **2× generation** on escalations | Pays weak **and** strong on hard tail |
| Speculative parallel (race small+large) | Fast when small would have won | Always pay **both** unless you cancel | Worst $ ; best p50 latency |
| Random / % canary | None | 0 | RouteLLM baseline |
| Always-strong for “premium” SKU | Contractual | 0 extra | Simple packaging |
| Ensemble / LLM-Blender | High | Multi-call | Usually loses the cost plot |

**Judge-in-the-loop escalation:** an LLM-as-judge on every weak answer can **eat the savings**. Use cheap heuristics first (logprob, length, “I don’t know”, schema fail), sample judge, or escalate on user retry.

**Tool-using agents:** cascading **per step** (router each tool loop) vs **per session**. Per-step saves $ on easy lookups; per-session avoids mixing model families in one transcript (thinking blocks, `cache_control`, tool XML). LiteLLM documents that **session_affinity** is off by default for cost routing, and that returning to a model often still finds a **warm prompt cache** ([auto router + caching](https://docs.litellm.ai/docs/auto_router/prompt_caching)).

---

## Necessity

All-frontier default **does not survive scale**. Naive “mini everywhere” fails on hard reasoning and on **trust** (one bad legal answer).

Cascading **without** an offline curve (quality vs % strong) means the threshold is folklore. Finance will pick 5% strong; Support will pick 80%.

If you cite **95%@15%** in a customer SLA, you have created a **legal metric** you cannot operationalize (which bench? which judge? which week’s models?). Use internal SLOs: golden-set score, thumbs, escape-hatches.

When the **model pair changes**, the curve moves. Budget a recalibration sprint (same as a prompt-version bump).

---

## Industry Practice

**Common:** two model IDs in config + a **manual percentage** (`STRONG_PCT=0.2`) that is not query-aware.

**Strong:**

1. Weekly plot: x = % strong calls, y = quality (judge or gold). Include **random** and **all-strong** reference lines (RouteLLM Figure 2 style).  
2. Auto-tune threshold under a **min quality** constraint.  
3. SKUs: `premium` force-strong; `balanced` routed; `economy` weak+cache only.  
4. Log **router score**, chosen arm, tokens, $ , user feedback.  
5. Shadow mode before cutover.  
6. Separate **eval traffic** so the cascade is not trained on its own production hacks.  
7. When using LiteLLM load balancing **and** Anthropic prompt cache, pin **deployment** after first cache write (`prompt_caching` pre-call check).

---

## Concrete Scenario

**Reproduce the public point, then distrust it.** Run RouteLLM eval: `python -m routellm.evals.evaluate --routers random mf bert --benchmark mt-bench` with the example config trained on Arena+judge ([GitHub README](https://github.com/lm-sys/RouteLLM)). Record CPT(50%) / 95% quality call fraction. Then **replay 500 labeled tickets** from the customer and draw the same axes. If in-domain data is tiny, RouteLLM’s lesson is **augment** (gold or judge) rather than ship Arena weights blindly — MMLU was random until ~1500 in-domain labels.

Paper + blog:  
https://arxiv.org/abs/2406.18665  
https://www.lmsys.org/blog/2024-07-01-routellm/  

FrugalGPT cascade (sequential APIs):  
https://arxiv.org/abs/2305.05176  

YouTube walkthrough of serving the open routers:  
https://www.youtube.com/watch?v=mcZKQe2pUA0  

---

## Open Questions

- Escalation **classifiers** vs **answer-quality judges** — when does the judge cost exceed Mixtral savings?  
- Cascading **agents**: router per tool call vs once per user message?  
- How to write an enterprise SLA without “95% of GPT-4” (maybe: “golden-set ≥ X, p95 TTFT ≤ Y, strong-call % ≤ Z”)?  
- Unified routing **and** cascading in one policy ([related papers exist]; production systems usually pick one primary).  
- Carbon / energy as a third axis next to $ and quality.

---

## Sources

- https://www.lmsys.org/blog/2024-07-01-routellm/  
- https://arxiv.org/abs/2406.18665  
- https://github.com/lm-sys/RouteLLM  
- https://huggingface.co/routellm  
- https://arxiv.org/abs/2305.05176  
- https://docs.litellm.ai/docs/auto_router/prompt_caching  
- https://www.youtube.com/watch?v=mcZKQe2pUA0  
