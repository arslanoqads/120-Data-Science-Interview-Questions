# Week 17 — LLM-as-Judge & Observability

Raw source material for designing calibrated LLM judges, choosing code vs model-based evals, and production observability (Langfuse / Arize Phoenix): spans, generations, cost/latency, dashboards, drift.

**Source policy:** Legal/public sources only (hamel.dev, Shreya Shankar papers, Langfuse/Phoenix docs, G-Eval, OpenAI/Anthropic public materials, talks). No pirate PDFs.

---

## Concept A — Designing LLM-as-judge that correlates with human judgment

### Fundamentals

An **LLM-as-judge** (model-based evaluator) scores or labels another system’s outputs using an LLM prompted with criteria—typically when quality is subjective or hard to assert in code (tone, persona, “should have clarified,” faithfulness given context).

Practitioner consensus (Hamel *Using LLM-as-a-Judge*):

- Prefer **binary Pass/Fail** (+ written critique) over uncalibrated 1–5 multi-metric dashboards.
- Scope the judge to **one failure mode** from error analysis—not a kitchen-sink “quality” score.
- Domain expert labels first (“critique shadowing”); the judge learns to shadow that expert.
- Measure **alignment with humans** (TPR/TNR / precision-recall), not vibes or raw agreement under class imbalance.

Research backdrop:

- **G-Eval** (Liu et al., EMNLP 2023): GPT-4 + chain-of-thought + form-filling; Spearman ~0.514 with humans on SummEval—far above ROUGE/BLEU. Also warns of **bias toward LLM-generated text**.
- **Who Validates the Validators?** (Shankar et al., 2024): LLM graders inherit LLM problems; humans must validate validators; **criteria drift**—criteria and observed outputs co-evolve.

OpenAI cookbook guidance: model grading works best with strong models and room to reason; validate with humans before scale; prefer a **different** model for grading than completing when possible.

### Alternatives & Tradeoffs

| Judge design | Pros | Cons |
|--------------|------|------|
| Binary + critique (Hamel) | Clear; forces criteria; actionable | Less nuance than multi-axis scores |
| Likert 1–5 multi-dim | Familiar dashboards | Uncalibrated; annotator disagreement; vanity metrics |
| G-Eval-style CoT + form fill | Better human correlation in NLG research | Cost; still needs product-specific calibration |
| Pairwise preference (A vs B) | Strong for ranking models/prompts | Harder for absolute regression gates |
| Reference-based (BLEU/ROUGE) | Cheap, deterministic | Weak human correlation for open-ended gen |
| Same model as producer | Ops-simple | Self-preference bias risk; Hamel: OK if binary task aligns with humans |

Hamel FAQ: same model for task and judge is often fine for **scoped binary** judges if TPR/TNR on held-out labels are strong; start with most capable judge, optimize cost later.

### Necessity

Uncalibrated judges:

- Optimize the product for the judge’s quirks (sycophancy, length bias, self-preference).
- Create dashboards nobody trusts → teams ignore evals.
- Fail to catch the taxonomy failures you actually care about.

Skipping judges entirely for subjective failures leaves only slow human review at production scale.

### Industry Practice

**Common:** Drop in a vendor “hallucination” template; never check vs humans.

**Strong:**

1. Error analysis → one failure mode.
2. Expert labels 100–200 examples (balanced Pass/Fail where possible).
3. Split train (few-shot) / dev / held-out test.
4. Iterate prompt (prefer PE over fine-tuning per Hamel) using expert critiques.
5. Gate on TPR & TNR; refuse to ship judge if alignment weak.
6. Recalibrate when product or judge model changes.
7. Log judge calls as traces (Langfuse: judge executions are traces you can debug).

### Concrete Scenario (URL)

Hamel’s end-to-end critique-shadowing guide (principal domain expert → dataset → pass/fail+critique → automate → validate agreement/TPR/TNR):

