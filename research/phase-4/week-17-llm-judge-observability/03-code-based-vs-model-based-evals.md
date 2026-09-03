# 03 — Code-based vs model-based evals (when each is appropriate)

> Week 17 — Pick the cheapest evaluator that matches the failure  
> Research notes (raw). Judge design/calibration: files [01](01-llm-as-judge-design.md)–[02](02-judge-alignment-calibration.md).

---

## Fundamentals

Two automated evaluator families (Hamel/Shreya teaching, Langfuse, OpenAI graders) plus humans:

| Type | Mechanism | Best for |
|------|-----------|----------|
| **Code-based / deterministic** | Assertions, regex, JSON schema, exact match, tool-arg checks, length, allowlists, citation-ID subset | Objective, unambiguous failures |
| **Model-based / LLM judge** | Prompted LLM (or classifier) scores output | Subjective, semantic, domain judgment |
| **Human** | Expert review | Ground truth, calibration, high-stakes, rubric discovery |

Langfuse also lists **user feedback** (sparse, clear) and **implicit feedback** (retries, abandonment — noisy) as production signals that are neither code nor judge ([evals blog](https://langfuse.com/blog/2025-11-12-evals)).

### Decision rule (repeat until muscle memory)

Repeated across Hamel FAQ, Langfuse error-analysis cookbook, Lenny’s Podcast ([`BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c)), Aakash Gupta write-up:

1. Can you **just fix** the bug in prompt/tools/code? **Do that first.**  
2. Else, if a **deterministic rule** catches it → **code eval** (cheap, CI-friendly).  
3. Else, if it needs **judgment** → **LLM judge**, then calibrate (file 02).  
4. **Safety/compliance** may need an evaluator **as guardrail** even after fixing (in-request), not only as a monitor.

Langfuse cookbook after taxonomy: **fix / evaluator / monitor**. Low-rate categories may only need monitoring. Do not build a judge for a 5% incomplete-resolution tail if nobody will iterate on it weekly.

Hamel FAQ: **Should I build automated evaluators for every failure mode?** **No.** Cost hierarchy: assertions **cheap**; LLM-as-judge needs **100+ labels**, **weekly maintenance**, PM/eng/expert coordination. Automate failures you will **iterate on repeatedly**.

Nova Escola lesson: they built an eval for “emit exactly one learning goal” when a **prompt change** deleted the double-goal bug — wasted meta-eval.

### What “code-based” looks like in 2026 tooling

**Langfuse code evaluators** (blog, July 2026 tooling): Python or TypeScript `evaluate(ctx) -> scores`; run on live observations or experiments; **no network**; **stdlib only**; **≤2 seconds** — keeps them deterministic. Examples: exact match, PII regex, numeric tolerance.

**OpenAI Evals API** ([working with evals](https://developers.openai.com/api/docs/guides/evals)): `testing_criteria` lists graders. Documented workhorse: **`string_check`** (e.g. exact match to `correct_label`, or `contains` “refund”). Combine multiple graders. Cookbook: getting started with evals ([cookbook](https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals)). GitHub [openai/evals](https://github.com/openai/evals) — registry of eval implementations (legal, public). Platform **deprecation**: read-only **2026-10-31**, shutdown **2026-11-30**; concepts of deterministic vs model graders **port**. OpenAI also points new users at **Datasets** as a more iterative environment.

**Hamel Level 1** ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)): pytest-like assertions; Rechat **hundreds** of checks (listing counts, no UUID leakage). Run on **every code change**.

**Agent tool-call evals** (Week 15 adjacency): name, arguments, schema, policy order — **code**; semantic appropriateness of *which* tool — often **judge**.

**RAG:** citation IDs ⊆ retrieved IDs, JSON shape, “must not claim X” substring — **code**; faithfulness / “did we ask a clarifying question” — **judge** (Langfuse: deterministic overlap is a **pre-filter**, not faithfulness).

### What “model-based” looks like

OpenAI: **model graders** for style/content criteria that strings cannot capture; give the grader room to reason; validate vs humans. Best practices: LLMs are better at **pairwise, classification, criteria scoring** than open-ended generation of a quality number.

Langfuse: managed catalog (incl. Ragas partners) **or** custom `{{variables}}`; boolean/categorical/numeric + reasoning. Stack a **cheap code pre-screen** in front of a judge to cut cost (evals blog).

Anthropic: robust production evals **combine** rule-based + LLM-powered + targeted human ([public PDF](https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf)).

### CI vs online

Talk write-ups / Shreya (Aakash): **several code evals in CI**; **one or two** LLM evals in CI **maybe**; more often **weekly sampled online** judges. Flaky LLM judges in CI (nondeterminism, rate limits) are a real ops tax — Langfuse production judges are **async** with retry/`Delayed` on rate limits; that is **monitoring**, not a blocking unit test.

Hybrid: **code prefilter → judge** (medium cost/latency). Property-based / generated inputs (Week 16 synthetic) still need **code or judge** on the **real** pipeline outputs.

---

## Alternatives & Tradeoffs

| Choice | Cost | Latency | Brittleness | Human correlation effort |
|--------|------|---------|-------------|---------------------------|
| **Code assert** | ≈0 | ms | High if format varies | Low (examples for edges) |
| **LLM judge** | $$ (~$0.01–0.10/call, Langfuse) | seconds | Prompt-sensitive | High (100–200 labels) |
| **Human** | $$$ | hours/days | Rater variance | N/A (is the reference) |
| **Hybrid: code prefilter → judge** | Medium | Medium | Manageable | Medium |
| **Fine-tuned classifier** | Cheap at serve | ms | Needs labels; drifts | High upfront |
| **Ragas / library metrics** | Low–medium | seconds | Generic dimensions | Still calibrate if used as gates |

| CI pattern | Pros | Cons |
|------------|------|------|
| Code-only CI | Stable, fast | Blind to persona/faithfulness |
| LLM judges on every PR | Dense | Cost, flake, rate limits |
| Code in CI + sampled online judges | Practical (Lenny/Shreya) | Online lag; statistical noise |

---

## Necessity

**Code-only** → blind to persona, tone, partial helpfulness, faithfulness nuance.  
**Judge-only** → expensive, flaky CI, meta-eval debt for failures `json.loads` would catch.  
**Neither** → flying blind.  
**Humans-only in production** → cannot scale (Nova Escola needed sampled automation *after* the rubric existed).

---

## Industry Practice

**Code examples:** valid JSON; required sections present; tool name/args schema; PII regex; max tokens; citation IDs ⊆ retrieved IDs; “must not claim X”; exact category label (`Hardware`/`Software`/`Other` — OpenAI `string_check` tutorial).

**Judge examples:** should have asked clarifying question; grounded in retrieved context; correct empathy/persona; summary coherence (if you insist on NLG research metrics, still calibrate).

**Langfuse:** code evaluators + LLM-as-judge; **observation-level** targeting (evaluate only `GENERATION` named `final-response`); sampling rules; scores unify all methods in one dashboard.

**OpenAI evals:** describe task → dataset → `testing_criteria` graders → analyze → iterate prompt. Mix grader types. Cookbook walks model grading + human validation.

**Hamel:** Level 1 assertions **every change**; Level 2 human/model on a cadence; Level 3 A/B rarely.

---

## Concrete Scenario (URL)

**Hamel/Shreya on code vs LLM evals (talk + FAQ + write-up).**  
https://www.youtube.com/watch?v=BsWxPI9UM4c  
https://hamel.dev/blog/posts/evals-faq/  
https://www.aakashg.com/ai-evals-masterclass-with-hamel-shreya/  
https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/

**Langfuse decision table after taxonomy + code vs judge methods.**  
https://langfuse.com/guides/cookbook/error-analysis-llm-applications  
https://langfuse.com/blog/2025-11-12-evals  
https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge

**OpenAI working with evals / graders / cookbook / GitHub.**  
https://developers.openai.com/api/docs/guides/evals  
https://developers.openai.com/api/docs/guides/evaluation-best-practices  
https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals  
https://github.com/openai/evals

**Nova Escola — don’t eval a bug you should prompt-fix.**  
https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

---

## Open Questions

- Flaky LLM judges in CI: retries, temperature 0, caching — what’s an acceptable flake rate?  
- Learned classifiers (fine-tuned small models) as middle ground vs prompt judges?  
- Property-based testing for agents vs static golden sets?  
- How to version **code** evaluators next to prompts so CI failures are attributable?  
- After OpenAI Evals platform shutdown, where do teams park portable `string_check` + model-grader graphs (Datasets, Langfuse experiments, pytest)?

---

## Sources

- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/llm-judge/  
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications  
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
- https://langfuse.com/blog/2025-11-12-evals  
- https://developers.openai.com/api/docs/guides/evals  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals  
- https://github.com/openai/evals  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
- https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf  
