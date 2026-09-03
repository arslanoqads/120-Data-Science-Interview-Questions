# 05 — Cost-attribution dashboards

> Week 20 — if you cannot say **which tenant, feature, model, and prompt version spent $X yesterday**, you cannot optimize or invoice.  
> Research notes (raw). Week 19 virtual keys are the **control plane**; this file is the **FinOps / observability** plane.

---

## Fundamentals

**Cost attribution** is labeling every LLM (and embedding) call so spend can be sliced. Provider consoles show **API keys and models**, not your product.

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

1. **LLM gateway** — LiteLLM spend logs, virtual keys, teams, budgets ([cost tracking](https://docs.litellm.ai/docs/proxy/cost_tracking); [virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys); [users](https://docs.litellm.ai/docs/proxy/users)). `completion_cost()` applies the **model cost map**, including **provider cache token** categories. Spend updates are designed to run **after** the response (async) so the DB write is not on the hot path ([architecture / life of a request](https://docs.litellm.ai/docs/proxy/architecture)).  
2. **OpenTelemetry** — spans with the attributes above; metrics with **bounded** cardinality; traces for drill-down ([OTel docs](https://opentelemetry.io/docs/)).  
3. **Warehouse ETL** — provider usage exports → BigQuery/Snowflake + dbt. Rich joins, **hours of lag**.

**LiteLLM specifics FDEs hit:**

- Track spend at **key / user / team**; end-user `user` field in the body can **mis-attribute** if clients self-declare — set `user_id` on the virtual key and force identity if needed.  
- Default **User-Agent** tag (Claude Code, Gemini CLI, etc.).  
- Virtual keys: model allowlists + **max_budget** / rate limits — the dashboard without a **kill switch** is a report, not a control.  
- Debug cost discrepancies: align time ranges, compare **token categories including cache**, then formula vs model-map.

**Cardinality:** do **not** put raw `user_id` × `prompt_hash` on **metrics**. Use exemplars/traces. `prompt_version` (semver) is fine; full prompt text is not a Prometheus label.

**Cascade accounting:** weak attempt + strong escalate = **two** generations, one user-visible answer. Decide: bill the **feature** the sum; show a `cascade_extra_usd` column so routing quality is visible.

**Cache credits:** a semantic hit is “free” generation but **used** someone else’s answer. Optional: credit the originating team’s cost center — advanced, usually skip until chargeback fights start.

**Eval vs prod:** Week 16/17 flywheels can dominate spend if judges run on every trace. Tag `environment=eval` or a dedicated virtual key.

AWS **GenAI Lens** multi-tenant scenario treats usage analytics and cost tracking as first-class for a multi-tenant GenAI platform ([Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html)).

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| Provider console only | Free | No tenant/feature split |
| Gateway virtual keys per tenant | Natural spend walls | Coarse if one key, many features — add `metadata` tags |
| Span attributes → metrics | Flexible, real-time | High-cardinality pitfalls; you must maintain the schema |
| FinOps warehouse | Rich joins, invoices | Lag; engineering cost |
| Spreadsheet monthly CSV | Honest start | Too late for scrapers |
| Always-on LLM judge for quality×cost | Causal | Judge $ can dwarf savings |

---

## Necessity

Without attribution, routing and caching wins are **anecdotal** (“feels cheaper”).

Without **budgets/hard limits** per tenant, one scraper or leaked virtual key exhausts the **org** OpenAI bill (Week 19 isolation without $ isolation).

Without linking **cost to quality**, teams cut the **wrong** model (the cheap arm that was already failing).

Without **cache_read** in the cube, prompt-caching projects cannot prove ROI and will be reverted after a scary invoice (writes are **premium**).

Without separating **eval** spend, the research org looks like a product outage.

---

## Industry Practice

**Common:** monthly invoice; one shared key; “the AI budget”; LiteLLM UI glanced at after an incident.

**Strong:**

1. Real-time gateway dashboards (LiteLLM + Grafana/Datadog/Langfuse).  
2. Per-tenant **soft then hard** budget; webhook / Slack at 70/90/100%.  
3. Anomaly detection (spend z-score by tenant×surface).  
4. Weekly FinOps review **tied to router threshold** (file [02](02-model-cascading-routellm.md)).  
5. Chargeback to internal LOBs.  
6. Cost of **eval** and **shadow routing** tracked separately.  
7. Canary abort includes **spend spike** (Week 18) — a bad prompt version that doubles output tokens is a deploy incident.  
8. Document who **owns** the dashboard (platform vs FinOps vs each squad) so it does not rot.

---

## Concrete Scenario

LiteLLM:  
https://docs.litellm.ai/docs/proxy/cost_tracking  
https://docs.litellm.ai/docs/proxy/users  
https://docs.litellm.ai/docs/proxy/virtual_keys  
https://docs.litellm.ai/docs/proxy/architecture  

AWS GenAI Lens multi-tenant usage analytics:  
https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  

OpenTelemetry:  
https://opentelemetry.io/docs/  

**Interview cube:** rows = tenants; columns = (`router=strong`, `router=weak`, `cache=semantic`, `cache=exact`); cell = USD and request count; extra sheet = p95 TTFT. Overlay golden-set score by arm. Before/after from file [00](00-week-overview.md) is this cube **summed**.

YouTube (gateway mental model, not a metrics spec): LiteLLM as unified router/fallback — use as orientation only:  
https://www.youtube.com/watch?v=MeTJVfdj3JM  

vLLM talk if the $ is **GPU** not API:  
https://www.youtube.com/watch?v=UdNocRPQS3Y  

---

## Open Questions

- Who owns the cost dashboard — platform eng, FinOps, or each product squad?  
- How to attribute **shared cascade** costs (weak + strong) fairly across features?  
- Should semantic cache hits **credit** the team that paid for the original generation?  
- How to show **prompt-cache writes** as investment (like a CDN fill) vs waste?  
- Carbon/energy metrics next to USD for self-hosted vLLM?

---

## Sources

- https://docs.litellm.ai/docs/proxy/cost_tracking  
- https://docs.litellm.ai/docs/proxy/users  
- https://docs.litellm.ai/docs/proxy/virtual_keys  
- https://docs.litellm.ai/docs/proxy/architecture  
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/multi-tenant-generative-ai-platform-scenario.html  
- https://opentelemetry.io/docs/  
- https://www.lmsys.org/blog/2024-07-01-routellm/  
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  
- https://platform.openai.com/docs/guides/prompt-caching  
- https://www.youtube.com/watch?v=MeTJVfdj3JM  
- https://www.youtube.com/watch?v=UdNocRPQS3Y  
