# Chapter 16 — Error analysis & the data flywheel

> **Phase 4 — Evals and Observability**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-4/week-16-error-analysis-flywheel/`  
> **Syllabus Build:** Do **not** skip to LLM-as-judge dashboards. You already have **structured traces** from Week 15. This week you **read them**. (1) **Error-analysis pass.** Sample ~100 diverse traces (or synthetic-through-prod if cold start). Personally open-code **≥30**, preferably **20–50 in ~30 minutes** after every significant prompt/model/feature change. One **benevolent dictator** (domain expert) owns pass/fail + free-text notes. (2) **Custom taxonomy.** Axial-code notes into **5–10** binary, named, one-sentence categories grounded in *this* app (`missing_device_lookup`, not `hallucination`). Split surface-similar failures with different root causes. (3) **Frequency.** Relabel the sample with boolean flags; compute **failure rate per category**; prioritize **rate × impact**. Fix prompt/tool bugs **before** building judges. (4) **Synthetic edges.** If production undersamples a known combo, generate **dimension tuples → natural-language queries**, run them through the **live stack**, open-code the traces. Do **not** use synthetic completions as gold. (5) **Flywheel.** Promote labeled failures into a **regression eval set**; run on change (CI) and on a **production sample** (Nova Escola ~2% daily). New incidents become new rows. Week 17 is when you **calibrate** residual LLM judges.

---

## Prerequisites Recap

Before this week you should already have from Week 15:

- **Structured traces** on both agentic systems (Week 11 loop agent + Week 14 write agent) on one primary tracer (LangSmith **or** Langfuse **or** OpenAI traces). Tool calls are structured fields (`name`, `arguments`, …), not parsed chat text; session / thread / `taskId` IDs join multi-turn and cross-peer runs.  
- A **split scorecard**, never one “quality” number: `task_success` (outcome / read-back), `tool_name`, `tool_args`, `policy_order`, `within_step_budget`, cost/turns — plus **tool-call correctness** checks (Hamel’s four: name, arguments, result, resulting state) and authorization/preconditions.  
- **Trajectory vs outcome** graded side by side on the same write task: a trial can pass outcome and fail trajectory (refund without verify — unsafe), or pass trajectory and fail outcome (right tools; DB never updated).  
- The **four failure-pattern fixtures** (C1–C4: loops, premature stop, missing tool, dropped early constraint) as regression cases, with at least one real failing prod/dev trace promoted into a dataset.  
- Benchmark **literacy** (τ-bench / WebArena / AgentBench) without treating a public leaderboard as the ship gate — the private suite remains the product truth.

You do **not** need a calibrated LLM-as-judge, an observability-platform bake-off, or production quality dashboards yet. That is what Week 17 teaches. This week **mines** the traces you already have.

---

## What this week builds

Week 15 **instrumented** both agents, defined **split scores**, contrasted **trajectory vs outcome**, and named **failure patterns**. Week 16 opens **Phase 4 — Evals and Observability** as the **discovery and prioritization** week. This week does **not** add a third agent and does **not** require a calibrated LLM judge. It answers three questions Hamel Husain and Shreya Shankar treat as the start of product evals:

1. **What actually fails** for *this* product on *this* data? (error-analysis pass)  
2. **What do we call those failures** so another human (or a later judge) can apply the same labels? (custom taxonomy)  
3. **Which failures dominate**, by **frequency** and impact, so we know what to fix vs measure vs ignore? (quantify)

Error analysis is borrowed from qualitative research and classic ML debugging: **open coding** (free-text notes on traces) then **axial coding** (group notes into a failure taxonomy) then **count**. It decides **which evals to write**. Platforms nudge generic “helpfulness / hallucination / toxicity” scores; those rarely match user pain. Week 15’s C1–C4 fixtures and split scores are **starting labels and slices**, not a finished product taxonomy — open coding will rename and split them when traces demand it.

**Do not start Week 17 (LLM-as-judge / calibration / observability platforms / production dashboards) from this chapter** — this week **mines traces** into a **custom failure taxonomy**, **quantifies frequency**, **bootstraps edges with synthetic inputs**, and **closes the production → labels → eval set → regression** flywheel. Judge *calibration*, code-vs-model evals, tracing product choices, and production dashboards are next week.

**What you ship this week**

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

Interview artifact = **taxonomy table with rates** + one prompt fix that killed a high-rate category + one failure reserved for a judge + how production sampling refills the set.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume Deployment Copilot’s Week 15 traces (loop agent + write agent) being mined for the first taxonomy and regression set.

---

### Error-analysis-first workflow (read 20–50 outputs before metrics)

* **Fundamentals:**  
  **Error-analysis-first** means you **manually read real application traces** (or outputs) and write **free-text notes** about what went wrong **before** you invent automated metrics, buy a generic judge pack, or write a rubric in a vacuum. Week 15 already gave you those traces and a first vocabulary (split scores, trajectory vs outcome disagreement, C1–C4 fixtures). This week you **read** them the way product teams do — free-text first — instead of skipping to a judge dashboard.

  Hamel Husain and Shreya Shankar treat this as the highest-ROI activity in **product** evals (as opposed to **model benchmarks** like MMLU). Product evals measure whether *your* stack—model, prompt, retrieval, tools, application code—does what users and the business need. Error analysis decides **which** of those evals to write, grounded in failure modes unique to the app.

  Generic dashboards create two failure modes (Field Guide): **false measurement** (celebrate a 10% “helpfulness” lift while users still fail basic tasks) and **fragmented attention** (optimizing many abstract dimensions at once means nothing is prioritized). Lenny’s Podcast (Hamel & Shreya): people get lost by jumping straight into writing tests—ground yourself in **actual errors**. Dumping a leasing-assistant trace into ChatGPT and asking “was the assistant correct?” often yields **yes**—and misses markdown-in-SMS, “I’ll check bathrooms” with no tool call, virtual tours the product does not offer, and double-booked tours. Taste and product context are not in the weights.

  **Minimum viable evaluation setup** (Hamel FAQ):

  | Step | Guidance |
  |------|----------|
  | Start with error analysis, not infrastructure | Traces already exist from Week 15 |
  | Cadence after changes | ~**30 minutes** reading **20–50** outputs after any significant prompt/model/feature change |
  | Owner | One domain expert (“**benevolent dictator**”) as quality decision maker |
  | Tooling | Notebook, CSV, or custom annotation UI beats waiting for a perfect platform; JSON/CSV/Datadog can work—the requirement is **notes on traces** |
  | Human first | Annotate **≥30 yourself** before an agent proposes similar failures |
  | Working pool | ~**100 diverse** traces (or synthetic queries run through the real app) |
  | Then metrics | Only then turn **recurring** failures into code assertions or LLM judges |

  Langfuse operationalizes the same pass in **five steps**: gather ~100 stratified traces → open-code 30–50 → cluster 5–10 categories → boolean-label and **chart failure rates** → decide **fix / evaluator / monitor**. Shreya’s public talks add an **analyze → measure → improve** lifecycle: error analysis finds modes; measurement estimates **prevalence**; only then do you change the product.

  **How to look:** remove friction—render traces domain-specifically; binary good/bad often beats Likert; all context on one screen; open-ended feedback; hotkeys. Scan in ~30 seconds; perfection is not the goal—catch important failures and move on. Prefer noting the **first** failure (upstream cascades). For conversational apps, annotate last-turn-per-session when that is the unit; for OTel apps with null trace I/O, annotate the **GENERATION** observation—not empty traces.

  **Cadence after the first pass:** after significant changes; heuristic **100+ fresh traces** per review cycle (typical **2–4 weeks**); between cycles **10–20 weekly** outliers; greenfield **weekly** until patterns stabilize; mature **monthly** unless usage shifts; always after incidents. Keep **some random** traces in every batch so you still find unknown modes. Sampling methods (exploratory → targeted): random → clustering → data analysis → classification → user feedback—limitation: users do not report many product failures.

  Hamel on **eval-driven development**: generally **no**. Unlike TDD for conventional software, the LLM failure surface is unbounded. Write evaluators for errors you **discover**, not errors you **imagine**. Exception: a known hard constraint (“never mention competitors”) can get an early check. Budget: consulting projects often spend **60–80%** of development time on looking at data / error analysis. Beware 100% eval pass rates—a **~70%** pass rate can indicate a more meaningful, stressful set.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Error analysis → targeted evals | Metrics match pain; avoids vanity scores | Domain-expert time; slower to look automated | Default for this syllabus / product evals |
  | Generic LLM-judge dashboard first | Fast vendor UI | Vanity scores; false confidence | Exploration signals at most—not quality scores |
  | Rubric written before reading traces | Feels rigorous | Most criteria may never appear; wasted labels (Nova Escola) | Avoid for first pass |
  | Eval-driven development of imagined failures | Familiar from TDD | Infinite surface; wrong evals | Only known hard constraints early |
  | Agent does the entire first pass | Scales | Biases taxonomy; misses product taste | After ≥30 human labels; accept/reject every suggestion |
  | Unit tests / golden answers only | Cheap CI; deterministic | Misses subjective / multi-turn / tool failures | Complementary Level-1 assertions—not a substitute |
  | A/B or business metrics only | Ties to revenue/NPS | Slow; hard to debug *why* | After significant product changes (Level 3) |
  | Wait for more production volume | “Real” rates | Ships blind | Use synthetic-through-prod for cold start |
  | Likert 1–5 on first pass | Feels nuanced | Slow; annotators hide in the middle | Prefer **binary** pass/fail + critique |

  The syllabus selects **error-analysis-first** because Week 16’s build explicitly requires reading Week 15 traces before inventing judges. OpenAI public guidance (log everything; complementary data sources; continuous eval) is complementary—not a substitute for reading traces.

* **Failure Modes:**  
  - Optimize metrics that do not correlate with user success (“helpfulness +10%, users still fail basic tasks”).  
  - Build LLM judges for bugs a one-line prompt would kill (Nova Escola: two learning goals instead of one).  
  - Inter-annotator agreement collapses because “good” was never defined on real outputs (Nova Escola: two annotators agreed **less often than chance** until experts rewrote the rubric).  
  - Criteria drift happens anyway, but invisibly—pretending the rubric existed a priori is false.  
  - Regressions ship because CI only checks JSON/format.  
  - Anything not externalized into traces or notes, an agent will never find.  
  - Failure distribution shifts after a prompt fix and you never re-read (one category dies; another appears).  
  - Annotating empty OTel **traces** instead of **GENERATION** observations—annotators see nothing.  
  - Debating one trace forever instead of scanning ~30 seconds and moving on.  
  - Outsourcing core error analysis to generic BPO—you lose the feedback loop and tacit knowledge.

* **Average vs. Strong Engineer:**  
  **Average:** instrument once; look at traces only when a ticket fires; add `helpfulness` from the vendor catalog; jump straight into writing tests.  
  **Strong:** 20–50 outputs after every significant change; ≥30 human open-coded before agent assist; ~100 diverse working pool; benevolent dictator owns pass/fail + critique; custom viewer or ruthless spreadsheet (all context one screen, hotkeys); PMs + engineers at the outset then lean dictator; binary + notes; fix prompt/tool bugs **before** evaluators; sell leadership top failure modes and rates—not “we adopted evals”; running log of error → learning → fix → impact. Hamel: evaluation is **part of development**, like debugging—not a separate line item. Do not outsource core analysis; exceptions are mechanical checks after a rubric exists, translation, or hiring SMEs into the process (AnkiHub: 4th-year med students for medical RAG).

* **Worked Example:**  
  Deployment Copilot has Week 15 traces on the loop agent and write agent. After a prompt change that “improved helpfulness,” you spend 30 minutes on 40 stratified traces (multi-turn sessions, high cost, retries, low split scores, known C1–C4 fixtures). Free-text notes: “said it would verify identity but called `commit_refund` first” (trajectory fail / outcome may still pass); “markdown bullets in SMS channel”; “promised to look up runbook, never called retrieve.” ChatGPT on the same transcripts says the assistant was fine. Only the notes reveal policy-order and channel-format failures. You do **not** open a judge dashboard yet—you open-code ≥30 yourself, then schedule axial coding.

  Langfuse Dad Tech Support parallel: 505 traces / 478 sessions; ~100 stratified sample; a 12-turn session where the system prompt said “Never say that you cannot look things up online” while the bot said “I can’t look up printer manuals” twice—**only visible by reading**.

* **Apply It:**  
  1. From Week 15 traces, build a ~100 diverse/stratified sample (tags, latency/cost tails, multi-turn, low split scores, trajectory/outcome disagreements, C1–C4 fixtures). Confirm annotation unit (session last-turn vs GENERATION).  
  2. Pick one benevolent dictator; configure `open_coding` (text) + `pass_fail` (binary)—not Likert.  
  3. Personally open-code ≥30 traces with free-text notes; prefer first-failure notes.  
  4. After the next significant prompt/model/feature change, spend ~30 minutes on 20–50 fresh outputs.  
  5. Between full cycles, review 10–20 weekly outliers; keep some random traces in every batch.  
  6. Do **not** invent a rubric or wire a generic judge pack until axial coding and rates exist.

---

### Open coding and custom failure taxonomy

* **Fundamentals:**  
  Failure taxonomies for LLM products are **induced from traces**, not copied from eval-vendor catalogs. The method:

  1. **Open coding** — Read each trace end-to-end; write short free-text observations of anything wrong, unexpected, or bad for the user. **No predefined category list.**  
  2. **Axial coding** — Group open codes into a **failure taxonomy**: typically **5–10** named categories, each with a **one-sentence definition** another person could apply. Then **count**. Axial coding is “the most important step” (Hamel error-analysis FAQ).

  Open-coding rules:

  | Do | Don’t |
  |----|--------|
  | Describe **behavior** (“bot said it can’t look things up”) | Diagnose root cause in the note (“web search broken”) |
  | Early on, note the **first** failure (cascades) | Optional later: tag all independent failures if feasible |
  | Domain expert / benevolent dictator | Generic BPO as first pass |
  | ≥**30** traces yourself before agent suggestions | Let an LLM propose the taxonomy from zero |
  | Binary **pass/fail** plus notes | Likert 1–5 on the discovery pass |
  | Move on (~30s–minutes per trace) | Debate one trace endlessly |

  A **custom** taxonomy is 5–10 **named, binary, one-sentence** categories grounded in observed traces. Naming after *what broke* (`identity_not_disclosed`, `date_handling`, `markdown_in_sms`) beats abstract quality (`hallucination`, `helpfulness`).

  Why custom: **actionability** (Nurture Boss: three issues covering **>60%** of problems—conversation flow, handoff, date handling; date handling **33% → 95%** after targeted tests); **criteria cannot be specified a priori**; **avoid confirmation bias** (brainstorming categories before reading traces is Langfuse’s #1 listed mistake).

  **Criteria drift** (Shankar et al., *Who Validates the Validators?*, UIST 2024 / arXiv:2404.12272): to grade outputs, people need to define criteria; grading outputs helps them define those criteria. It is **impossible to completely determine evaluation criteria prior to human judging of LLM outputs**. Participants added criteria, reinterpreted existing ones, even changed previous grades. Open coding **is** the operationalization of criteria drift—you do not pretend the rubric existed first (Nova Escola counterexample). Treat criteria as **living documents**.

  Axial coding practice: read notes → group similar → **split** alike surface / different root cause → **merge** same underlying problem → name + one-sentence definition. LLM-assisted clustering is a **draft**—always review. LLMs cluster by **surface similarity**. Dad Tech Support: an LLM merged **passive** identity non-disclosure with **active** child impersonation—different fixes (add disclosure vs dial back persona). Human split after two refinement rounds. Spreadsheet pattern: export notes → LLM proposes 5–6 categories → **edit** → classify each note → include **none of the above** → pivot counts.

  **Theoretical saturation:** stop when new traces don’t add or reshape categories. Langfuse rule of thumb: **no new category in the last ~20 traces**; ~**100 total** often enough for a first pass. Hamel: continue past 100 while still learning.

  After taxonomy: one **boolean** score config per category; then Langfuse Step 5 in order—**Can we just fix it?** → **Is an evaluator worth it?** → **What kind?** (objective → code; judgment → LLM-as-judge in Week 17; low rate → monitor). Do not write an eval for every cell in the pivot (markdown-in-SMS may be a prompt/format fix + cheap regex).

  **SPADE** (Shankar et al., arXiv:2401.03038): synthesize assertions from prompt-version deltas—complements taxonomy work once prompts are versioned, not a substitute for open coding.

* **The Alternatives:**  

  | Taxonomy style | When useful | Failure mode |
  |----------------|-------------|--------------|
  | App-specific (`missing_device_lookup`, `denied_scope`) | Actionable fixes & evaluators | Expert time |
  | Generic (`hallucination`, `toxicity`, `helpfulness`) | Cross-product comparison / safety baselines; **trace discovery** | Not actionable; confirmation bias; do not use as product quality |
  | Multi-label every independent failure | Rich analysis | Annotator fatigue; cascade confusion |
  | First-failure-only | Faster; focuses root cause | Undercounts co-occurring issues |
  | LLM-proposed clusters unreviewed | Speed | Conflates root causes (Langfuse identity merge) |
  | Hierarchical (pivot drill-down) | PM storytelling | Overfitting tiny bins |
  | Rubric-first (Nova Escola v1) | Feels complete | Labels for failures that never occur |
  | Bottom-up (Field Guide) | Counts match user pain | Requires reading |
  | Top-down vendor catalog | Convenient | Misses domain issues |

  Hamel: generic metrics (and BERTScore/ROUGE) are not useful as product quality. IR similarity metrics are useful for **retrieval** debugging (Week 10), not as a stand-in for this taxonomy. Binary flags force a decision; nuance lives in the **critique**, not the scale.

* **Failure Modes:**  
  - Teams argue vibes; nobody owns `helpfulness`.  
  - LLM clustering merges different root causes (passive non-disclosure vs active impersonation).  
  - Evaluators multiply without ownership.  
  - Prompt fixes and CI tests don’t map to observed production pain.  
  - Criteria drift bites silently; Week 17 judges trained on vague labels cannot reach high TPR/TNR.  
  - Hallucinated settings icon filed as a separate “hallucination” bucket instead of under `missing_device_lookup` (same root cause).  
  - Vague Claude-proposed codes (`quality`, `temporal issues`) that a second labeler cannot apply.  
  - “None of the above” becomes a junk drawer.  

* **Average vs. Strong Engineer:**  
  **Average:** spreadsheet of thumbs-up/down with ad-hoc tags that never stabilize; start from hallucination/toxicity; ask an agent to “do evals” end-to-end.  
  **Strong:** score configs `open_coding` + `pass_fail` + later boolean per category; categories named after *what broke*; after taxonomy decide **fix / build evaluator / monitor only**; revisit when distribution shifts; binary + written critiques (critiques later become few-shots for judges and synthetic seeds); Nurture Boss–style UI may draft axial codes—still human-owned; use AI to **apply your judgment faster**, not invent taste; feed **new annotations** back so the agent can find similar cases. Multi-annotator path when leaving the dictator: draft definitions + examples → independent labels → Cohen’s Kappa → alignment session → update rubric → relabel → dictator breaks ties. If you need five SMEs per interaction, product scope may be too broad.

* **Worked Example:**  
  Open codes from Deployment Copilot traces become axial categories such as `policy_order_skipped` (verify/preview before commit), `markdown_in_sms`, `missing_runbook_lookup`, `handoff_not_offered`, `identity_not_disclosed`. A hallucinated “Settings → Devices” path that never existed is grouped under `missing_runbook_lookup`, not a free-floating `hallucination` bucket—same root cause as failing to call retrieve.

  Dad Tech Support taxonomy after two refinement rounds: `identity_not_disclosed`, `impersonates_child`, `missing_device_lookup`, `too_verbose`, `tone_persona_off`, `missing_clarifying_question`, `incomplete_resolution`, `denied_scope`. Nurture Boss pivot: conversation flow, handoff, date handling—three issues >60% of problems.

* **Apply It:**  
  1. Export open-coding notes; draft 5–10 snake_case names with one-sentence definitions; include “none of the above.”  
  2. Split surface-similar / different-root-cause pairs by hand (do not accept the first LLM cluster).  
  3. Relabel the sample with one boolean flag per category.  
  4. For each category, walk fix → evaluator → monitor before writing any judge.  
  5. Version the taxonomy definitions as living documents when criteria drift.  
  6. Reserve judgment-heavy residual categories for Week 17; fix clear prompt/tool gaps now.

---

### Frequency (rate × impact)

* **Fundamentals:**  
  After axial coding, **relabel** the sample with boolean flags per category. **Failure rate** = share of traces where the flag is true. Langfuse: average of a boolean score **is** the rate. Pivot tables / boolean score averages are the product decision.

  Prioritize **rate × business impact**, not rate alone. Conversational-flow issues may be frequent; **human-handoff** might still rank first if catastrophic (Aakash Gupta masterclass on Nurture Boss). Rate-only ranking ignores catastrophic rare failures; impact-only ranking may ignore the 60% blob users feel every day.

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

  Identity cluster dominated; one prompt change hit multiple high-rate categories. That is the point of **counting**. Nurture Boss: date handling went from **33% → 95%** success after targeted tests—not after a generic hallucination dashboard.

  Counting also decides **what not to automate**: Hamel/Shreya—do not build automated evaluators for every failure mode. Fix unspecified preferences in the prompt first. Automate only failures you will **iterate on repeatedly**.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Rate × impact prioritization | Product-decision clarity; PM-accessible pivots | Needs boolean relabel + impact judgment | Default after taxonomy |
  | Rate-only ranking | Simple | Ignores catastrophic rare failures | Never alone for ship priority |
  | Impact-only ranking | Protects worst cases | May ignore the daily 60% blob | Pair with rates |
  | Generic dashboard scores as priority | Fast UI | Wrong ranking vs user pain | Avoid as quality truth |
  | Fix pet peeves without counts | Feels productive | Miss the 58% identity failure | Anti-pattern |

* **Failure Modes:**  
  - Fix a pet peeve and miss the dominant rate category.  
  - Cannot tell a stakeholder a story with data (Hamel: “caught N issues before users saw them,” not “we adopted evals”).  
  - Lock priorities on a tiny labeled subset (e.g. 19 traces) before finishing ~100.  
  - Build judges for high-rate bugs a prompt fix would kill.  
  - Write an eval for every pivot cell, including one-off format bugs.  
  - After a fix, skip re-count—distribution shifted and priorities are stale.

* **Average vs. Strong Engineer:**  
  **Average:** glance at a few bad traces; never compute rates; argue about which bug “feels” worse.  
  **Strong:** boolean relabel → failure-rate chart → rate × impact ranking; Langfuse-style decision tree (fix / evaluator / monitor); show leadership a pivot; re-run counts after prompt/model/feature changes; track whether iterating on handoff **broke** date handling (suite visibility). Hamel: the pivot is the PM “superpower.”

* **Worked Example:**  
  Deployment Copilot boolean rates on ~100 traces: `policy_order_skipped` 24%, `markdown_in_sms` 18%, `missing_runbook_lookup` 11%, `incomplete_refund_readback` 4%. Impact weighting promotes `policy_order_skipped` first (unsafe write) even if `markdown_in_sms` is close in rate. One prompt + tool-gate fix collapses the identity/policy cluster; `missing_runbook_lookup` is reserved for a Week 17 judge; `incomplete_refund_readback` at 4% is monitor-only until volume justifies an assertion.

* **Apply It:**  
  1. Relabel the full working sample with booleans per taxonomy category.  
  2. Compute failure rate (mean of boolean) per category; chart it.  
  3. Rank by rate × business impact with the benevolent dictator + eng.  
  4. Fix high-rate prompt/tool bugs before any new judge work.  
  5. Mark residual judgment-heavy and low-rate categories for Week 17 / monitor.  
  6. Re-count after the next significant change; do not lock priorities on <~100 labeled traces when avoidable.

---

### Synthetic data for edge cases

* **Fundamentals:**  
  In this week’s vocabulary, **synthetic data** means **LLM-generated user inputs** (queries, tickets, utterances) that you run through the **real application** so you get **real traces**. It does **not** mean generating synthetic “gold” assistant completions and scoring against them. Field Guide guideline: **generate user inputs, not outputs**, so you do not inherit the generator’s answer biases.

  **When to use it** (Hamel FAQ): bootstrap error analysis before enough production traffic; force rare edge cases that random samples of 100 will miss. After generation: run through the **full system**, capture traces, then open-code as usual. Synthetic **cannot** estimate production **failure rates**. Compare with real traffic ASAP.

  OpenAI public evaluation best practices: collect synthetic, domain-specific, purchased, human-curated, production, and historical data as **complementary** sources; include typical, edge, and adversarial cases. Hamel still: synthetic queries must hit **your** tools/DB constraints.

  Common mistake: one-shot “give me 50 test queries” → generic, repetitive phrasing. Instead use **dimensions** (categories of variation). Examples: recipe app = dietary restriction × cuisine × query complexity; support bot = issue type × customer mood × prior context. Field Guide / Rechat Lucy: **features × scenarios × personas**:

  ```
  features  = property search, market analysis, scheduling, follow-up
  scenarios = exact match, multiple matches, no matches, invalid criteria
  personas  = first_time_buyer, investor, luxury_client, relocating_family
  ```

  Start from **failure hypotheses**. If you lack intuition, **use the app** first, then choose dimensions that target likely failures.

  **Two-step generation:** (1) Write **~20 tuples by hand** so you understand the space—e.g. `(Vegan, Italian, Multi-step)`. (2) Scale: LLM generates more **tuples**, then a **separate** prompt converts each tuple → natural language. Cross-product then filter guarantees rare edges but needs a filter for invalid combos; direct LLM tuples are more realistic but miss long-tail. Use cross-product when most combinations are valid; direct generation when many combos are nonsense.

  **Ground in system constraints:** test database (or anonymized prod copy) with enough variety; **verify** the generated query actually triggers the intended scenario (`no matches` must return zero rows). Rechat: queries use real listing IDs, schedules, HOA rules. If you have no production DB: generate both queries and underlying records, still constrained. Fix obvious problems first—don’t synthesize tests for a missing dietary-restriction instruction; **add the instruction**.

  Lucy example: synthetic CRM “create contact” instructions plus a lookup; assertion `len(results)==1`; plus regex “no exposed UUID”—synthetic inputs + **code assertions** on **system state**, not BLEU on a fake reply. Bryan Bischof (Hex): LLMs are “surprisingly good” at diverse user-prompt examples for features and evals—“large language snake eating its tail” but **it works**; still need production.

  **When synthetic is unreliable:** complex domain-specific content (legal, medical, technical forms); low-resource languages/dialects; cannot validate realism; high-stakes domains; underrepresented user groups (can reinforce generator biases). Those cases still need **real** traces and SME labeling.

  For apps with wildly different query types, do **not** pre-build a giant eval matrix by query class—let **error analysis** show which categories share failure patterns.

* **The Alternatives:**  

  | Data source | Strength | Weakness |
  |-------------|----------|----------|
  | Production sampling | Real distribution, **rates** | Cold start; privacy; rare edges missing |
  | Synthetic **inputs** → real system | Coverage of rare combos; fast | Distribution ≠ production; domain blind spots |
  | Purchased / vendor datasets | Scale | Often generic; weak product fit |
  | Human-written cases only | High quality | Expensive; incomplete coverage |
  | Fully synthetic I/O (fake answers) | Cheap | Useless for product evals of *your* pipeline |
  | Adversarial / red-team generators | Stress safety | May not match real user phrasing; still not rates |
  | Historical logs | Real past traffic | Stale vs current prompt/model |
  | Cross-product tuples then filter | Guarantees rare edges | Many invalid combos |
  | Direct LLM tuples | More realistic combos | Misses long-tail |

* **Failure Modes:**  
  - Pre-launch products have nothing to open-code (no synthetic bootstrap).  
  - Known rare failures never appear in random samples of 100.  
  - Eval sets overfit happy-path traffic and miss edge regressions.  
  - Optimize for LLM-imagined users and ship into a different distribution (OpenAI “biased design”).  
  - A “no matches” query that actually matches 40 listings tests nothing you intended.  
  - Synthetic **rates** treated as production rates.  
  - Generated assistant answers used as gold for *your* pipeline.  
  - One-shot “50 test queries” → repetitive generic phrasing.  
  - Synthesize tests for bugs you could fix immediately with a prompt change.

* **Average vs. Strong Engineer:**  
  **Average:** “Give me 50 test queries” one-shot; or synthetic dialogues including assistant lines used as gold.  
  **Strong:** structured dimensions; two-step generation; full stack with logging; mix synthetic + production; don’t synthesize tests for immediate prompt gaps; ~100 diverse traces as discovery pool; ground queries in DB/tools and verify scenario constraints; privacy: synthetic as a safer stand-in for dumping PII into vendor UIs—still validate later on real (possibly redacted) traffic. Rechat: hundreds of Level-1 assertions; continuously update from observed failures; pass rate is a **product decision**, not 100%.

* **Worked Example:**  
  Deployment Copilot undersamples “refund + SMS channel + missing identity.” You hand-write 20 tuples across `features × channels × personas × scenarios`, scale tuples with an LLM, then convert each to a natural-language user message. Each query runs through the **live** retrieve/tool/write stack; traces land in the Week 15 tracer. You open-code those traces into the existing taxonomy. You do **not** score against a model-written “correct refund reply.” A `no_matching_runbook` scenario is verified against the test index returning zero chunks before it enters the pool.

* **Apply It:**  
  1. List dimensions (features × scenarios × personas, or product-specific axes) from failure hypotheses.  
  2. Write ~20 tuples by hand; only then scale with two-step LLM generation.  
  3. Ground queries in a test DB / index; assert the intended scenario is true.  
  4. Run synthetic inputs through the **real** system; capture traces; open-code ≥30 of the discovery pool.  
  5. Never use synthetic completions as gold; never publish synthetic rates as production rates.  
  6. Fix obvious prompt/tool gaps before synthesizing more cases for them.

---

### Data flywheel (production → labels → eval set → regression)

* **Fundamentals:**  
  The eval **flywheel** is Hamel’s “virtuous cycle”: **evaluate quality**, **debug (look at data)**, **change the system** (prompt, tools, RAG, code, later fine-tune). Teams that only change the system plateau (Lucy: whack-a-mole, vibe checks, 12k-token prompts).

  Week 16’s specific loop:

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

  Labeled failures do **triple duty**: measure system quality, **calibrate** automated judges (Week 17), and **filter/curate** synthetic or fine-tuning data. Expert **critiques** become few-shots for judges and documentation. Field Guide: critiques as few-shots often yield **15–20%** higher human–judge agreement vs prompts without them (Hamel’s consulting observation—not a universal constant).

  **Stages and sample sizes** (Hamel FAQ):

  | Stage | Guidance |
  |-------|----------|
  | **1. Error discovery** | ~**100** diverse traces; **≥30** human-annotated first; continue to theoretical saturation |
  | **2. Create/validate evaluators** | **Code:** pass + fail examples for every condition + important edges. **LLM judge:** **100–200 labeled examples per failure mode**; train/dev/test split; aim **30–50 Pass and 30–50 Fail** in both dev and test when possible; track **TPR/TNR** not raw agreement — **Week 17** depth; this week **collect** labels |
  | **3. Repeatable eval set** | Often **≥100** examples covering important workflows + **confirmed failures**; grow with incidents |

  **Agreement is a trap metric:** if a failure is 10% prevalent, a judge that always predicts pass is **90% accurate**. Measure **TPR** and **TNR** separately.

  **Three levels of evaluation** (Lucy / Hamel cost stack):

  | Level | What | Cadence |
  |-------|------|---------|
  | **1 Unit / assertions** | Fast, cheap, pytest-like | Every code change (CI) |
  | **2 Human & model eval** | Binary labels; then judges aligned to humans | Cadence + after meaningful changes |
  | **3 A/B / business** | True user signal | After significant product changes |

  Do not skip Level 1. OpenAI: continuous evaluation (CE) on every change; grow the set; log everything to **mine** new cases.

  **Production sampling for regression:** Nova Escola—after taxonomy-driven judges, **daily suite on ~2% of production traffic**. Shreya: typically several code evals in CI; maybe one or two LLM evals in CI; more often **weekly sampled online** LLM judges. You do **not** need a hundred judges. Langfuse: offline datasets/experiments (CI) + online evaluators with sampling; failing prod traces → dataset items → keep as regression. Version prompts; pin dataset versions.

  **Cost-benefit:** do not automate every failure mode. Assertions/reference checks are cheap; LLM-as-judge needs 100+ labels and weekly maintenance. Nova Escola mistake: built an eval for “two learning goals instead of one”—a **prompt change stopped it**.

  **Trust, drift, leakage:** teams lose faith when metrics diverge from production. Embrace criteria drift; living rubrics; regular human–judge calibration (Week 17). **Eval-set leakage:** do not dump the golden set into the **product** model’s few-shots; only the judge-train slice may appear in the judge prompt. **Stale golden sets:** remedy with sampled production + incident promotion. Fine-tune on every failure is not the default Week 16 action—flywheel *can* feed fine-tuning later.

  Field Guide §6: traditional feature roadmaps fail for AI—**evaluation infrastructure** makes experiment cadences honest. The flywheel is organizational, not just a dataset file.

* **The Alternatives:**  

  | Loop design | Pros | Cons |
  |-------------|------|------|
  | Offline-only golden set | Stable CI | Goes stale; misses live drift |
  | Online judges on 100% traffic | Dense signal | Costly; uncalibrated noise |
  | Sampled online (e.g. **2–10%**) + offline regression | Balanced cost/coverage | Need a sampling strategy (Nova Escola 2% is an existence proof, not a universal optimum) |
  | User thumbs only | Cheap | Sparse, biased, late |
  | Fine-tune on every failure | May lift model | Quality/leakage; slower than prompt+eval |
  | Generic vendor scores as the loop | Pretty dashboards | Tools trap; vanity metrics |
  | Eval-driven imagined suite | Looks complete at launch | Nova Escola wasted labels |

* **Failure Modes:**  
  - Eval sets freeze at launch and stop catching new user behaviors.  
  - Production incidents don’t become regression tests (rediscover the same failure quarterly).  
  - Judges drift from human preference as the product changes.  
  - Stakeholders lose trust (“how do you know that metric?”).  
  - Criteria drift proceeds without versioned labels.  
  - Synthetic-only sets overfit imagined users; rates are lies.  
  - Prompt “fixes” silently break other taxonomy categories (Lucy whack-a-mole) because there is no suite.  
  - Golden set leaked into product few-shots.  
  - Offline-only suite misses live drift.

* **Average vs. Strong Engineer:**  
  **Average:** one-time golden set; occasional manual review after outages; thumbs in Discord.  
  **Strong:** every significant failure → ticket + **dataset example** + evaluator-or-monitor decision; version prompts; CE on change + scheduled production samples; Langfuse-style annotation queues → datasets → experiments → online evaluators with sampling; custom admin UI so domain experts edit prompts **in the real app context** (playgrounds lack your tools/RAG); experiment-count roadmaps; weekly error log for leadership. AlignEval-style binary human vs judge until alignment is trustworthy is **Week 17** execution—this week you collect the labels and promote failures into the set.

* **Worked Example:**  
  Deployment Copilot’s labeled `policy_order_skipped` and `markdown_in_sms` failures become rows in a versioned eval set (≥100 covering workflows + confirmed failures). CI runs Level-1 assertions (tool order, no UUID leakage, SMS has no markdown) on every change. A daily job samples ~2% of production traces (Nova Escola pattern), scores monitor categories, and failing traces are promoted into the dataset. After a handoff prompt tweak, the suite shows date-handling / policy-order still green—or flags the regression before users do. Critiques on labeled rows are stored for Week 17 few-shot judge calibration. The golden set is **not** pasted into the product system prompt.

* **Apply It:**  
  1. Promote each prioritized labeled failure into a versioned eval / golden set with the critique attached.  
  2. Add Level-1 code assertions for decidable high-rate categories; run them in CI on every change.  
  3. Schedule production sampling (start from Nova Escola’s ~2% existence proof; tune later) and route fails into the set.  
  4. Keep product prompts and eval sets versioned separately—no golden-set leakage into product few-shots.  
  5. Collect toward 100–200 labels per judgment-heavy mode for Week 17 TPR/TNR work; do not claim judge calibration this week.  
  6. Log error → learning → fix → impact for stakeholders; treat the flywheel as weekly maintenance, not a launch checkbox.

---

## Week 16 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Error-analysis pass:** Sample ~100 diverse/stratified Week 15 traces; open-code ≥30 as benevolent dictator; 20–50 in ~30 minutes after significant changes.  
2. **Custom taxonomy:** Axial-code into 5–10 binary, named, one-sentence categories; split surface-similar / different-root-cause failures; operationalize criteria drift as living definitions.  
3. **Frequency:** Boolean relabel; failure-rate chart; prioritize rate × impact; fix prompt/tool bugs before judges.  
4. **Synthetic edges:** Dimension tuples → natural-language queries through the **live** stack; open-code traces; no synthetic gold answers; no synthetic rates as production rates.  
5. **Flywheel:** Promote labeled failures into a regression eval set; CI assertions + sampled production; new incidents become new rows.  
6. **Interview artifact:** Taxonomy table with rates + one prompt fix that killed a high-rate category + one failure reserved for a judge + how production sampling refills the set.

When those steps are true, Week 16 is done in the syllabus sense: Week 15 traces have been mined into a countable taxonomy, high-rate bugs are fixed or queued, edges are stressable with synthetic inputs, and Week 17 has labels to calibrate residual judges.

---

## Looking ahead

Week 17 is the **automation and instrumentation** half of Phase 4: design **binary LLM-as-judge** prompts (Pass/Fail + critique) for residual judgment-heavy taxonomy categories; **calibrate** them against the expert labels you collected this week with **TPR/TNR** gates on held-out splits; prefer **code evals** for objective failures in CI and reserve model judges for the rest; instrument hierarchical tracing (Langfuse and/or Phoenix) so generations carry tokens/cost and retrieved context; ship **production dashboards** for cost, latency, errors, 1–3 calibrated quality timeseries, and drift — with sampled online judges and alerts that open traces. Do **not** start Week 17 by inventing new failure modes from a vendor catalog — use this week’s taxonomy and labels. The flywheel does not stop: disagreements and low scores feed annotation queues back into the set.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-4/week-16-error-analysis-flywheel/` (`00`–`04`, README).  
- No section required `[NEEDS MORE RESEARCH]` for the five syllabus concepts; research Open Questions (agent-assisted bias bounds, optimal mature vs greenfield cadence, taxonomy versioning for comparable dashboards, optimal production sample rate beyond Nova Escola’s published ~2%, multi-tenant golden-set leakage, synthetic realism metrics for medicine/law, hierarchical vs flat taxonomies at 10+ modes) remain open and were **not** resolved with invented answers.  
- Outside URLs from research are cited inline; operational detail was inlined from the notes.  
- Week 17 LLM-as-judge calibration, observability-platform bake-offs, and production dashboards are explicitly deferred.
