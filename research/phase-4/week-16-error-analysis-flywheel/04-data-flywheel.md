# 04 — Data flywheel (production → labeled failures → eval set → regression prevention)

> Week 16 — Close the loop so incidents become tests  
> Research notes (raw).

---

## Fundamentals

The eval **flywheel** is Hamel’s “virtuous cycle”: **evaluate quality**, **debug (look at data)**, **change the system** (prompt, tools, RAG, code, later fine-tune). Teams that only do #3 plateau (Lucy: whack-a-mole, vibe checks, 12k-token prompts) ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/); [Field Guide](https://hamel.dev/blog/posts/field-guide/)).

Week 16’s specific loop (error analysis → regression prevention):

```
Production traffic
    → Traces in observability (Week 15 instrumentation)
    → Error analysis / human labels + critiques
    → Failure taxonomy + prioritized fixes
    → Targeted evaluators (code now; LLM judge Week 17)
    → Curated eval / golden set (+ synthetic fill for edges)
    → CI / periodic regression runs
    → Online sampling & monitoring scores
    → New failures mined back into the set
```

Labeled failures do **triple duty** (evals post): measure system quality, **calibrate** automated judges, and **filter/curate** synthetic or fine-tuning data. Expert **critiques** become few-shots for judges and documentation. Field Guide: critiques as few-shots often yield **15–20%** higher human–judge agreement vs prompts without them (Hamel’s consulting observation—not a universal constant).

### Stages and sample sizes

