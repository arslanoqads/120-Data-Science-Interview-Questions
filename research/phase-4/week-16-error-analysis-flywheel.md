# Week 16 — Error Analysis & the Data Flywheel

Raw source material for LLM product evals: error-analysis-first workflows, open/axial coding taxonomies, synthetic data for edge cases, and the production → labels → eval set → regression-prevention flywheel.

**Source policy:** Legal/public sources only (hamel.dev, Shreya Shankar public papers, Langfuse docs, OpenAI/Anthropic public guides, conference talks). No pirate PDFs.

---

## Concept A — Error-analysis-first workflow (read 20–50 real outputs before metrics)

### Fundamentals

Error analysis is the practice of manually reading real application traces (or outputs) and writing free-text notes about what went wrong *before* inventing automated metrics. Hamel Husain and Shreya Shankar treat it as the highest-ROI activity in product evals: it decides *which* evals to write, grounded in failure modes unique to your app and data, instead of generic “helpfulness / hallucination / toxicity” scores that platforms push by default.

Minimum viable loop (Hamel FAQ):

1. Instrument so you have traces (prompt, tools, retrieval, final answer).
2. Sample a diverse set (~100 working pool; annotate ≥30 yourself first).
3. Spend ~30 minutes reading **20–50** outputs after any significant change.
4. Use one domain expert (“benevolent dictator”) as the quality decision maker.
5. Only then turn recurring failures into code assertions or LLM judges.

OpenAI’s evaluation best practices converge: adopt eval-driven development, design task-specific evals, log everything so you can mine production for cases, and treat evaluation as continuous—not a one-shot dashboard.

### Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **Error analysis → targeted evals** | Metrics match real user pain; avoids vanity scores | Requires domain expert time; slower to “look automated” |
| **Generic LLM-judge dashboards first** | Fast to wire; vendor UI looks mature | Measures the wrong things; false confidence; criteria drift ignored |
| **Unit tests / golden answers only** | Cheap CI; deterministic | Misses subjective / multi-turn / tool failures |
| **A/B or business metrics only** | Ties to revenue/NPS | Slow signal; hard to debug *why* quality moved |
| **Delegate first pass entirely to an LLM** | Scales annotation | Biases categories early; misses product taste (Hamel/Langfuse: humans do first 30–50) |

Tradeoff: teams that skip reading traces often build evaluators for failures that never appear—or miss the failure that dominates production (Nova Escola case: rubric written before error analysis wasted labeling).

### Necessity

If you skip error analysis:

- You optimize for metrics that don’t correlate with user success.
- You build LLM judges for bugs a one-line prompt fix would kill.
- Inter-annotator agreement collapses because “good” was never defined on real outputs (criteria drift — Shankar et al.).
- Regressions ship silently because CI only checks format/JSON, not product failures.

### Industry Practice

**Common:** Trace into Langfuse/Phoenix/Braintrust, glance at a few bad traces after user tickets, add a generic judge.

**Strong / senior:**

- Domain expert owns pass/fail + critique.
- Re-run full error analysis after prompt/model/feature changes; between cycles, weekly sample of 10–20 outlier traces (long sessions, retries, low scores).
- Fix obvious prompt/tool bugs *before* building evaluators (Langfuse cookbook decision tree).
- Budget: Hamel reports 60–80% of development time on looking at data / error analysis in consulting projects—not building dashboards.

### Concrete Scenario (URL)

**Langfuse “Dad Tech Support” error analysis cookbook** — end-to-end on a phone tech-support chatbot with 505 traces / 478 sessions. They sample ~100 stratified traces (multi-turn, latency, cost tiers), open-code 30–50, build a taxonomy, quantify rates (e.g. `impersonates_child` ~58%), then decide prompt fix vs LLM-judge vs monitor.

- https://langfuse.com/guides/cookbook/error-analysis-llm-applications

**Hamel/Shreya process definition:**

- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html

**Nova Escola production case (rubric-before-analysis mistake):**

- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

### Open Questions

- How much of early error analysis can safely be agent-assisted without biasing the taxonomy?
- What’s the right cadence for mature vs greenfield products (weekly vs monthly)?
- When is random sampling enough vs clustering / feedback-sorted sampling?
- Can product managers without ML background own the benevolent-dictator role at scale?

### Sources