- https://hamel.dev/blog/posts/llm-judge/

G-Eval paper (ACL Anthology / DOI):

- https://aclanthology.org/2023.emnlp-main.153/
- https://doi.org/10.18653/v1/2023.emnlp-main.153

Shankar et al. criteria drift / EvalGen:

- https://arxiv.org/abs/2404.12272

### Open Questions

- When do multi-dimensional scores become necessary vs harmful?
- How much self-enhancement bias remains for modern judges on binary product tasks?
- Probabilistic scoring (token probs / n-sample as in G-Eval) vs single structured label in production?
- Can smaller/cheaper judges match large ones after distillation on expert labels?

### Sources

- https://hamel.dev/blog/posts/llm-judge/
- https://hamel.dev/blog/posts/evals/
- https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html
- https://arxiv.org/abs/2404.12272
- https://aclanthology.org/2023.emnlp-main.153/
- https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge

---

## Concept B — Judge alignment / calibration against expert-labeled examples

### Fundamentals

**Alignment** = the judge’s labels match the domain expert’s labels on held-out data. **Calibration** (ops sense) = ongoing checks so that trust remains as data and models drift.

Hamel methodology (“critique shadowing”):

1. Expert labels with Pass/Fail + critique.
2. Build judge prompt that asks for the same decision (+ optional rationale).
3. Put some labeled critiques as few-shots; iterate on failures where judge ≠ expert.
4. Report **True Positive Rate** and **True Negative Rate** separately (raw accuracy is a trap when failures are rare—always predicting Pass looks great).
5. Only then run judge on unseen synthetic/production traffic to estimate failure rates.

Shankar *Who Validates the Validators?*: EvalGen generates candidate assertions/prompts, humans grade a subset, system selects implementations that maximize alignment (coverage vs false failure tradeoff). Qualitative finding: grading outputs *changes* the criteria—so treat calibration as iterative, not one-shot.

OpenAI: maintain agreement between automated scoring and human feedback; continuous evaluation.

Langfuse: calibrate judges on a small human-annotated sample before trusting trend lines; typical judge cost cited ~$0.01–0.10 per assessment—use sampling.

### Alternatives & Tradeoffs

| Calibration practice | Pros | Cons |
|----------------------|------|------|
| Held-out TPR/TNR gates | Honest; imbalance-aware | Needs enough Fail examples |
| Cohen’s κ / correlation only | Single number | Hides asymmetric errors |
| Periodic human audits (weekly sample) | Catches drift | Ongoing cost |
| AlignEval-style UI loops | Fast iteration | Tooling investment |
| No calibration (“vendor template”) | Zero effort | Untrusted metrics |

Split guidance (Hamel): ~10–20% train (few-shot), ~40–45% dev, ~40–45% final test; aim ~30–50 Pass and Fail in dev and test when possible.

### Necessity

Without calibration:

- Online “quality” charts are fiction.
- You “fix” regressions that are judge noise—or miss real ones.
- Multi-annotator chaos: if two humans disagree worse than chance (Nova Escola), the judge cannot align to a nonexistent standard—fix the rubric first.

### Industry Practice

**Common:** Spot-check 10 examples once, then forget.

**Strong:**

- Version judge prompts; store alignment report next to prompt version.
- Recalibrate on model upgrades (judge or app).
- Use disagreements as gold for taxonomy/rubric updates (criteria drift as feature).
- Separate **offline experiment** alignment from **online sampled** monitoring.
- Anthropic-style guidance: combine rule-based, model-based, and targeted human grading; larger models can help evaluate smaller ones; decompose evals for frontier models.

### Concrete Scenario (URL)

Nova Escola: two annotators initially agreed less than chance → rewrite rubric with pedagogical experts → relabel → then automate judges validated against humans; daily evals on 2% production traffic.

- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

Alignment metrics discussion in Hamel judge guide + FAQ:

