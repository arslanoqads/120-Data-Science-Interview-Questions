# 02 — Judge alignment / calibration against expert-labeled examples

> Week 17 — Prove the judge shadows Week 16 labels; keep proving it as criteria drift  
> Research notes (raw). Judge *prompt shape*: file [01](01-llm-as-judge-design.md).

---

## Fundamentals

**Alignment** (product sense) = the judge’s labels match the **domain expert’s** labels on **held-out** data. **Calibration** (ops sense) = ongoing checks so that trust remains as data, prompts, models, and **criteria** drift.

This is not “the model outputs a well-calibrated probability 0.73.” You may later use token probs (G-Eval-style); Week 17’s bar is **classifier performance vs humans**.

Hamel (YouTube [`DZxaPNYi_k0`](https://www.youtube.com/watch?v=DZxaPNYi_k0)): if you do not measure the judge against humans, **evals lose trust**.

### Critique-shadowing measurement loop

From [llm-judge](https://hamel.dev/blog/posts/llm-judge/) + [FAQ sample sizes](https://hamel.dev/blog/posts/evals-faq/):

1. Expert labels Pass/Fail + critique (Week 16 gold).  
2. Judge prompt asks for the **same** decision (+ rationale). Few-shots from **train** split only.  
3. Iterate on **dev** where judge ≠ expert (read both critiques; fix rubric or examples).  
4. Report **True Positive Rate** and **True Negative Rate** on **held-out test**.  
5. Only then run the judge on unseen synthetic/production traffic to estimate **failure rates**.

**Agreement is a trap** (Aakash masterclass / Hamel warning on Honeycomb): if failures are 10% prevalent, a judge that **always predicts Pass** is **90% accurate**. Honeycomb used raw agreement only because the set was **~50/50**. Default reporting:

| Metric | Meaning for a **Fail = positive** (catching bad outputs) |
|--------|----------------------------------------------------------|
| **TPR** (recall / sensitivity) | Share of expert-Fails the judge also Fails — **catches real failures** |
| **TNR** (specificity) | Share of expert-Passes the judge also Passes — **doesn’t flag goods** |
| Precision | Of judge-Fails, how many are real — useful when paging humans |
| Accuracy / % agreement | **Do not gate on this** under imbalance |
| Cohen’s κ | Better than raw agreement; still **hides asymmetric errors** if used alone |

Define the positive class explicitly (Fail vs Pass) in the alignment report next to the prompt version.

### Splits and sample size

Hamel:

| Stage | Guidance |
|-------|----------|
| Discover failure modes / write rubric | ~30+ until no new modes (Week 16) |
| **Validate a judge** | **~100–200 labeled examples per failure mode**; **<60** often has CIs too wide to conclude anything |
| Split | **~10–20% train** (few-shot), **~40–45% dev**, **~40–45% final test** |
| Balance | Aim **~30–50 Pass and 30–50 Fail** in **both** dev and test when possible |

Leakage: few-shots must not include test items. Production online scores are **not** the alignment set — they estimate **prevalence**, biased by TPR/TNR.

Langfuse: calibrate on a **small human-annotated sample** before trusting trend lines; typical judge **$0.01–0.10** per call — sample production ([LLM-as-a-Judge FAQ](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge); [evals blog](https://langfuse.com/blog/2025-11-12-evals)). Faithfulness write-up: calibrate **20–50** answers vs a person **once for rubric wording**, then still keep a proper held-out set for gates.

### Criteria drift (why calibration is not a one-shot project)

Shankar et al., *Who Validates the Validators?* (UIST 2024, [arXiv:2404.12272](https://arxiv.org/abs/2404.12272)): **EvalGen** generates candidate assertions/prompts; humans grade a subset; the system selects implementations that maximize alignment (coverage vs false-failure tradeoff). Qualitative finding: **grading outputs changes the criteria** — **criteria drift**. Implication: you cannot fully specify the rubric a priori; Week 16 open coding made that explicit; Week 17 **must re-label** when the expert’s taste or the product moves.

Hamel quotes the paper in the judge guide: people need outputs to define criteria and criteria to grade outputs.

Nova Escola ([Hamel notes](https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html)): two annotators initially agreed **less often than chance** → rewrite rubric **with pedagogical experts** → relabel → **then** automate judges. If IAA is broken, **alignment to “humans” is undefined**.

OpenAI: **maintain agreement** between automated scoring and human feedback; continuous evaluation; anti-pattern = ignoring human feedback ([best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)).

### Tooling for the alignment conversation

- **Spreadsheets** (Honeycomb): expert vs judge side by side.  
- **AlignEval** (Eugene Yan, recommended by Hamel): upload data, binary human labels, compare judges — alignment as an **ongoing conversation** ([Field Guide](https://hamel.dev/blog/posts/field-guide/)).  
- Langfuse **annotation queues** + scores of type human vs judge on the **same observation**.  
- Phoenix **annotations** on traces.  
- Version **judge prompts** (Langfuse evaluators create a new version on update; rules keep sampling). Store the **alignment report** next to the version.

### Recalibration triggers

Hamel: human review at **regular intervals** and whenever something **material** changes (model upgrade, major prompt, new cohort). After early iterations, bias sampling toward **errors** but **keep some random**. Langfuse: updating the **project default judge model** changes **every** evaluator using it — that is a **recalibration event**, not a silent upgrade.

Anthropic (*Planning to production*, public PDF): robust systems combine rule-based, model-based, and **targeted human** grading; larger models can help evaluate smaller ones; **decompose** evals for frontier models.

---

## Alternatives & Tradeoffs

| Calibration practice | Pros | Cons |
|----------------------|------|------|
| **Held-out TPR/TNR gates** | Honest; imbalance-aware | Needs enough Fail examples |
| Cohen’s κ / Spearman only | Single number; G-Eval uses Spearman vs humans | Hides asymmetric errors; research ≠ product gate |
| Periodic human audits (weekly sample) | Catches drift | Ongoing cost |
| AlignEval / annotation-queue loops | Fast iteration | Tooling investment |
| Langfuse “small sample then trust trends” | Practical | Underpowered if you skip a real test split |
| No calibration (“vendor template”) | Zero effort | Untrusted metrics |
| Bayesian-adjust online scores by known TPR/TNR | Statistically nicer prevalence | Rarely implemented; still need labels |

---

## Necessity

Without calibration:

- Online “quality” charts are fiction.  
- You “fix” regressions that are judge noise — or miss real ones.  
- Multi-annotator chaos: if two humans disagree worse than chance, the judge cannot align to a nonexistent standard — **fix the rubric first** (Nova Escola).  
- Criteria drift happens **anyway** (EvalGen); unmeasured drift is silent policy change.

---

## Industry Practice

**Common:** Spot-check 10 examples once; ship; never re-check after a model bump.

**Strong:**

- Version judge prompts; store TPR/TNR (with class definition) next to prompt version and dataset version.  
- Recalibrate on **app or judge** model upgrades and on product/taxonomy changes.  
- Use **disagreements** as gold for taxonomy/rubric updates (criteria drift as a **feature**).  
- Separate **offline experiment** alignment from **online sampled** monitoring.  
- OpenAI: log everything; grow the set; CE on change. Note: **Evals platform** read-only **2026-10-31**, shutdown **2026-11-30** — the *practice* of human–auto agreement remains; don’t couple the course to that UI.  
- Field Guide: teams **lose faith** when metrics diverge from production; binary + critiques + regular human–judge calibration + **strategic sampling** (don’t remove humans from hard cases).

**Langfuse operationalization:** test evaluator on representative observations in the UI; inspect score + reasoning; iterate mappings. Production: rules with **sampling rate**. Debug failed judges via their traces.

**G-Eval’s Spearman 0.514** is **not** your gate. It is evidence that CoT judges *can* correlate with humans on summarization *in that paper’s setup*. Your gate is **your** expert’s held-out TPR/TNR.

---

## Concrete Scenario (URL)

**Honeycomb Query Assistant (Hamel)** — three iterations; agreement **and** the imbalance warning.  
https://hamel.dev/blog/posts/llm-judge/

**Nova Escola** — IAA < chance → expert rubric → relabel → judges; daily **2%** prod.  
https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

**AlignEval / ongoing calibration (Field Guide).**  
https://hamel.dev/blog/posts/field-guide/

**FAQ — TPR/TNR; same model; sample sizes.**  
https://hamel.dev/blog/posts/evals-faq/  
https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html

**EvalGen / criteria drift.**  
https://arxiv.org/abs/2404.12272  
https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf

**Langfuse — calibrate before trend lines; judge traces.**  
https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
https://langfuse.com/blog/2025-11-12-evals

**OpenAI — maintain agreement; CE.**  
https://developers.openai.com/api/docs/guides/evaluation-best-practices

**YouTube — classifier vs humans.**  
https://www.youtube.com/watch?v=DZxaPNYi_k0

**Anthropic — rule + model + human triad (public PDF).**  
https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf

---

## Open Questions

- Minimum labeled set for high-stakes domains (healthcare, finance) beyond the 100–200 heuristic?  
- How to calibrate when the “expert” is a **committee** with persistent disagreement (beyond Nova Escola: rewrite rubric)?  
- Active learning: which disagreements to send to humans next?  
- Should online scores be **prevalence-adjusted** by measured TPR/TNR?  
- When is κ + TPR/TNR enough vs a full confusion matrix in the weekly review?  
- Project-default judge model upgrades: auto-recalibrate or pin per evaluator?

---

## Sources

- https://hamel.dev/blog/posts/llm-judge/  
- https://hamel.dev/blog/posts/field-guide/  
- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html  
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html  
- https://arxiv.org/abs/2404.12272  
- https://langfuse.com/blog/2025-11-12-evals  
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf  
- https://www.youtube.com/watch?v=DZxaPNYi_k0  
- https://aclanthology.org/2023.emnlp-main.153/  