- https://hamel.dev/blog/posts/evals-faq/
- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html
- https://hamel.dev/blog/posts/evals/
- https://hamel.dev/blog/posts/field-guide/
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications
- https://developers.openai.com/api/docs/guides/evaluation-best-practices
- https://www.youtube.com/watch?v=BsWxPI9UM4c (Hamel & Shreya, Lenny’s Podcast / AI evals talk)

---

## Concept B — Open coding & taxonomy building (failure modes)

### Fundamentals

Borrowed from qualitative research:

1. **Open coding** — Read each trace end-to-end; write short free-text observations of anything wrong, unexpected, or bad for the user. No predefined category list. Prefer describing *behavior* (“bot said it can’t look things up”) over diagnosing root cause (“web search broken”). Early on, note the **first** failure (upstream errors cascade).

2. **Axial coding** — Group open codes into a **failure taxonomy**: 5–10 named categories, each with a one-sentence definition clear enough for another person to apply consistently. Categories should be binary/testable, distinct (minimal overlap), and grounded in observed data—not theoretical “hallucination” buckets.

3. **Label & quantify** — Relabel the sample with boolean flags per category; compute failure rates; prioritize by rate × business impact.

4. **Theoretical saturation** — Stop when new traces don’t add or reshape categories (rule of thumb: no new category in last ~20 traces; ~100 total often enough for first pass).

Hamel/Shreya recommend annotating ≥30 yourself before letting an agent propose similar failures. LLMs help with clustering drafts; humans must split groups that share surface form but different root causes (Langfuse: passive identity non-disclosure vs active child impersonation).

### Alternatives & Tradeoffs

| Taxonomy style | When useful | Failure mode |
|----------------|-------------|--------------|
| App-specific (`missing_device_lookup`, `denied_scope`) | Actionable fixes & evaluators | Takes expert time |
| Generic (`hallucination`, `toxicity`, `helpfulness`) | Cross-product comparison / safety baselines | Not actionable; confirmation bias |
| Multi-label every independent failure | Rich analysis | Annotator fatigue; cascade confusion |
| First-failure-only | Faster; focuses root cause | May undercount co-occurring issues |
| LLM-proposed clusters unreviewed | Speed | Conflates root causes |

### Necessity

Without a grounded taxonomy:

- Teams argue about vibes instead of countable failure rates.
- Evaluators multiply without ownership (“who owns helpfulness?”).
- Prompt fixes and CI tests don’t map to observed production pain.
- Shankar’s **criteria drift** bites: people need outputs to define criteria, and criteria to grade outputs—open coding makes that loop explicit instead of pretending rubrics exist a priori.

### Industry Practice

**Common:** Spreadsheet of thumbs-up/down with ad-hoc tags.

**Strong:**

- Score configs in Langfuse/Phoenix annotation queues: `open_coding` (text) + `pass_fail` + later boolean per category.
- Name categories after *what broke* (`identity_not_disclosed`), not abstract quality.
- After taxonomy: for each category decide **fix prompt/code**, **build evaluator**, or **monitor only** (Langfuse step 5).
- Revisit taxonomy when distribution shifts after model/prompt changes.

### Concrete Scenario (URL)

Dad Tech Support taxonomy (after two refinement rounds) included `identity_not_disclosed`, `impersonates_child`, `missing_device_lookup`, `too_verbose`, `tone_persona_off`, `missing_clarifying_question`, `incomplete_resolution`, `denied_scope` — with failure-rate chart driving decisions (most identity issues → prompt fix; judgment-heavy device lookup → LLM-as-judge).

- https://langfuse.com/guides/cookbook/error-analysis-llm-applications

Shankar et al., *Who Validates the Validators?* (UIST 2024 / arXiv:2404.12272) — criteria drift and why criteria cannot be fully specified before seeing outputs:

- https://arxiv.org/abs/2404.12272
- https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf

### Open Questions

- Best practices for multi-annotator agreement once past a single benevolent dictator?
- How to version taxonomies as products evolve without breaking historical dashboards?
- When should failure modes be hierarchical vs flat?
- How to handle agent trajectories (multi-span) vs single-generation annotation units?

### Sources

- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications
- https://arxiv.org/abs/2404.12272
- https://www.aakashg.com/ai-evals-masterclass-with-hamel-shreya/ (public write-up of Hamel/Shreya talk)
- https://www.youtube.com/watch?v=BsWxPI9UM4c

---

## Concept C — Synthetic data to surface edge cases

### Fundamentals

Synthetic data here means **LLM-generated user inputs** (not synthetic “gold” answers). Workflow:

1. Define **dimensions** (e.g. feature × scenario × persona; or dietary restriction × cuisine × complexity).
2. Write ~20 dimension tuples by hand to understand the space.
3. Scale: generate more tuples, then separately convert tuples → natural-language queries (two-step generation avoids repetitive phrasing).
4. Run queries through the **real** system; capture full traces.
5. Use those traces for open coding / judge calibration—not as fake ground-truth completions.

Use cases (Hamel FAQ): bootstrap error analysis before production traffic; force rare edge cases that production undersamples.

**Limits:** Synthetic data cannot estimate production failure *rates*; can miss domain-specific realism; must be validated against real traffic ASAP.

### Alternatives & Tradeoffs

| Data source | Strength | Weakness |
|-------------|----------|----------|
| Production sampling | Real distribution, rates | Cold start; privacy; rare edges missing |
| Synthetic inputs → real system | Coverage of rare combos; fast | Distribution ≠ production; domain blind spots |
| Purchased / vendor datasets | Scale | Often generic; weak product fit |
| Human-written cases only | High quality | Expensive; incomplete coverage |
| Fully synthetic I/O (fake answers) | Cheap | Useless for product evals of *your* pipeline |

Cross-product + filter vs direct LLM tuple generation: cross-product guarantees rare edges; direct generation is more realistic but misses long-tail combos.

### Necessity

Without synthetic (or other stress) data:

- Pre-launch products have nothing to open-code.
- Known rare failures never appear in random samples of 100.
- Eval sets overfit to “happy path” traffic and miss regressions on edges.

Without validating synthetic against real:

- You optimize for LLM-imagined users and ship into a different distribution.

### Industry Practice

**Common:** “Give me 50 test queries” one-shot prompts → repetitive, generic queries.

**Strong:**

- Structured dimensions; two-step generation; feed through full stack with logging.
- Mix synthetic + production; Hex (cited by Hamel) uses synthetic prompts heavily for evals.
- Don’t synthesize tests for bugs you can fix immediately (fix prompt first).
- ~100 diverse traces is a useful starting pool for discovery.

### Concrete Scenario (URL)

Hamel’s LLM-as-judge guide: features/scenarios/personas tables and example prompts that generate frustrated-customer invalid order numbers, ambiguous meeting requests, etc., then run through the live app.

- https://hamel.dev/blog/posts/llm-judge/

Synthetic methodology FAQ:

- https://hamel.dev/blog/posts/evals-faq/ (section: “What is the best approach for generating synthetic data?”)

OpenAI eval best practices — collect synthetic, domain-specific, purchased, human-curated, production, and historical data as complementary sources:

- https://developers.openai.com/api/docs/guides/evaluation-best-practices

### Open Questions

- How to measure “synthetic realism” quantitatively for specialized domains (medicine, law)?
- Can adversarial / red-team generators replace dimension design?
- Privacy: when is synthetic a safer substitute for production logs in vendor tools?
- Interaction with agentic systems: synthetic *trajectories* vs single-turn queries?

### Sources

- https://hamel.dev/blog/posts/llm-judge/
- https://hamel.dev/blog/posts/evals-faq/
- https://hamel.dev/blog/posts/field-guide/
- https://hamel.dev/blog/posts/evals/
- https://developers.openai.com/api/docs/guides/evaluation-best-practices

---

## Concept D — Data flywheel (production → labeled failures → eval set → regression prevention)

### Fundamentals

The eval **flywheel** (Hamel *Your AI Product Needs Evals* / Field Guide):

```
Production traffic
    → Traces in observability
    → Error analysis / human labels + critiques
    → Failure taxonomy + prioritized fixes
    → Targeted evaluators (code + LLM judge)
    → Curated eval / golden set (+ synthetic fill)
    → CI / periodic regression runs
    → Online sampling & monitoring scores
    → New failures mined back into the set
```

Labeled failures do triple duty: measure system quality, calibrate automated judges, and filter/curate synthetic or fine-tuning data. Critiques from experts become few-shot material for judges and docs for the team.

Stages and sample sizes (Hamel FAQ “How many examples”):

| Stage | Guidance |
|-------|----------|
| Error discovery | ~100 diverse traces; ≥30 human-annotated first |
| Validate LLM judge | ~100–200 labeled examples per failure mode; train/dev/test split; track TPR/TNR not raw accuracy |
| Repeatable eval set | Often ≥100 examples covering workflows + confirmed failures; grow with incidents |

