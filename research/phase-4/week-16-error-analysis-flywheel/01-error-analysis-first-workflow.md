# 01 — Error-analysis-first workflow (read 20–50 outputs before metrics)

> Week 16 — Read traces before inventing scores  
> Research notes (raw).

---

## Fundamentals

**Error-analysis-first** means you **manually read real application traces** (or outputs) and write **free-text notes** about what went wrong **before** you invent automated metrics, buy a generic judge pack, or write a rubric in a vacuum.

Hamel Husain and Shreya Shankar treat this as the highest-ROI activity in **product** evals (as opposed to **model benchmarks** like MMLU). Product evals measure whether *your* stack—model, prompt, retrieval, tools, application code—does what users and the business need ([FAQ: What are AI evals?](https://hamel.dev/blog/posts/evals-faq/)). Error analysis decides **which** of those evals to write, grounded in failure modes unique to the app.

### Why “before metrics”

Generic dashboards create two failure modes ([Field Guide](https://hamel.dev/blog/posts/field-guide/)):

1. **False measurement.** Teams celebrate a 10% “helpfulness” lift while users still fail basic tasks.  
2. **Fragmented attention.** Optimizing many abstract dimensions at once means nothing is prioritized.

Lenny’s Podcast (Hamel & Shreya, [YouTube `BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c)): people get lost by jumping straight into writing tests. Ground yourself in **actual errors**. Chapter ~16:51 in Lenny’s newsletter notes: always start with error analysis; don’t jump into writing evals ([newsletter](https://www.lennysnewsletter.com/p/why-ai-evals-are-the-hottest-new-skill)).

Shreya on the same episode / Aakash masterclass: dumping a leasing-assistant trace into ChatGPT and asking “was the assistant correct?” often yields **yes**—and misses markdown-in-SMS, “I’ll check bathrooms” with no tool call, virtual tours the product does not offer, and double-booked tours ([Aakash write-up](https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/)). Taste and product context are not in the weights.

Hamel FAQ on **eval-driven development**: generally **no**. Unlike TDD for conventional software, LLM failure surface is unbounded. Write evaluators for errors you **discover**, not errors you **imagine**. Exception: a known hard constraint (“never mention competitors”) can get an early check. Always cost-benefit before implementing an eval.

### Minimum viable evaluation setup

From [What’s a minimum viable evaluation setup?](https://hamel.dev/blog/posts/evals-faq/):

1. **Start with error analysis, not infrastructure.**  
2. Spend **~30 minutes** reviewing **20–50 LLM outputs** whenever you make **significant changes**.  
3. Use **one domain expert** who understands users as quality decision maker (**benevolent dictator**).  
4. A **notebook**, a CSV, or a **custom annotation UI** (Claude/Codex-built) beats waiting for a perfect platform. Hamel: you do **not** necessarily need a dedicated AI observability product to *start*—JSON/CSV/Datadog can work; the requirement is **notes on traces**.  
5. You can write arbitrary code, visualize, iterate.

YouTube lesson [Intro To Error Analysis: Creating Custom Data Annotation Apps](https://www.youtube.com/watch?v=qH1dZ8JLLdU): Shreya builds a viewer in minutes; takeaways are (1) build a viewer that removes friction, (2) **free-form notes**, do not categorize too early, (3) this is the foundation of evals.

### Dataset construction (the working pool)

[Error-analysis FAQ](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html) process:

1. **Create a dataset** of representative traces. No data? **Synthetic inputs** through the real system (file [03](03-synthetic-data-edge-cases.md)).  
2. **Open coding** by humans (ideally the dictator). Journaling. **≥30 traces yourself** before reviewing agent suggestions. Prefer noting the **first** failure (upstream cascades). Domain expert.  
3. **Axial coding** into a failure taxonomy; count; LLM may help cluster.  
4. **Iterative refinement** to **theoretical saturation**: new reviews stop revealing or reshaping modes. Agent clusters and searches remaining traces after 30. Working pool ~**100 diverse** traces as a guardrail—you need not read all 100 sequentially once the agent focuses you.

Langfuse **Step 1** adds *what unit to annotate*: conversational apps often last-turn-per-session; OTel apps may have **null trace I/O**—annotate the **GENERATION** observation. Stratify: tags, low scores, latency, cost tails, multi-turn. Dad Tech Support: of 478 sessions only 11 were multi-turn (rest possibly synthetic)—**confirm scope** before committing to a sample.

### How to look (friction kills the workflow)

[Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) (Lucy / Rechat): remove friction—render traces **domain-specifically** (CRM + listing + tool). Binary good/bad often beats Likert. Labeled examples later measure quality, validate judges, and curate synthetic/fine-tune data.

Field Guide data-viewer checklist: all context on one screen; one-click correct/incorrect; **open-ended** feedback; filter/sort; hotkeys. Off-the-shelf label UIs that force hunting across systems **discourage** analysis.

Hamel/Shreya on Nurture Boss traces (Aakash): scan in **~30 seconds**; you need not reread the system prompt every time; **perfection is not the goal**—catch the important failures and **move on**. Debating one trace forever is a failure mode.

### Cadence and sampling after the first pass

[How often should I re-run error analysis?](https://hamel.dev/blog/posts/evals-faq/)

- After **significant changes**: features, prompts, model switches, major bug fixes.  
- Heuristic: **100+ fresh traces** per review cycle. Typical cycles **2–4 weeks**.  
- Between cycles: **10–20 traces weekly**, outliers (long conversations, retries, monitoring flags).  
- New systems: **weekly** until patterns stabilize. Mature: **monthly** unless usage changes.  
- Always after incidents, complaint spikes, metric drift. Scaling usage introduces new edges.

[How do I surface problematic traces?](https://hamel.dev/blog/posts/evals-faq/) Complementary methods: random sample; existing evals as a **screen** (not as quality truth); clustering; sort by feedback; high-probability failure patterns. Over time you develop a “nose.” Keep **some random** traces in every batch so you still find unknown modes.

Sampling methods ordered exploratory → targeted (Hamel FAQ table): random → clustering → data analysis (latency/tool count) → classification (known-failure model) → user feedback. Limitation of feedback: **users do not report** many product failures.

**Active learning** (Shreya walkthrough in FAQ): agent clusters; `monitor` on `annotations.json`; new labels update taxonomy and search for similar/different failures.

### Who does the reading

[How many people should annotate?](https://hamel.dev/blog/posts/evals-faq/) For most small/medium teams: **one benevolent dictator**. Multiple annotators → Cohen’s Kappa, independent labels then alignment sessions. If you need five SMEs per interaction, **product scope may be too broad**.

**Do not outsource** core error analysis: you lose the feedback loop and tacit knowledge. Exceptions: mechanical checks after a rubric exists; translation; **hiring SMEs into the process** (AnkiHub: 4th-year med students for medical RAG—not generic BPO).

PMs + engineers at the outset: engineers catch retrieval/tool bugs; PMs catch unmet expectations. Then lean dictator. Ask “was an appointment made?” not only “did the tool succeed?”—show **outcomes** on the annotation screen.

### Budget and selling the work

Hamel: evaluation is **part of development**, like debugging—not a separate line item. Consulting projects: **60–80%** of time on error analysis / looking at data. Many issues found are **immediate bugs**; those do not need eval infrastructure.

Do not sell “evals.” Show: top failure modes, rates, surprising user behavior, bugs caught framed as prevented production issues. Running log: error, learning, fix, impact. Weekly/monthly.

Beware 100% eval pass rates: you may not be challenging the system. A **~70%** pass rate can indicate a more meaningful, stressful set.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **Error analysis → targeted evals** | Metrics match pain; avoids vanity scores | Domain-expert time; slower to look automated |
| Generic LLM-judge dashboards first | Fast to wire; vendor UI looks mature | Wrong things; criteria drift ignored |
| Unit tests / golden answers only | Cheap CI; deterministic | Misses subjective / multi-turn / tool failures |
| A/B or business metrics only | Ties to revenue/NPS | Slow; hard to debug *why* |
| Delegate first pass entirely to an LLM | Scales annotation | Biases categories; misses taste (Hamel/Langfuse: humans do first 30–50) |
| Wait for more production volume | “Real” rates | Ships blind; synthetic-through-prod exists for a reason |
| Eval-driven development of all imagined failures | Feels like TDD | Infinite surface; wasted rubric (Nova Escola) |
| Likert 1–5 on first pass | Feels nuanced | Slow; annotators hide in the middle; Hamel/Shreya: start **binary** |

---

## Necessity

If you skip reading 20–50 traces before metrics:

- You optimize for scores that do not correlate with user success.  
- You build LLM judges for bugs a prompt fix would kill.  
- IAA collapses (Nova Escola).  
- Criteria drift happens **anyway**, but invisibly—EvalGen study: people refine criteria *while* grading; pretending the rubric existed a priori is false ([arXiv:2404.12272](https://arxiv.org/abs/2404.12272)).  
- Regressions ship because CI only checks JSON/format.  
- Shreya: anything not externalized into traces or your notes, an agent **will never find**.

If you never revisit after changes:

- Failure **distribution shifts** (Langfuse: a prompt fix can kill one category and reveal another).  
- Flywheel starves (file [04](04-data-flywheel.md)).

---

## Industry Practice

**Common:** Instrument once; look at traces only when a ticket fires; add `helpfulness` from the vendor catalog.

**Strong:**

- 20–50 after every significant change; 100+ per cycle; 10–20 weekly outliers.  
- Custom viewer or ruthless spreadsheet. Nurture Boss vibe-coded theirs (Aakash / Field Guide).  
- Fix prompt/tool bugs **before** evaluators (Langfuse decision tree; FAQ “Should I build automated evaluators for every failure mode?”).  
- Binary pass/fail + critique, not 1–5, for the analysis pass.  
- OpenAI: log as you develop so you can **mine logs for eval cases**; continuous evaluation on change ([best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)). Use that logging **to feed error analysis**, not as a substitute for it.  
- SPADE (Shankar et al., [arXiv:2401.03038](https://arxiv.org/abs/2401.03038)): prompt-version **deltas** can suggest **candidate assertions**—useful *after* you know the pipeline, not as a replacement for reading traces.

**Anti-pattern (Langfuse cookbook table):** annotating **traces** instead of **GENERATION** observations in OTel apps (annotators see nothing).

---

## Concrete Scenario (URL)

**Hamel FAQ — 20–50 in 30 minutes, benevolent dictator.**  
https://hamel.dev/blog/posts/evals-faq/

**Langfuse Dad Tech Support — 12-turn session:** system prompt “Never say that you cannot look things up online” vs bot “I can’t look up printer manuals” twice until the user pushed. **Only visible by reading.**  
https://langfuse.com/guides/cookbook/error-analysis-llm-applications

**Nurture Boss live walkthrough (Aakash / Lenny):** markdown in SMS; bathroom-not-connected ignored; virtual tour that is actually in-person; reschedule = second booking.  
https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
https://www.youtube.com/watch?v=BsWxPI9UM4c

**Nova Escola — rubric first:** most criteria never appeared as failures; labeling wasted.  
https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html

**Custom annotation app (Hamel & Shreya YouTube).**  
https://www.youtube.com/watch?v=qH1dZ8JLLdU

---

## Open Questions

- How much of early error analysis can safely be agent-assisted without biasing the taxonomy?  
- What’s the right cadence for mature vs greenfield products (weekly vs monthly)?  
- When is random sampling enough vs clustering / feedback-sorted sampling / active learning?  
- Can product managers without ML background own the benevolent-dictator role at scale?  
- How to time-box 30 minutes when traces are 40-turn agent trajectories (Week 15 units vs last-turn-only)?  
- Privacy: how much production text can land in a custom viewer vs vendor SaaS?

---

## Sources

- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/field-guide/  
- https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html  
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications  
- https://developers.openai.com/api/docs/guides/evaluation-best-practices  
- https://arxiv.org/abs/2404.12272  
- https://arxiv.org/abs/2401.03038  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.youtube.com/watch?v=qH1dZ8JLLdU  
- https://www.youtube.com/watch?v=tqUDjc1HzO4  
- https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
- https://www.lennysnewsletter.com/p/why-ai-evals-are-the-hottest-new-skill  
