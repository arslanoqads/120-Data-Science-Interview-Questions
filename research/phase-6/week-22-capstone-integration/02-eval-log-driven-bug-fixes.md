# 02 — Turning eval logs into prioritized bug fixes

> Week 22 — Capstone integration  
> Research notes (raw). Meta-concept: eval logs as a work queue for polish week.

---

## Fundamentals

Eval logs are not a dashboard vanity metric; they are a **work queue**. Hamel Husain’s error-analysis loop is the meta-skill for capstone weeks ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/); [error-analysis FAQ](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html)):

1. **Sample traces** — start ~20–50 after significant changes; working pool often ~100 diverse; prefer noting the **first** failure in a trace (upstream cascades).  
2. **Open-ended notes (“journaling”)** by a domain-aware reviewer (benevolent dictator).  
3. **Axial coding** → **failure taxonomy** with counts.  
4. **Write evals for observed modes** — code assertions vs LLM-judge (only for subjective residuals).  
5. **Fix highest-frequency / highest-severity classes first**; regenerate/expand golden set; repeat.

Priority is usually **frequency × user severity × fix leverage**, not “average score went up 2%.” Many issues found in error analysis are ordinary bugs (bad chunk metadata, wrong tool schema, prompt contradiction)—**fix immediately**; only persistent subjective failures need judge infrastructure ([Field Guide](https://hamel.dev/blog/posts/field-guide/); FAQ hub: [evals-faq](https://hamel.dev/blog/posts/evals-faq/)).

### Capstone top-5 bug classes (from overview)

Reuse the Week 22 default ranking unless *your* counts disagree:

| Rank | Class | Why it dominates polish week | Typical fix |
|------|-------|------------------------------|-------------|
| 1 | Wrong / empty retrieval | Breaks every downstream claim | Metadata filters, hybrid weights, reindex, chunk boundaries |
| 2 | Ungrounded / fake citations | Trust killer in live demos | Citation aligner, faithfulness assert, refuse-if-unquoted |
| 3 | Tool schema / selection bugs | Flaky agent path; duplicate writes | JSON schema validation, tighter tool descriptions, idempotency keys |
| 4 | Refusal / abstain failures | Cannot show control | Thresholds, “I don’t know” goldens, over-refuse cases |
| 5 | ACL / tenancy / PII leak | Rare but catastrophic | Filter-before-rank, middleware tenant inject, red-team goldens |

Hamel on Lenny’s Podcast: people get lost jumping straight into writing tests — ground yourself in **actual errors** first ([YouTube `BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c)). Shreya’s annotation walkthrough: build a low-friction viewer; free-form notes; do not categorize too early ([YouTube `qH1dZ8JLLdU`](https://www.youtube.com/watch?v=qH1dZ8JLLdU)).

### From taxonomy to fix tickets

Convert each high-count category into an engineering ticket with:

- **Repro trace ID** (or golden query).  
- **Layer hypothesis** — retrieval / prompt / tool / auth / index freshness (Huyen platform layers help you avoid “swap the LLM” as default).  
- **Fix type** — code bug vs prompt vs data vs eval-only monitor.  
- **Regression artifact** — one automated check before merge.  
- **Demo note** — whether this mode is shown live as a *controlled* failure or must be green on happy path.

Binary **pass/fail + critique text** often beats 1–5 Likert for iteration speed (Hamel). A ~70% pass rate on a stressful set can be healthier than 100% on easy vibes.

### Logging / eval as a platform layer

Chip Huyen treats **observability** (logging, monitoring, eval hooks) as a first-class GenAI platform component — without it you cannot see which layer failed ([GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html)). Capstone implication: if traces are incomplete (no retrieval set, no tool args, no final citations), fix instrumentation **before** another prompt pass.

Anthropic’s public FDE posting lists **evaluation frameworks** alongside prompt engineering, agents, and production deployment as required production LLM experience ([Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)). Saying “we look at traces weekly and ship taxonomy-driven fixes” is role-shaped language.

### Worked prioritization example (illustrative)

Suppose 40 open-coded traces:

| Category | Count | Severity (1–5) | Leverage | Score (count×sev×lev) | Action |
|----------|-------|----------------|----------|------------------------|--------|
| `chunk_meta_tenant_filter_bug` | 8 | 5 | 3 | 120 | Fix now + ACL golden |
| `citation_off_by_one` | 10 | 4 | 3 | 120 | Fix now + faithfulness assert |
| `tool_missing_invoice_id` | 7 | 4 | 3 | 84 | Schema validation |
| `answers_on_corpus_miss` | 6 | 4 | 2 | 48 | Refusal prompt + goldens |
| `tone_too_verbose` | 9 | 2 | 2 | 36 | Defer or light prompt tweak |
| `judge_disagrees_on_style` | 3 | 2 | 1 | 6 | Monitor; Week 17 judge work |

Severity overrides pure count: an ACL bug at count=2 still outranks verbose tone at count=15 for enterprise/FDE demos.

---

## Alternatives & Tradeoffs

| Prioritization heuristic | Strength | Weakness |
| --- | --- | --- |
| **Count-ranked taxonomy** | Forces focus; demos “data-driven iteration” | Can undervalue rare catastrophic failures (ACL leak, unsafe action) |
| **Severity / blast-radius first** | Matches production / FDE instincts | Needs explicit severity rubric or you thrash |
| **frequency × severity × leverage** | Balances product + engineering reality | Requires honest leverage estimates |
| **Metric chasing** (generic coherence/fluency) | Easy tooling | Misaligned with product; Hamel warns against platform default metrics |
| **Only automated judges** | Scales | Without human error analysis, you optimize the wrong thing |
| **Only vibe checks** | Fast early | No regression gate; demo flips flop |
| **Eval-driven development of imagined failures** | Feels proactive | Hamel: generally **no** — unbounded failure surface; write evals for discovered errors |

---

## Necessity

Skipping error analysis → writing generic evals → “improving” the wrong layer (swap LLM when retrieval recall is the bug). Capstone without a prioritized fix list looks like random prompt thrash in demos and interviews.

Without promoting fixes into regression tests: the same failure returns the night before the demo. Without severity weighting: you polish tone while an ACL footgun remains.

Hamel consulting heuristic: **60–80%** of eval time looking at data — many “eval” findings are ordinary bugs that never needed a judge.

---

## Industry Practice

| Bar | Practice |
|-----|----------|
| **Common** | Langfuse/Phoenix/Braintrust traces exist; nobody triages them weekly; README cites “evals” without taxonomy |
| **Strong** | Spreadsheet or tagged traces → top-3/5 failure modes on README; each mode ≥1 regression test; CI or scripted `make eval` blocks prompt/retrieval regressions |
| **FDE / Applied AI signal** | Error analysis cadence after every significant change; production sample feeds the golden set; Anthropic-style “evaluation frameworks” language backed by artifacts |

Office-hours note on analyzing **real conversations** before Azure-style generic metrics: [Hamel office hours](https://hamel.dev/notes/llm/officehours/erroranalysis.html).

Field Guide: the highest-ROI investment is often a **simple domain-specific data viewer**, not a fancier dashboard ([Field Guide](https://hamel.dev/blog/posts/field-guide/)).

---

## Concrete Scenario (URL)

**Canonical Hamel loop + FAQ.** Why error analysis comes before tests; how open → axial coding works; minimum viable setup of 20–50 outputs in ~30 minutes after changes:

- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/notes/llm/officehours/erroranalysis.html  

**Nurture Boss / Field Guide.** Bottom-up coding surfaces a few modes covering most failures; targeted tests move a stubborn mode (e.g. date handling) from low success to high — not a generic hallucination dashboard ([Field Guide](https://hamel.dev/blog/posts/field-guide/); Lenny’s [YouTube](https://www.youtube.com/watch?v=BsWxPI9UM4c); Aakash masterclass write-up: https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/).

**Annotation UX.** Shreya builds a custom viewer in minutes so friction does not kill the habit ([YouTube `qH1dZ8JLLdU`](https://www.youtube.com/watch?v=qH1dZ8JLLdU)).

---

## Open Questions

- What severity weight should safety / ACL failures get relative to answer quality in a hiring demo?  
- When is synthetic expansion of failure modes safe vs distribution-shift theater?  
- How do you present “we fixed 3 of 7 taxonomy buckets” without sounding unfinished?  
- Should the demo show a *fixed* former failure (before/after) or only current controlled failures?

---

## Sources

- Hamel Husain, Your AI Product Needs Evals: https://hamel.dev/blog/posts/evals/  
- Hamel, Error analysis FAQ: https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- Hamel, Evals FAQ index: https://hamel.dev/blog/posts/evals-faq/  
- Hamel, Field Guide: https://hamel.dev/blog/posts/field-guide/  
- Hamel, Office hours — error analysis: https://hamel.dev/notes/llm/officehours/erroranalysis.html  
- Hamel / Shreya, Lenny’s Podcast (YouTube): https://www.youtube.com/watch?v=BsWxPI9UM4c  
- Shreya / Hamel, Intro to error analysis annotation (YouTube): https://www.youtube.com/watch?v=qH1dZ8JLLdU  
- Aakash Gupta, Hamel/Shreya masterclass write-up: https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
- Anthropic FDE responsibilities (evals called out): https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Chip Huyen GenAI platform (logging/eval as platform layer): https://huyenchip.com/2024/07/25/genai-platform.html  
