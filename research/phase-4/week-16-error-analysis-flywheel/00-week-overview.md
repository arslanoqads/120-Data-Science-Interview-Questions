# 00 — Week overview: error-analysis pass, custom taxonomy, frequency

> Week 16 — Error analysis & the data flywheel  
> Research notes (raw). Phase 4 week after agent traces (Week 15). Next: LLM-as-judge & observability (Week 17).

---

## Fundamentals

Week 16 is the **discovery and prioritization** week of Phase 4. Week 15 **instrumented** both agentic systems and defined **split scores** (tool-call correctness, trajectory vs outcome). This week does **not** add a third agent and does **not** require a calibrated LLM judge. It answers three questions Hamel Husain and Shreya Shankar treat as the start of product evals:

1. **What actually fails** for *this* product on *this* data? (error-analysis pass)  
2. **What do we call those failures** so another human (or a later judge) can apply the same labels? (custom taxonomy)  
3. **Which failures dominate**, by **frequency** and impact, so we know what to fix vs measure vs ignore? (quantify)

Error analysis is borrowed from qualitative research and classic ML debugging: **open coding** (free-text notes on traces) then **axial coding** (group notes into a failure taxonomy) then **count**. Hamel/Shreya: it is “the most important activity in evals” because it decides **which evals to write** ([error-analysis FAQ](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html)). Platforms nudge generic “helpfulness / hallucination / toxicity” scores; those rarely match user pain.

### The error-analysis pass (what you physically do)