- https://hamel.dev/blog/posts/llm-judge/
- https://hamel.dev/blog/posts/evals-faq/

Field Guide on AlignEval and ongoing calibration:

- https://hamel.dev/blog/posts/field-guide/

### Open Questions

- Minimum labeled set for high-stakes domains (healthcare, finance)?
- How to calibrate when the “expert” is a committee with persistent disagreement?
- Active learning: which disagreements to send to humans next?
- Should online scores be Bayesian-adjusted by known TPR/TNR?

### Sources

- https://hamel.dev/blog/posts/llm-judge/
- https://hamel.dev/blog/posts/field-guide/
- https://hamel.dev/blog/posts/evals-faq/
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html
- https://arxiv.org/abs/2404.12272
- https://langfuse.com/blog/2025-11-12-evals
- https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf (Anthropic “Planning to production” — public PDF)

---

## Concept C — Code-based vs model-based evals (when each is appropriate)

### Fundamentals

Two evaluator families (Hamel/Shreya teaching, Langfuse docs, OpenAI graders):

| Type | Mechanism | Best for |
|------|-----------|----------|
| **Code-based / deterministic** | Assertions, regex, JSON schema, exact match, tool-arg checks, length, allowlists | Objective, unambiguous failures |
| **Model-based / LLM judge** | Prompted LLM (or classifier) scores output | Subjective, semantic, domain judgment |
| **Human** | Expert review | Ground truth, calibration, high-stakes, rubric discovery |

Decision rule (repeated across Hamel FAQ, Langfuse error-analysis cookbook, Lenny’s Podcast talk):

1. Can you **just fix** the bug in prompt/tools/code? Do that first.
2. Else, if a **deterministic rule** catches it → code eval (cheap, CI-friendly).
3. Else, if it needs **judgment** → LLM judge (then calibrate).
4. Safety/compliance may need an evaluator **as guardrail** even after fixing.

OpenAI Evals API: `string_check` and similar deterministic graders vs model graders; combine evaluator types. Anthropic: robust systems combine rule-based + LLM-powered + targeted human grading.

### Alternatives & Tradeoffs

| Choice | Cost | Latency | Brittleness | Human correlation effort |
|--------|------|---------|-------------|---------------------------|
| Code assert | ≈0 | ms | High if format varies | Low (examples for edges) |
| LLM judge | $$ | seconds | Prompt-sensitive | High (100–200 labels) |
| Human | $$$ | hours/days | Rater variance | N/A (is the reference) |
| Hybrid: code prefilter → judge | Medium | Medium | Manageable | Medium |

Trap: building a judge for “emit exactly one learning goal” when a prompt change deletes the double-goal bug (Nova Escola lesson).

CI pattern (talk write-ups): several code evals in CI; LLM judges sparingly in CI or on a schedule/sample due to cost/flakiness.

### Necessity

Code-only → blind to persona, tone, partial helpfulness, faithfulness nuance.  
Judge-only → expensive, flaky CI, meta-eval debt for failures a `json.loads` would catch.  
Neither → flying blind.

### Industry Practice

**Code examples:** valid JSON; required sections present; tool name/args schema; PII regex; max tokens; citation IDs ⊆ retrieved IDs; “must not claim X”.

**Judge examples:** should have asked clarifying question; grounded in retrieved context; correct empathy/persona; summary coherence.

**Langfuse:** code evaluators + LLM-as-judge; observation-level targeting (evaluate only `GENERATION` named `final-response`); sampling rules for cost.

### Concrete Scenario (URL)

Hamel/Shreya on code vs LLM evals (talk + FAQ):

- https://www.youtube.com/watch?v=BsWxPI9UM4c
- https://hamel.dev/blog/posts/evals-faq/
- https://www.aakashg.com/ai-evals-masterclass-with-hamel-shreya/

Langfuse decision table after taxonomy:

- https://langfuse.com/guides/cookbook/error-analysis-llm-applications

OpenAI working with evals / graders:

- https://developers.openai.com/api/docs/guides/evals
- https://github.com/openai/evals

### Open Questions

- Flaky LLM judges in CI: retries, temperature 0, caching—what’s acceptable flake rate?
- Learned classifiers (fine-tuned small models) as middle ground?
- Property-based testing for agents vs static golden sets?

### Sources

- https://hamel.dev/blog/posts/evals-faq/
- https://hamel.dev/blog/posts/evals/
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge
- https://developers.openai.com/api/docs/guides/evals
- https://developers.openai.com/api/docs/guides/evaluation-best-practices
- https://github.com/openai/evals

---

## Concept D — Observability platforms (Langfuse / Arize Phoenix)

### Fundamentals

**Observability** for LLM apps = understanding internal behavior from logged outputs. **Tracing** records the causal tree of a request.

Core objects:

- **Trace** — full path of one request/session unit (vendor definitions vary slightly).
- **Span / observation** — one unit of work (retrieval, tool, LLM call, chain).
- **Generation** (Langfuse) — specialized observation for LLM calls with `model`, `model_parameters`, `usage_details` (tokens), `cost_details`.
- **OpenInference span kinds** (Phoenix/Arize): `LLM`, `CHAIN`, `RETRIEVER`, `RERANKER`, `TOOL`, `AGENT`, `EMBEDDING`, `GUARDRAIL`, `EVALUATOR`, `PROMPT`, …

Both Langfuse and Phoenix ride **OpenTelemetry** (OTLP); async export so app latency impact is negligible if batched correctly.

**Langfuse** (OSS, self-hostable): traces → scores (human/code/judge) → datasets/experiments → prompt management → custom dashboards & alerts. Observation-level LLM-as-judge with filters + sampling.

**Arize Phoenix** (OSS): OTEL + OpenInference; first-class framework integrations; inspect latency, tokens, retrieved docs, embeddings, tool calls; sessions; annotations; run LLM-as-judge evals on traces; embedding/drift exploration.

### Alternatives & Tradeoffs

| Platform / approach | Pros | Cons |
|---------------------|------|------|
| Langfuse | Strong eval+prompt+dataset loop; generations/cost native | Must filter OTEL noise or observation volume explodes |
| Phoenix | OpenInference richness; embedding drift UX; OTEL-native | Drift automation vs exploration tradeoffs (community discussion) |
| General APM (Datadog-only) | Already deployed | Weak prompt/token/eval semantics |
| Homegrown logs | Full control | No trace UI; reinvent scoring/datasets |
| Closed SaaS-only | Managed | Data residency / lock-in concerns |

Instrumentation tradeoff: auto-instrument frameworks vs manual spans—hybrid often best (OpenInference best practices): wrap logical units, keep LLM child spans.

### Necessity

Without tracing:

- Cannot do error analysis on real cascades (RAG vs model vs tool).
- Cost/latency debugging is guesswork.
- Judges lack context (e.g. faithfulness needs retrieved docs on the same observation—Langfuse RAG guide).
- Flywheel has no production inlet.

### Industry Practice

**Common:** Log final answer only.

**Strong:**

- Hierarchical traces with inputs/outputs on each span.
- Tag `userId`, `sessionId`, `version`, `env`, feature flags.
- Record token usage and model name on every generation.
- Attach retrieved context onto the generation being judged.
- Sample or filter non-LLM OTEL spans (`should_export_span`) to control cost/noise (Langfuse).
- Use annotation queues on the **GENERATION** observation when trace I/O is null under OTEL.

### Concrete Scenario (URL)

Langfuse observability overview (tracing, cost, scores, dashboards, alerts):

- https://langfuse.com/docs/observability/overview

Langfuse SDK: spans vs generations, OTEL:

- https://langfuse.com/docs/observability/sdk/overview

Phoenix tracing overview:

- https://arize.com/docs/phoenix/tracing/llm-traces