Nova Escola / Lucas Machado case: daily suite on ~2% of production traffic to catch regressions early after taxonomy-driven judges.

### Alternatives & Tradeoffs

| Loop design | Pros | Cons |
|-------------|------|------|
| Offline-only golden set | Stable CI | Goes stale; misses live drift |
| Online judges on 100% traffic | Dense signal | Costly; uncalibrated noise |
| Sampled online (e.g. 2–10%) + offline regression | Balanced cost/coverage | Need good sampling strategy |
| User thumbs only | Cheap | Sparse, biased, late |
| Fine-tune on every failure | May lift model | Data quality / leakage risks; slower than prompt+eval |

Cost-benefit: automate an evaluator only when the failure is recurrent, high-impact, and not trivially fixed—otherwise you maintain meta-evals forever.

### Necessity

Without a flywheel:

- Eval sets freeze at launch and stop catching new user behaviors.
- Production incidents don’t become regression tests.
- Judges drift from human preference as the product changes.
- Teams rediscover the same failure every quarter.

### Industry Practice

**Common:** One-time golden set; occasional manual review after outages.

**Strong:**

- Every significant failure → ticket + dataset example + evaluator or monitor decision.
- Version prompts in observability; tie eval runs to prompt/model versions.
- Continuous evaluation on change (OpenAI CE guidance) + scheduled production samples.
- AlignEval-style workflows (cited by Hamel): binary human labels vs judge, iterate until alignment trustworthy.
- Langfuse: annotation queues → datasets → experiments → online evaluators with sampling rules.

### Concrete Scenario (URL)

**Flywheel narrative & critique→synthetic reuse:**

- https://hamel.dev/blog/posts/evals/
- https://hamel.dev/blog/posts/field-guide/

**Production sampling for regression (Nova Escola daily 2%):**

- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

**Langfuse: scores unify human, code, and judge signals for dashboards/alerts; online judges with sampling:**

- https://langfuse.com/blog/2025-11-12-evals
- https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge

### Open Questions

- Optimal production sample rate by traffic volume and judge cost?
- How to prevent eval-set leakage into prompts/few-shots used by the product model?
- Ownership: eng vs PM vs domain expert for flywheel maintenance?
- When does the flywheel justify fine-tuning vs continued prompt/RAG iteration?

### Sources

- https://hamel.dev/blog/posts/evals/
- https://hamel.dev/blog/posts/field-guide/
- https://hamel.dev/blog/posts/evals-faq/
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html
- https://langfuse.com/blog/2025-11-12-evals
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications
- https://developers.openai.com/api/docs/guides/evaluation-best-practices
- https://www.youtube.com/watch?v=BsWxPI9UM4c

---

## Cross-cutting notes for Week 16 synthesis

1. **Read before you measure.** 20–50 manual reviews beat premature automation.
2. **Taxonomies emerge from data** via open → axial coding; generic metrics are a trap.
3. **Synthetic inputs bootstrap and stress**; production rates still require production samples.
4. **Flywheel closes the loop:** labeled production failures become the regression suite and judge-calibration set.
5. **Fix first, evaluate second** for clear prompt/tool bugs; reserve judges for subjective residual failures.

---

## Master source list (Week 16)

| Source | URL |
|--------|-----|
| Hamel — Evals FAQ hub | https://hamel.dev/blog/posts/evals-faq/ |
| Hamel/Shreya — Error analysis FAQ | https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html |
| Hamel — Your AI Product Needs Evals | https://hamel.dev/blog/posts/evals/ |
| Hamel — LLM-as-a-Judge guide | https://hamel.dev/blog/posts/llm-judge/ |
| Hamel — Field Guide | https://hamel.dev/blog/posts/field-guide/ |
| Hamel — Evals in production case | https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html |
| Shankar et al. — Who Validates the Validators? | https://arxiv.org/abs/2404.12272 |
| Langfuse — Error analysis cookbook | https://langfuse.com/guides/cookbook/error-analysis-llm-applications |
| Langfuse — Evals roadmap blog | https://langfuse.com/blog/2025-11-12-evals |
| OpenAI — Evaluation best practices | https://developers.openai.com/api/docs/guides/evaluation-best-practices |
| YouTube — Hamel & Shreya AI evals | https://www.youtube.com/watch?v=BsWxPI9UM4c |
| Public talk write-up | https://www.aakashg.com/ai-evals-masterclass-with-hamel-shreya/ |