Minimum viable loop (Hamel [FAQ: minimum viable evaluation](https://hamel.dev/blog/posts/evals-faq/)):

| Step | Guidance |
|------|----------|
| Instrument | Traces already exist from Week 15 (prompt, tools, retrieval, final answer, session). |
| Pool | ~**100 diverse** traces (or synthetic queries run through the real app). |
| Human first | Annotate **≥30 yourself** before an agent proposes similar failures. |
| Cadence after changes | ~**30 minutes** reading **20–50** outputs after any significant prompt/model/feature change. |
| Owner | One domain expert (“**benevolent dictator**”) as quality decision maker. |
| Then metrics | Only then turn **recurring** failures into code assertions or LLM judges. |

Langfuse operationalizes the same pass in **five steps** on a real app ([error-analysis cookbook](https://langfuse.com/guides/cookbook/error-analysis-llm-applications)): gather ~100 stratified traces → open-code 30–50 → cluster 5–10 categories → boolean-label and **chart failure rates** → decide **fix / evaluator / monitor**.

Shreya’s public talks add an **analyze → measure → improve** lifecycle ([How to Automate AI Evals](https://www.youtube.com/watch?v=tqUDjc1HzO4)): error analysis finds modes; measurement estimates **prevalence**; only then do you change the product. Automating “the whole eval” in one LLM call skips the taste-specific first step.

### Custom failure taxonomy (not a vendor catalog)

A **custom** taxonomy is 5–10 **named, binary, one-sentence** categories grounded in observed traces. Naming after *what broke* (`identity_not_disclosed`, `date_handling`, `markdown_in_sms`) beats abstract quality (`hallucination`, `helpfulness`).

Why custom:

- **Actionability.** Nurture Boss’s bottom-up coding found three issues covering **>60%** of problems (conversation flow, handoff, **date handling**). Date handling went from **33% → 95%** success after targeted tests—not after a generic hallucination dashboard ([Field Guide](https://hamel.dev/blog/posts/field-guide/)).  
- **Criteria cannot be specified a priori.** Shankar et al. call this **criteria drift**: people need outputs to define criteria, and criteria to grade outputs (*Who Validates the Validators?*, UIST 2024, [arXiv:2404.12272](https://arxiv.org/abs/2404.12272)). Open coding makes that loop explicit.  
- **Avoid confirmation bias.** Brainstorming categories before reading traces is Langfuse’s #1 listed mistake.

### Frequency (the product decision)

After axial coding, **relabel** the sample with boolean flags per category. **Failure rate** = share of traces where the flag is true. Langfuse: average of a boolean score **is** the rate.

Prioritize **rate × business impact**, not rate alone. Aakash Gupta’s public masterclass (Hamel/Shreya on Nurture Boss): conversational-flow issues were frequent; **human-handoff** might still rank first if catastrophic ([write-up](https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/)).

Dad Tech Support **illustrative** rates (19 labeled traces; cookbook says finish 100 before locking priorities):

| Category | Rate (illustrative) | Typical next action |
|----------|---------------------|---------------------|
| `impersonates_child` | 58% | Prompt fix (persona over-strong) |
| `identity_not_disclosed` | 42% | Prompt fix (disclosure) |
| `tone_persona_off` | 42% | Likely downstream of persona; monitor after fix |
| `too_verbose` | 32% | Prompt + examples |
| `denied_scope` | 16% | Prompt scope |
| `missing_device_lookup` | 11% | **LLM-as-judge** (judgment-heavy) |
| `missing_clarifying_question` | 11% | LLM-as-judge |
| `incomplete_resolution` | 5% | **Monitor only** |

Identity cluster dominated; one prompt change hit multiple high-rate categories. That is the point of **counting**.

### What you ship this week

```
Week 15 traces ──► sample (~100 diverse / stratified)
                      │
              open coding (≥30 human; 20–50 after changes)
                      │
              axial coding (5–10 custom categories)
                      │
              boolean relabel ──► failure-rate chart (frequency)
                      │
         ┌────────────┼────────────────┐
         ▼            ▼                ▼
    prompt/tool    code eval /      monitor
    fix now        (Week 17 judge)   low-rate
         │
         ▼
    labeled failures ──► eval set ──► CI + sampled prod (flywheel)
```

### Mapping to later weeks

| This week | Not this week |
|-----------|----------------|
| Read traces; notes; taxonomy; rates | Calibrated LLM-as-judge TPR/TNR (Week 17) |
| Decide *whether* a judge is worth it | Vendor tracing bake-off as the main deliverable |
| Synthetic **queries** through the real pipeline | Fine-tuning on synthetic **answers** |
| Promote failures into a golden/regression set | Claiming a 100% eval pass rate as success (Hamel: 70% can mean a harder, useful set) |

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **Error analysis → custom taxonomy → frequency** | Metrics match user pain; PM-accessible (spreadsheet + pivot) | Expert time; slower to “look automated” |
| Generic LLM-judge dashboard first | Fast vendor UI | Vanity scores; false confidence ([Field Guide](https://hamel.dev/blog/posts/field-guide/)) |
| Rubric written before reading traces | Feels rigorous | Nova Escola: most criteria never appeared; wasted labels ([production case](https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html)) |
| Eval-driven development of imagined failures | Familiar from TDD | Hamel: LLM failure surface is unbounded; write evals for **discovered** errors |
| Agent does the entire first pass | Scales | Biases taxonomy; misses product taste (Shreya Lenny: ChatGPT says the leasing bot is “fine”) |
| Rate-only ranking | Simple | Ignores catastrophic rare failures |
| Impact-only ranking | Protects worst cases | May ignore the 60% blob that users feel every day |

---

## Necessity

If you skip the error-analysis pass:

- You optimize metrics that do not correlate with user success (Field Guide “helpfulness +10%, users still fail basic tasks”).  
- You build judges for bugs a one-line prompt would kill (Nova Escola: two learning goals instead of one).  
- Inter-annotator agreement collapses because “good” was never defined on real outputs (Nova Escola: two annotators agreed **less often than chance** until pedagogical experts rewrote the rubric).  
- Week 17 judges have nothing trustworthy to align to.

If you skip a **custom** taxonomy:

- Teams argue vibes; nobody owns `helpfulness`.  
- Langfuse: LLM clustering merges different root causes (passive non-disclosure vs active impersonation).

If you skip **frequency**:

- You fix a pet peeve and miss the 58% identity failure.  
- You cannot tell a stakeholder a story with data (Hamel: “caught N issues before users saw them,” not “we adopted evals”).

---

## Industry Practice

**Common:** Trace into Langfuse/Phoenix/Braintrust, glance at a few bad traces after tickets, add a generic judge, never count.

**Strong / senior:**

- Domain expert owns pass/fail + critique; engineers pair at the start so PMs can access traces ([FAQ: PM + eng](https://hamel.dev/blog/posts/evals-faq/)).  
- Custom **data viewer** (Nurture Boss, Lucy/Rechat): all context on one screen, hotkeys, open-ended notes ([Field Guide](https://hamel.dev/blog/posts/field-guide/); [YouTube annotation lesson](https://www.youtube.com/watch?v=qH1dZ8JLLdU)). Spreadsheet is valid to start.  
- Re-run full analysis after prompt/model/feature changes; **2–4 week** cycles targeting **100+ fresh traces**; between cycles, **10–20** weekly outliers (long sessions, retries, low scores) ([FAQ: how often](https://hamel.dev/blog/posts/evals-faq/)). Greenfield: weekly until patterns stabilize. Mature: monthly unless usage shifts. Always after incidents.  
- Budget: Hamel reports **60–80%** of development time on looking at data / error analysis in consulting projects.  
- Fix obvious gaps first; automate only recurrent, high-impact, not-trivially-fixed failures.

**OpenAI public guidance** (complementary, not a replacement): eval-driven development, **task-specific** tests, **log everything** so you can mine cases, evaluation as continuous, mix synthetic / domain / purchased / human / production / historical data ([evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)). Hamel’s sharper opinion: do **not** start from generic academic metrics as quality scores; use them at most as **exploration signals**.

---

## Concrete Scenario (URL)

**Langfuse Dad Tech Support** — 505 traces / 478 sessions; ~100 stratified sample (multi-turn, latency, cost tiers); open-code; taxonomy; rates; fix vs judge vs monitor.  
https://langfuse.com/guides/cookbook/error-analysis-llm-applications

**Nurture Boss (Hamel Field Guide + Lenny / Aakash talks)** — open notes beside conversations; three issues >60%; date handling 33% → 95%.  
https://hamel.dev/blog/posts/field-guide/  
https://www.youtube.com/watch?v=BsWxPI9UM4c  
https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/

**Nova Escola (Lucas Machado, Hamel notes)** — rubric-before-analysis; IAA disaster; then taxonomy-driven judges; **daily suite on ~2% of production**.  
https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

**Shankar et al. criteria drift** — EvalGen mixed-initiative study; criteria co-evolve with grading.  
https://arxiv.org/abs/2404.12272  
https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf

---

## Open Questions

- How much of early error analysis can be **agent-assisted** without biasing the taxonomy? (Shreya: use AI to *scale your labels*, not to invent taste.)  
- Right cadence for mature vs greenfield (weekly vs monthly) as traffic and models change?  
- When is random sampling enough vs clustering / feedback / active learning (Hamel FAQ sampling table)?  
- Can PMs without ML background own the benevolent-dictator role at scale, or only with custom viewers?  
- How to version taxonomies when frequency charts must stay comparable across prompt versions?  
- Hierarchical vs flat taxonomies once you have 10+ modes?

---

## Sources

- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/field-guide/  
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html  
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications  
- https://arxiv.org/abs/2404.12272  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.youtube.com/watch?v=qH1dZ8JLLdU  
- https://www.youtube.com/watch?v=tqUDjc1HzO4  
- https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
- https://www.lennysnewsletter.com/p/why-ai-evals-are-the-hottest-new-skill  