Hamel FAQ [How many examples do I need?](https://hamel.dev/blog/posts/evals-faq/):

| Stage | Guidance |
|-------|----------|
| **1. Error discovery** | ~**100** diverse traces; **≥30** human-annotated first; continue to theoretical saturation |
| **2. Create/validate evaluators** | **Code:** pass + fail examples for every condition + important edges (maybe few). **LLM judge:** **100–200 labeled examples per failure mode**; domain-expert labels; train/dev/test split (10–20% train few-shots, 40–45% dev, 40–45% held-out test); aim **30–50 Pass and 30–50 Fail** in both dev and test when possible; track **TPR/TNR** not raw agreement |
| **3. Repeatable eval set** | Often **≥100** examples covering important workflows + **confirmed failures**; grow with incidents; cheap enough to run often |

Stage 2 judge validation is **Week 17** depth; this week you **collect** the labels and **promote** failures into stage 3 so Week 17 has a set.

**Agreement is a trap metric** (Aakash masterclass / FAQ): if a failure is 10% prevalent, a judge that always predicts pass is **90% accurate**. Measure **TPR** (catch real failures) and **TNR** (don’t flag goods) separately. Honeycomb Query Assistant: Hamel reports **three iterations** to **>90%** human–judge agreement ([Field Guide](https://hamel.dev/blog/posts/field-guide/); details in the LLM-as-judge post). AlignEval (Eugene Yan, cited by Hamel): upload data, binary human labels, compare judges—alignment is an **ongoing conversation**.

### Three levels of evaluation (Lucy)

Hamel’s cost stack ([evals post](https://hamel.dev/blog/posts/evals/)):

| Level | What | Cadence |
|-------|------|---------|
| **1 Unit / assertions** | Fast, cheap, pytest-like; also usable for retries/data cleaning | Every code change (CI) |
| **2 Human & model eval** | Needs traces; binary labels; then judges aligned to humans | Cadence + after meaningful changes |
| **3 A/B / business** | Expensive, slow, true user signal | After significant product changes |

Do not skip Level 1. Rechat: **hundreds** of assertions (listing counts, no UUID leakage). Track results over time (they used Metabase). Pass rate is a **product** decision.

OpenAI: define objective → collect dataset → metrics → run/compare → **continuous evaluation (CE)** on every change, monitor nondeterminism, **grow the set** ([best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)). Log everything to **mine** new cases. (Platform deprecation dates are Week 17/ops concern; the **practice** of CE remains.)

### Production sampling for regression

**Nova Escola** (Lucas Machado, [Hamel notes](https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html)): Brazilian nonprofit lesson planner (~1M MAU, ~200k teachers). After taxonomy-driven judges: **daily suite on ~2% of production traffic** to catch regressions early.

Shreya (Aakash): typically **several code evals in CI**; maybe **one or two** LLM evals in CI; more often **weekly sampled online** LLM judges; watch for new cohorts/document types (legal contracts). You do **not** need a hundred judges.

Langfuse: scores unify human, code, and judge signals; **offline** datasets/experiments (CI) + **online** evaluators with sampling; failing prod traces → dataset items → experiments → keep as regression ([cookbook “what comes next”](https://langfuse.com/guides/cookbook/error-analysis-llm-applications); [evals blog](https://langfuse.com/blog/2025-11-12-evals)). Version **prompts**; pin dataset versions.

Hamel FAQ sampling for **review** (also feeds the flywheel): keep random traces in every batch; targeted sampling for **rare** modes (tool sequence, long traces, retries, known input pattern).

### Cost-benefit: what enters the automated loop

FAQ: **Should I build automated evaluators for every failure mode?** No. Fix unspecified preferences (brevity, format) in the prompt first. Cost hierarchy: assertions/reference checks **cheap**; LLM-as-judge needs 100+ labels, **weekly maintenance**, PM/eng/expert coordination. Automate only failures you will **iterate on repeatedly**—persistent generalization failures, not one-off bugs.

Nova Escola mistake #2: built an eval for “two learning goals instead of one”—**prompt change stopped it**. FAQ on when to automate an evaluator: don’t maintain meta-evals forever for trivia.

### Trust, drift, leakage

Field Guide §5: teams **lose faith** in evals when metrics diverge from production or become uninterpretable, then revert to gut.

- Embrace **criteria drift**; living rubrics.  
- Binary + critiques.  
- Regular human–judge calibration (Week 17).  
- Scale by **strategic sampling**, not by removing humans from hard cases.

**Eval-set leakage:** do not dump the golden set into the **product** model’s few-shots. Hamel judge split: only **train** slice may appear in the **judge** prompt. Keep product prompts and eval sets versioned separately.

**Stale golden sets:** offline-only suites miss live drift. Remedy: sampled production + incident promotion (Nova Escola 2%; Langfuse online evals).

**Fine-tune on every failure:** may lift the model; risks data quality, leakage, slower than prompt+eval. Flywheel **can** feed fine-tuning later (Lucy editable outputs for curation)—not the default Week 16 action.

### Roadmaps: experiments, not features

Field Guide §6: traditional feature roadmaps fail for AI. Bryan Bischof **capability funnel**; Eugene Yan timeboxed feasibility. **Evaluation infrastructure** is what makes experiment cadences honest (GitHub Copilot offline tests against repo unit tests—public Hamel telling). Stakeholder communication: timeboxes and outcomes, not fake ship dates. Share **failures** as learning. This is why the flywheel is organizational, not just a dataset file.

---

## Alternatives & Tradeoffs

| Loop design | Pros | Cons |
|-------------|------|------|
| Offline-only golden set | Stable CI | Goes stale; misses live drift |
| Online judges on 100% traffic | Dense signal | Costly; uncalibrated noise |
| Sampled online (e.g. **2–10%**) + offline regression | Balanced cost/coverage | Need a sampling strategy (Nova Escola 2% is an existence proof, not a universal optimum) |
| User thumbs only | Cheap | Sparse, biased, late |
| Fine-tune on every failure | May lift model | Quality/leakage; slower than prompt+eval |
| Generic vendor scores as the loop | Pretty dashboards | Field Guide tools trap |
| Eval-driven imagined suite | Looks complete at launch | Nova Escola wasted labels |

---

## Necessity

Without a flywheel:

- Eval sets freeze at launch and stop catching new user behaviors.  
- Production incidents don’t become regression tests (you rediscover the same failure quarterly).  
- Judges drift from human preference as the product changes.  
- Stakeholders lose trust (Hamel: “how do you know that metric?”).  
- Criteria drift proceeds without versioned labels (Shankar et al.).

Without production in the loop:

- Synthetic-only sets overfit imagined users.  
- Rates are lies.

Without labels feeding CI:

- Prompt “fixes” silently break other taxonomy categories (Lucy whack-a-mole). Hamel/Shreya: a **suite** lets you see whether iterating on handoff **broke** date handling.

---

## Industry Practice

**Common:** One-time golden set; occasional manual review after outages; thumbs in Discord.

**Strong:**

- Every significant failure → ticket + **dataset example** + evaluator-or-monitor decision.  
- Version prompts in observability; tie eval runs to prompt/model versions.  
- Continuous evaluation on change (OpenAI CE) + scheduled production samples.  
- AlignEval-style binary human vs judge until alignment is trustworthy (Week 17 execution).  
- Langfuse: annotation queues → datasets → experiments → online evaluators with sampling rules.  
- Custom admin UI so domain experts edit prompts **in the real app context** (Field Guide “integrated prompt environments”)—playgrounds lack your tools/RAG.  
- Experiment-count roadmaps; weekly error log for leadership.  
- Copilot-style: invest in harness so thousands of experiments are **measurable**.

Langfuse [2025-11-12 evals blog](https://langfuse.com/blog/2025-11-12-evals): product direction toward unified human/code/judge scores, experiments, online evals—use as **map of industry tooling**, not as a requirement to adopt Langfuse.

---

## Concrete Scenario (URL)

**Flywheel narrative (Lucy cycle; critiques → synthetic reuse).**  
https://hamel.dev/blog/posts/evals/  
https://hamel.dev/blog/posts/field-guide/

**Production sampling for regression (Nova Escola daily ~2%).**  
https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

**Sample sizes per pipeline stage.**  
https://hamel.dev/blog/posts/evals-faq/

**Langfuse: scores, online judges, sampling; error analysis → versioned prompts → re-analysis after changes.**  
https://langfuse.com/blog/2025-11-12-evals  
https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
https://langfuse.com/guides/cookbook/error-analysis-llm-applications

**OpenAI CE + grow the set; log mining.**  
https://developers.openai.com/api/docs/guides/evaluation-best-practices

**Lenny / Aakash: from taxonomy → handoff judge → score production → iterate without breaking other evals.**  
https://www.youtube.com/watch?v=BsWxPI9UM4c  
https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
https://www.lennysnewsletter.com/p/why-ai-evals-are-the-hottest-new-skill  

**Honeycomb alignment iterations.**  
https://hamel.dev/blog/posts/field-guide/  
https://hamel.dev/blog/posts/llm-judge/

---

## Open Questions

- Optimal production sample rate by traffic volume and judge cost? (2% is one published point.)  
- How to prevent eval-set leakage into product few-shots?  
- Ownership: eng vs PM vs domain expert for flywheel **maintenance** week to week?  
- When does the flywheel justify **fine-tuning** vs continued prompt/RAG iteration?  
- How to keep historical dashboards comparable when the taxonomy versions?  
- Multi-tenant enterprise: whose production sample (which customer) enters the shared golden set without leaking confidential traces?

---

## Sources

- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/field-guide/  
- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/llm-judge/  
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html  
- https://langfuse.com/blog/2025-11-12-evals  
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications  
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
- https://arxiv.org/abs/2404.12272  