OpenInference spec / semantic conventions:

- https://arize-ai.github.io/openinference/spec/
- https://arize-ai.github.io/openinference/spec/semantic_conventions.html

OpenInference best practices (span kinds, hybrid instrumentation):

- https://arize.com/docs/phoenix/cookbook/tracing/openinference-best-practices

### Open Questions

- Standardized trace semantics across vendors (Hamel FAQ notes definition drift)?
- How much payload (full prompts) to store under privacy/retention law?
- Multi-agent graphs: one trace vs many linked traces?
- Self-host vs cloud for regulated industries?

### Sources

- https://langfuse.com/docs/observability/overview
- https://langfuse.com/docs/observability/sdk/overview
- https://langfuse.com/
- https://arize.com/docs/phoenix/tracing/llm-traces
- https://arize-ai.github.io/openinference/spec/
- https://hamel.dev/blog/posts/evals-faq/ (trace definition Q)

---

## Concept E — Production monitoring dashboards (cost, latency, error rate, drift)

### Fundamentals

Production monitoring for LLM apps sits on top of traces:

| Signal | What it catches | Notes |
|--------|-----------------|-------|
| **Latency** (p50/p95/p99, per-span) | Slow tools, model, retrieval | Phoenix: component-level latency; Langfuse dashboards |
| **Cost / tokens** | Prompt bloat, wrong model, loops | Needs pricing table + usage on generations |
| **Error rate** | API failures, tool exceptions, rate limits | Span status `ERROR`; runtime exceptions in Phoenix |
| **Quality scores** | Judge/human/code scores over time | Sampled online evals; alert on threshold |
| **Volume** | Traffic spikes, abuse | Per user/session/feature |
| **Drift** | Input/embedding/behavior shift while accuracy looks flat | Phoenix embedding drift / clustering; quality score drift; taxonomy rate shifts |

Langfuse: custom dashboards for cost, latency, volume, quality; alerts when metrics cross thresholds; online judges asynchronously after response ships (monitoring ≠ blocking guardrail).

Phoenix: token usage breakdown, latency, error inspection, embedding views; community notes embedding-distance drift useful for RAG when HTTP 200 + stable latency hide retrieval decay.

Hamel ops pattern: weekly sample of traces + periodic judge runs; don’t rely on generic scores alone—pair with error-analysis revisits when distributions shift.

### Alternatives & Tradeoffs

| Monitoring style | Pros | Cons |
|------------------|------|------|
| Infra-only (CPU/5xx) | Familiar SRE | Misses silent quality failure |
| Cost+latency only | Controls spend/SLO | Quality can rot unnoticed |
| 100% online LLM judges | Dense quality signal | Expensive; needs calibration |
| Sampled judges (2–10%) + human queues | Practical | Statistical noise; need enough volume |
| Embedding drift dashboards | Early RAG warning | May miss behavioral collapse with stable embeddings |
| Business KPIs only | Executive-friendly | Slow/ambiguous attribution |

Guardrail vs monitor: blocking bad answers belongs in-app; async evaluators are for trends and triage (Langfuse faithfulness engineering note).

### Necessity

Without production dashboards:

- Cost regressions (agent loops) burn budget silently.
- Latency SLOs break without span attribution.
- Quality drifts after prompt/model/corpus changes with green CI.
- No queue of bad traces to feed the Week-16 flywheel.

### Industry Practice

**Dashboards to ship early:**

1. Requests, error %, p95 latency by route/version.
2. Cost per day / per successful task / by model.
3. Score timeseries for top 1–3 calibrated failure modes (sampled).
4. Annotation queue depth / human review SLA.
5. Optional: embedding distance to corpus centroid for RAG.

**Alerting:** budget burn, p95 latency, error spikes, sudden drop in Pass rate or faithfulness—then open traces, don’t just page on the number.

**Sampling example:** Nova Escola ~2% production through eval suite daily; Langfuse docs often cite ~5–10% for faithfulness trend monitoring.

