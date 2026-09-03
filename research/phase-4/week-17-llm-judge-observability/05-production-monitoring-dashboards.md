# 05 — Production monitoring dashboards (cost, latency, error rate, drift)

> Week 17 — What to chart and page on once traces exist  
> Research notes (raw). Platform objects: file [04](04-observability-platforms.md). Online judges must be calibrated: file [02](02-judge-alignment-calibration.md).

---

## Fundamentals

Production monitoring for LLM apps sits **on top of traces**. Infra-green (HTTP 200, CPU OK) is **not** product-healthy. Langfuse Academy framing: use traces to monitor; custom dashboards for **cost, latency, volume, quality**; **alerts** when metrics cross thresholds ([observability overview](https://langfuse.com/docs/observability/overview)).

### Signals that belong on the first dashboard

| Signal | What it catches | Notes |
|--------|-----------------|-------|
| **Latency** (p50/p95/p99, **per-span**) | Slow tools, model, retrieval | Phoenix: component-level latency; Langfuse dashboards |
| **Cost / tokens** | Prompt bloat, wrong model, agent loops | Needs pricing table + usage on **generations** |
| **Error rate** | API failures, tool exceptions, rate limits | Span status `ERROR`; Phoenix runtime exceptions |
| **Quality scores** | Judge/human/code scores over time | **Sampled** online evals; alert on threshold **after** calibration |
| **Volume** | Traffic spikes, abuse | Per user/session/feature/version |
| **Drift** | Input/embedding/behavior shift while accuracy looks flat | Phoenix embedding drift / clustering; quality-score drift; **taxonomy rate** shifts (Week 16 flywheel) |

Langfuse: **online judges asynchronously after the response ships** — monitoring ≠ blocking guardrail ([faithfulness engineering](https://langfuse.com/resources/engineering/rag-faithfulness-evaluation); [evals blog](https://langfuse.com/blog/2025-11-12-evals)).

Phoenix: token usage breakdown, latency, error inspection, embedding views; community notes embedding-distance drift useful for RAG when **HTTP 200 + stable latency hide retrieval decay** ([discussion 10442](https://github.com/Arize-ai/phoenix/discussions/10442)).

Hamel ops: **weekly sample of traces** + periodic judge runs; don’t rely on generic scores alone — pair with **error-analysis revisits** when distributions shift ([Field Guide](https://hamel.dev/blog/posts/field-guide/); [FAQ cadence](https://hamel.dev/blog/posts/evals-faq/)).

### Guardrail vs monitor (do not collapse these)

| | **Guardrail** | **Monitor / online eval** |
|--|---------------|---------------------------|
| When | In the request path, **before** the user sees output | **After** response ships (async) |
| Purpose | Block policy/safety/unfaithful answers | Trends, triage, dataset refill |
| Failure mode if confused | User-facing latency + judge flake as outages | Thinking a dashboard “blocks” bad answers |

Langfuse faithfulness: a check that **must** block belongs **in-app**; sampled 5–10% faithfulness is for **trend + routing low scores to review**.

### Sampling (you will not judge 100% of tokens)

| Source | Practice |
|--------|----------|
| **Nova Escola** | Daily eval suite on **~2%** of production traffic ([Hamel notes](https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html)) |
| **Langfuse faithfulness** | **5–10%** of matching observations often enough for a trend |
| **Langfuse cost FAQ** | ~$0.01–0.10 per judge call; sampling + observation targeting + cheaper models |
| **Hamel review sampling** | Keep **random** traces in every human batch; target outliers (long, retries) |

Need enough volume for the quality timeseries to be more than noise; rare failures need **targeted** sampling (known input patterns), not only 2% random.

### Dashboards to ship early (checklist)

1. **Requests, error %, p95 latency** by route / **version** / env.  
2. **Cost** per day / per successful task / **by model** (generation `cost_details`).  
3. **Score timeseries** for top **1–3 calibrated** failure modes (sampled boolean Pass rate).  
4. **Annotation queue depth** / human review SLA.  
5. Optional RAG: **embedding distance** to corpus centroid / cluster view (Phoenix).  
6. **Judge health:** judge error/Delayed rate, judge token cost (Langfuse judge traces).

**Alerting:** budget burn, p95 latency, error spikes, **sudden drop in Pass rate or faithfulness** — then **open traces**, don’t just page on the number. Version tags prevent mixing v1 and v2 quality on one line.

### Drift (several kinds)

| Kind | Example | Tooling |
|------|---------|---------|
| **Quality-score drift** | Calibrated faithfulness mean drops | Langfuse score dashboards + alerts |
| **Taxonomy-rate drift** | Week 16 `missing_device_lookup` rate up | Relabel sample; don’t trust judge until recalibrated |
| **Embedding / retrieval drift** | Corpus moved; latency/accuracy look fine | Phoenix embedding views; discussion 10442 |
| **Criteria drift** | Expert would now Fail yesterday’s Pass | Shankar et al.; human audits (file 02) |
| **Traffic mix drift** | New user cohort, new doc types (Shreya/legal contracts) | Stratify dashboards by tag |

OpenAI: continuous evaluation on every change; monitor **nondeterminism**; **grow the set** ([best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)). Offline experiments catch known regressions; online catches **unknowns** that refill Week 16 flywheel.

---

## Alternatives & Tradeoffs

| Monitoring style | Pros | Cons |
|------------------|------|------|
| Infra-only (CPU/5xx) | Familiar SRE | Misses silent quality failure |
| Cost+latency only | Controls spend/SLO | Quality can rot unnoticed |
| 100% online LLM judges | Dense quality signal | Expensive; needs calibration; still not a guardrail |
| Sampled judges (2–10%) + human queues | Practical | Statistical noise; need volume |
| Embedding drift dashboards | Early RAG warning | May miss behavioral collapse with stable embeddings |
| Business KPIs only | Executive-friendly | Slow/ambiguous attribution |
| Quality SLOs (Pass rate) | Product-honest | Nondeterministic; needs calibrated judge + sample size |

---

## Necessity

Without production dashboards:

- Cost regressions (agent loops) burn budget silently.  
- Latency SLOs break without **span attribution**.  
- Quality drifts after prompt/model/corpus changes with **green CI**.  
- No queue of bad traces to feed the Week 16 flywheel.  
- Uncalibrated quality alerts page the team into ignoring evals (Field Guide trust collapse).

---

## Industry Practice

**Common:** Cloudwatch 5xx + a single “helpfulness” sparkline.

**Strong:**

- Ship the five dashboard tiles above in week one of production.  
- Alerts **deep-link to traces** filtered by version.  
- Sampled calibrated scores; human queues for disagreements and tails.  
- Recalibrate judges when the timeseries jumps after a **model** change (could be judge or app).  
- Separate **experiment** comparison (offline dataset run) from **online** monitoring.  
- Nova Escola: daily 2% as a **product** habit, not a one-off.  
- Langfuse: scores on observations; dashboards + alerts; RAG context on the generation.  
- Phoenix: inspect exceptions and retrieved docs when quality drops.  
- Hamel: 10–20 weekly outlier traces between full error-analysis cycles; full 100+ every 2–4 weeks.

**Cost attribution:** tag traces by feature/tenant; sum `cost_details` — Week 20 goes deeper on routing/cache; this week you **must at least see** spend.

---

## Concrete Scenario (URL)

**Langfuse monitoring + evals unification + sampling.**  
https://langfuse.com/docs/observability/overview  
https://langfuse.com/blog/2025-11-12-evals  
https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
https://langfuse.com/resources/engineering/rag-faithfulness-evaluation  

**Phoenix metrics / tracing insights (latency, tokens, exceptions).**  
https://arize.com/docs/phoenix/tracing/llm-traces  

**Phoenix drift discussion (accuracy stable, behavior shifts; embedding-based tools).**  
https://github.com/Arize-ai/phoenix/discussions/10442  

**Nova Escola — daily sampled production evals.**  
https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html  

**Hamel Field Guide — trust, cadence, don’t generic-score-only.**  
https://hamel.dev/blog/posts/field-guide/  

**OpenAI CE / log mining.**  
https://developers.openai.com/api/docs/guides/evaluation-best-practices  

**YouTube — production-minded evals, not vanity dashboards.**  
https://www.youtube.com/watch?v=BsWxPI9UM4c  

---

## Open Questions

- What drift metrics deserve **paging** vs weekly review?  
- How to attribute cost to product features in **multi-tenant agents**?  
- Can we detect “behavioral collapse” automatically when embeddings look fine?  
- SLO design: **quality SLOs** vs classic latency SLOs for nondeterministic systems?  
- How large a sample for a 5% Pass-rate drop to be statistically real at 2% traffic sampling?  
- Should judge **cost** appear as a first-class budget line next to app completions?

---

## Sources

- https://langfuse.com/docs/observability/overview  
- https://langfuse.com/blog/2025-11-12-evals  
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
- https://langfuse.com/resources/engineering/rag-faithfulness-evaluation  
- https://arize.com/docs/phoenix/tracing/llm-traces  
- https://github.com/Arize-ai/phoenix/discussions/10442  
- https://hamel.dev/blog/posts/field-guide/  
- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
