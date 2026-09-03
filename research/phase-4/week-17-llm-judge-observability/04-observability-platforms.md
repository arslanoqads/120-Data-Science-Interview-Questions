# 04 — Observability platforms (Langfuse, Arize Phoenix)

> Week 17 — Tracing products: spans, generations, OpenInference, OTEL  
> Research notes (raw). Dashboards/alerts/drift as *use* of traces: file [05](05-production-monitoring-dashboards.md).

---

## Fundamentals

**Observability** for LLM apps = understanding internal behavior from logged outputs (metrics, logs, **traces**). Langfuse FAQ: observability is the broader capability; **tracing** is the technique that records the **flow of a request** and preserves **causal** relationships. For LLM apps, tracing is the most important tool because it captures prompts, responses, tool calls, and their relationships ([observability overview](https://langfuse.com/docs/observability/overview)).

**Why LLM-specific platforms exist:** general APM (Datadog-only) has weak prompt/token/eval semantics. OpenTelemetry is generic by design; **OpenInference** adds AI span kinds and attributes on top of valid OTLP ([OpenInference spec](https://arize-ai.github.io/openinference/spec/)).

### Core objects (learn both vocabularies)

**Langfuse ↔ OpenTelemetry mapping** ([SDK overview](https://langfuse.com/docs/observability/sdk/overview)):

| OTel | Langfuse |
|------|----------|
| Trace (defined by root span; shares ID) | Langfuse **trace** = observations sharing `trace_id` + `session_id` / `user_id` |
| Span | **Observation** (span, **generation**, event, tool, retrieval, …) |
| — | **Generation**: specialized span for LLM calls: `model`, `model_parameters`, `usage_details` (tokens), `cost_details` |

Langfuse v4: overall input/output belong on the **root observation**; **trace-level I/O is deprecated**. Attribute propagation: `userId`, `sessionId`, `metadata`, `version`, `tags` via `propagate_attributes()`.

**Phoenix / OpenInference:**

- **Trace** = full execution path (user input → retrieval → LLM → tools → response).  
- **Span** = atomic unit: one LLM call, one tool, one retrieval. Fields: name, start/end, `openinference.span.kind`, attributes, status `OK`/`ERROR`/`UNSET`.  
- **Span kinds:** `LLM`, `AGENT`, `CHAIN`, `TOOL`, `RETRIEVER`, `RERANKER`, `EMBEDDING`, `GUARDRAIL`, `EVALUATOR`, `PROMPT` ([spec](https://arize-ai.github.io/openinference/spec/)).  
- **Motivation in the spec:** structured multi-turn messages, token economics, agentic control flow, privacy masking, nondeterminism (enough context to explain a run), **quality feedback** (human / LLM / code scores associated with the operation).

**Sessions:** Phoenix groups related traces into conversations; Langfuse has `sessionId` similarly. Annotation queues in both: **label the GENERATION** when trace I/O is null under OTEL (Week 16 Langfuse anti-pattern).

### Langfuse (OSS, self-hostable)

Purpose-built loop: **traces → scores (human/code/judge) → datasets/experiments → prompt management → custom dashboards & alerts**.

- Python SDK v4 / JS SDK v5 on **OpenTelemetry**; **async** export; “cannot break your application” (errors caught).  
- `start_as_current_observation(as_type="span"| "generation", ...)`. Nested generation under span. `flush()` in short-lived jobs.  
- Default export: Langfuse + GenAI/LLM spans; customize with **`should_export_span` / `shouldExportSpan`** (filter OTEL noise). `blocked_instrumentation_scopes` deprecated.  
- Regions: EU default, US, Japan, HIPAA cloud URLs in docs.  
- Judges: observation-level; compositional (toxicity on LLM, relevance on retrieval); filters stack observation + trace tags. Evaluator executions are traces in env `langfuse-llm-as-a-judge`.  
- Latency: SDK queues/batches; **does not add request latency** if used as documented.

### Arize Phoenix (OSS)

Traces via **OTEL**; first-class LlamaIndex, LangChain, OpenAI, DSPy, Bedrock, etc. Insights listed in [LLM traces](https://arize.com/docs/phoenix/tracing/llm-traces):

- Application **latency** (slow LLM / retriever / other)  
- **Token usage** breakdown  
- **Runtime exceptions** (e.g. rate limits)  
- **Retrieved documents** (score + order)  
- **Embeddings** (text + model)  
- **LLM parameters** (temperature, system prompts)  
- **Prompt templates** + variables  
- **Tool descriptions** and **function calls**

Features: projects, sessions, annotations, metrics, **run evaluations** (LLM-as-judge on traces), embedding views.

**OpenInference best practices** ([Phoenix cookbook](https://arize.com/docs/phoenix/cookbook/tracing/openinference-best-practices)): hierarchy **sessions → traces → spans**; three capture modes — **auto-instrumentation**, **manual**, **hybrid** (wrap logical units, keep LLM child spans). Enrich auto-instrumented spans with LLM/tool/agent/chain/session attributes. Local `phoenix serve` UI `:6006` for the cookbook.

### Instrumentation principles (both)

- Hierarchical traces with **inputs/outputs on each span**.  
- Tag `userId`, `sessionId`, `version`, `env`, feature flags.  
- Record **token usage and model name** on every generation/LLM span.  
- **Attach retrieved context** onto the generation being judged (Langfuse: judges **cannot** see siblings).  
- Sample or filter non-LLM OTEL spans to control cost/noise.  
- Privacy: OpenInference calls out **per-field masking**; decide how much prompt payload to store under retention law (open question, file 00).  
- Hamel FAQ: you do **not** need a dedicated AI observability product to *start* error analysis (JSON/CSV) — you **do** need structured traces before judges and cost dashboards scale.

---

## Alternatives & Tradeoffs

| Platform / approach | Pros | Cons |
|---------------------|------|------|
| **Langfuse** | Strong eval+prompt+dataset loop; generations/cost native; OSS self-host | Must filter OTEL noise or observation volume explodes; v4 observation-first migration |
| **Phoenix** | OpenInference richness; embedding drift UX; OTEL-native; OSS | Drift automation vs exploration (community [discussion 10442](https://github.com/Arize-ai/phoenix/discussions/10442)); less “prompt CMS” than Langfuse |
| General APM (Datadog-only) | Already deployed | Weak prompt/token/eval semantics |
| Homegrown logs | Full control | No trace UI; reinvent scoring/datasets |
| Closed SaaS-only | Managed | Data residency / lock-in |
| LangSmith (adjacent, not this week’s bake-off focus) | Trajectory graders (Week 15) | Another vendor; still OTEL-ish |

Instrumentation: **auto** vs **manual** vs **hybrid** — OpenInference: hybrid often best.

---

## Necessity

Without tracing:

- Cannot do error analysis on real **cascades** (RAG vs model vs tool) — Week 16 dies.  
- Cost/latency debugging is guesswork.  
- Judges lack context (faithfulness needs retrieved docs **on the same observation**).  
- Flywheel has no production inlet.  
- You cannot debug **the judge** (Langfuse: judge runs are traces).

Without LLM-specific semantics (generations / OpenInference kinds):

- You have spans named `HTTP POST` and no token/cost/model.  
- Dashboards cannot split “slow retriever” vs “slow 32k prompt”.

---

## Industry Practice

**Common:** Log final answer only; maybe wrap OpenAI SDK once; never set `sessionId`.

**Strong:**

- Hierarchical traces; I/O on spans; propagate user/session/version.  
- Generations with usage + cost tables.  
- Retrieved context on the judged observation.  
- `should_export_span` to drop framework spam.  
- Annotation queues on **GENERATION** when OTEL trace I/O is null.  
- Dual-write or pick **one primary** (Langfuse *or* Phoenix) and map concepts; don’t run three incomplete instrumentations.  
- Self-host for regulated industries (both OSS); Langfuse HIPAA cloud exists as a managed option.  
- Instrument **judge** and **app** the same way.

**Langfuse vs Phoenix pick (engineering, not marketing):** choose Langfuse if the bottleneck is **eval/experiment/prompt versioning**; choose Phoenix if the bottleneck is **OpenInference-shaped traces, embeddings, and retrieval inspection**. Many teams can start with either; the **syllabus requires literacy in both**.

---

## Concrete Scenario (URL)

**Langfuse observability overview (tracing, cost, scores, dashboards, alerts; async SDK).**  
https://langfuse.com/docs/observability/overview

**Langfuse SDK: spans vs generations, OTEL mapping, `should_export_span`.**  
https://langfuse.com/docs/observability/sdk/overview

**Langfuse LLM-as-judge on observations; judge debug traces.**  
https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge

**Phoenix tracing overview.**  
https://arize.com/docs/phoenix/tracing/llm-traces

**OpenInference spec + semantic conventions.**  
https://arize-ai.github.io/openinference/spec/  
https://arize-ai.github.io/openinference/spec/semantic_conventions.html

**OpenInference best practices (span kinds, hybrid instrumentation).**  
https://arize.com/docs/phoenix/cookbook/tracing/openinference-best-practices

**Hamel FAQ — you can start without a vendor; trace definition drift.**  
https://hamel.dev/blog/posts/evals-faq/

---

## Open Questions

- Standardized trace semantics across vendors (Hamel FAQ: definition drift)?  
- How much payload (full prompts) to store under privacy/retention law?  
- Multi-agent graphs: **one** trace vs many **linked** traces? OpenInference `AGENT` children vs separate traces?  
- Self-host vs cloud for regulated industries (latency to OTLP collector, data residency)?  
- Langfuse v4 cutover (trace-level evaluators stop **2026-11-16** on Cloud) — migration cost?  
- When is Datadog + OpenInference exporter “enough” vs a dedicated UI?

---

## Sources

- https://langfuse.com/docs/observability/overview  
- https://langfuse.com/docs/observability/sdk/overview  
- https://langfuse.com/  
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
- https://arize.com/docs/phoenix/tracing/llm-traces  
- https://arize.com/docs/phoenix/cookbook/tracing/openinference-best-practices  
- https://arize-ai.github.io/openinference/spec/  
- https://arize-ai.github.io/openinference/spec/semantic_conventions.html  
- https://hamel.dev/blog/posts/evals-faq/  