### Concrete Scenario (URL)

Langfuse monitoring features + academy pointer:

- https://langfuse.com/docs/observability/overview
- https://langfuse.com/blog/2025-11-12-evals
- https://langfuse.com/resources/engineering/rag-faithfulness-evaluation (sample 5–10%, context on observation)

Phoenix metrics / tracing insights (latency, tokens, exceptions):

- https://arize.com/docs/phoenix/tracing/llm-traces

Phoenix drift discussion (accuracy stable, behavior shifts; embedding-based tools):

- https://github.com/Arize-ai/phoenix/discussions/10442

Production evals case (daily sampled traffic):

- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

### Open Questions

- What drift metrics deserve paging vs weekly review?
- How to attribute cost to product features in multi-tenant agents?
- Can we detect “behavioral collapse” automatically when embeddings look fine?
- SLO design: quality SLOs vs classic latency SLOs for nondeterministic systems?

### Sources

- https://langfuse.com/docs/observability/overview
- https://langfuse.com/blog/2025-11-12-evals
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge
- https://langfuse.com/resources/engineering/rag-faithfulness-evaluation
- https://arize.com/docs/phoenix/tracing/llm-traces
- https://github.com/Arize-ai/phoenix/discussions/10442
- https://hamel.dev/blog/posts/field-guide/
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html
- https://developers.openai.com/api/docs/guides/evaluation-best-practices

---

## Cross-cutting notes for Week 17 synthesis

1. **Judges are products**—design for one failure mode, binary+critique, validate TPR/TNR.
2. **Criteria drift is real**—calibration is continuous; humans redefine “good” as they label.
3. **Code evals first** when objective; judges for residual subjective failures; humans for truth.
4. **Tracing is the substrate**—generations carry tokens/cost; attach context for faithfulness.
5. **Dashboards need quality + cost + latency + drift**—infra green ≠ product healthy.
6. **Online evals sample and triage**; blocking guardrails live in the request path.

---

## Master source list (Week 17)

| Source | URL |
|--------|-----|
| Hamel — LLM-as-a-Judge guide | https://hamel.dev/blog/posts/llm-judge/ |
| Hamel — Your AI Product Needs Evals | https://hamel.dev/blog/posts/evals/ |
| Hamel — Field Guide | https://hamel.dev/blog/posts/field-guide/ |
| Hamel — Evals FAQ | https://hamel.dev/blog/posts/evals-faq/ |
| Hamel — Same model for judge? | https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html |
| Hamel — Production evals case | https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html |
| Shankar et al. — Who Validates the Validators? | https://arxiv.org/abs/2404.12272 |
| G-Eval (EMNLP 2023) | https://aclanthology.org/2023.emnlp-main.153/ |
| OpenAI — Evaluation best practices | https://developers.openai.com/api/docs/guides/evaluation-best-practices |
| OpenAI — Working with evals | https://developers.openai.com/api/docs/guides/evals |
| OpenAI — Evals cookbook | https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals |
| OpenAI — openai/evals | https://github.com/openai/evals |
| Anthropic — Planning to production (public) | https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf |
| Langfuse — Observability overview | https://langfuse.com/docs/observability/overview |
| Langfuse — SDK / generations | https://langfuse.com/docs/observability/sdk/overview |
| Langfuse — LLM-as-a-Judge | https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge |
| Langfuse — Evals blog | https://langfuse.com/blog/2025-11-12-evals |
| Langfuse — Error analysis cookbook | https://langfuse.com/guides/cookbook/error-analysis-llm-applications |
| Phoenix — Tracing | https://arize.com/docs/phoenix/tracing/llm-traces |
| OpenInference spec | https://arize-ai.github.io/openinference/spec/ |
| YouTube — Hamel & Shreya AI evals | https://www.youtube.com/watch?v=BsWxPI9UM4c |
