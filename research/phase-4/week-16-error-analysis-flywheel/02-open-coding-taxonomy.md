# 02 — Open coding & taxonomy building (failure modes)

> Week 16 — Open → axial coding; custom binary categories; frequency  
> Research notes (raw).

---

## Fundamentals

Failure taxonomies for LLM products are **induced from traces**, not copied from eval-vendor catalogs. The method is adapted from **qualitative research** (and long used in ML error analysis). Hamel/Shreya names:

1. **Open coding** — Read each trace end-to-end; write short free-text observations of anything wrong, unexpected, or bad for the user. **No predefined category list.**  
2. **Axial coding** — Group open codes into a **failure taxonomy**: typically **5–10** named categories, each with a **one-sentence definition** another person could apply. Then **count**. Axial coding is “the most important step” ([error-analysis FAQ](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html)).

Langfuse uses the same two terms throughout the [cookbook](https://langfuse.com/guides/cookbook/error-analysis-llm-applications).

### Open coding (journaling)

Rules that show up consistently across Hamel FAQ, Langfuse, Aakash masterclass, and the annotation YouTube:

| Do | Don’t |
|----|--------|
| Describe **behavior** (“bot said it can’t look things up”) | Diagnose root cause in the note (“web search broken”) |
| Early on, note the **first** failure (cascades) | Optional later: tag all **independent** failures if feasible |
| Domain expert / benevolent dictator | Generic BPO as first pass |
| ≥**30** traces yourself before agent suggestions | Let an LLM propose the taxonomy from zero |
| Binary **pass/fail** plus notes | Likert 1–5 on the discovery pass |
| Move on (~30s–minutes per trace) | Debate one trace endlessly |

Langfuse score configs for the first queue: `open_coding` (text) + `pass_fail_assessment` (categorical). **Write the description** that appears in the UI or annotators guess.

Example notes (Dad Tech Support):

| Trace | open_coding | pass_fail |
|-------|-------------|-----------|
| 001 | Agent does not tell user he is not actually the kid | Fail |
| 002 | Too long | Fail |
| 003 | Did not properly look up current phone info | Fail |
| 004 | Follow-up missed; should have asked what kind of PIN | Fail |
| 005 | Agent impersonates kid too much | Fail |
| 006 | Icon did not exist that the agent mentioned | Fail |
| 007 | (clean) | Pass |

Nurture Boss examples (Aakash / Lenny): “told user it would check bathrooms but didn’t”; “markdown in a text message”; “should have handed off”; “we don’t do virtual tours”; “reschedule booked a second tour.”

Hamel: after ~100 traces you already understand the system better than anyone; analysis of the **notes** still pays (pivot).

### Axial coding (taxonomy)

Goal: **5–10 distinct, named** categories with definitions. Langfuse clustering steps: read notes → group similar → **split** alike surface / different root cause → **merge** same underlying problem → name + one-sentence definition.

**Name after what broke.** `missing_device_lookup` > `information_quality`. `identity_not_disclosed` > `transparency`. Shreya on Claude-proposed Nurture Boss codes: reject vague `quality` / `temporal issues`; prefer `date formatting error` / `conversational flow` that a second labeler could apply ([Aakash](https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/)).

**LLM-assisted clustering is a draft.** Langfuse prompt pattern: paste notes; ask for 5–10 snake_case names, one-sentence definitions, membership. **Always review.** LLMs cluster by **surface similarity**. Dad Tech Support: LLM merged **passive** identity non-disclosure with **active** child impersonation—different fixes (add disclosure vs dial back persona). Human split after two refinement rounds.

Hamel spreadsheet pattern: export notes → LLM proposes 5–6 categories → **edit** → classify each note (spreadsheet AI formula) → include **none of the above** so missed categories surface → **pivot table counts**. Optional hierarchy (conversational flow → repeated messages vs should-have-handled).

FAQ: after 30 annotations, let an agent **search remaining traces** for likely instances; **accept/reject** every suggestion.

### Theoretical saturation

Stop when new traces don’t add or reshape categories. Langfuse rule of thumb: **no new category in the last ~20 traces**; ~**100 total** often enough for a first pass. Hamel: continue past 100 while still learning.

### Label, quantify, decide

Langfuse Step 4: one **boolean** score config per category; description of what `true` means (example: generic guidance without checking the user’s phone UI, including hallucinated icons). New annotation queue (queues often **immutable**; re-add observations—prior notes remain). Failure rate = mean of boolean.

**Bottom-up vs top-down** ([Field Guide](https://hamel.dev/blog/posts/field-guide/)):

- Top-down: start with hallucination/toxicity + a few task metrics — convenient, **misses domain issues**.  
- Bottom-up: spreadsheet rows = conversations; open notes; LLM-draft taxonomy; map rows to labels; **count**. Nurture Boss: **three issues >60%** of problems (flow, handoff, rescheduling/dates).

**Binary flags** (Hamel FAQ: why not Likert): force a decision; faster; Likert 3-vs-4 is inconsistent; businesses binarize anyway. Nuance lives in the **critique**, not the scale. Sub-components can each be binary (“4 of 5 expected facts”) if you need partial credit.

Langfuse Step 5 — for each category, in order:

1. **Can we just fix it?** Missing prompt requirement, contradicting instructions, missing tool, engineering bug. **Fix first.**  
2. **Is an evaluator worth it?** Rate, business impact, will someone iterate on the evaluator?  
3. **What kind?** Objective → **code**; judgment → **LLM-as-judge** (Week 17); safety/compliance → evaluator as **guardrail** even after prompt fix. Low rate → **monitor**.

Do not write an eval for every cell in the pivot (Hamel/Shreya: markdown-in-SMS may be a prompt/format fix + cheap regex).

### Criteria drift (Shreya Shankar public research)

*Who Validates the Validators?* (Shankar, Zamfirescu-Pereira, Hartmann, Parameswaran, Arawjo; UIST 2024; [arXiv:2404.12272](https://arxiv.org/abs/2404.12272); [Berkeley PDF](https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf)):

- LLM-generated evaluators inherit LLM problems; humans must **validate the validators**.  
- EvalGen: mixed-initiative criteria + assertion implementations; humans grade a subset; implementations selected to match grades.  
- **Criteria drift:** “to grade outputs, people need to externalize and define their evaluation criteria; however, the process of grading outputs helps them to define those very criteria.” It is **impossible to completely determine evaluation criteria prior to human judging of LLM outputs**. Participants added criteria, **reinterpreted** existing ones, even **changed previous grades**.  
- Some criteria are **dependent on the specific outputs observed**, challenging pipelines that assume evaluation is independent of observation.  
- Implication: tooling must support **simultaneous** iteration on criteria and grades. Hamel Field Guide: treat criteria as **living documents**; Honeycomb’s Phillip Carter: seeing LLM reasoning revealed **inconsistent** personal standards on edge cases.

Open coding **is** the operationalization of criteria drift: you do not pretend the rubric existed first (Nova Escola counterexample).

**SPADE** (Shankar et al., [arXiv:2401.03038](https://arxiv.org/abs/2401.03038)): synthesize **assertions** from **prompt version history** deltas; ILP to cover failures with few false fails. Complements taxonomy work once prompts are versioned—not a substitute for open coding.

### Multi-annotator alignment (when you leave the dictator)

Draft Pass/Fail definitions + examples → independent labels on a shared set → **Cohen’s Kappa** (chance-corrected) → alignment session: which rubric clause caused disagreement → update definition/rule/example → relabel → dictator breaks remaining ties ([FAQ](https://hamel.dev/blog/posts/evals-faq/)).

---

## Alternatives & Tradeoffs

| Taxonomy style | When useful | Failure mode |
|----------------|-------------|--------------|
| App-specific (`missing_device_lookup`, `denied_scope`) | Actionable fixes & evaluators | Expert time |
| Generic (`hallucination`, `toxicity`, `helpfulness`) | Cross-product comparison / safety baselines; **trace discovery** | Not actionable; confirmation bias; Hamel: do not use as quality |
| Multi-label every independent failure | Rich analysis | Annotator fatigue; cascade confusion |
| First-failure-only | Faster; focuses root cause | Undercounts co-occurring issues |
| LLM-proposed clusters unreviewed | Speed | Conflates root causes (Langfuse identity merge) |
| Hierarchical (pivot drill-down) | PM storytelling | Overfitting tiny bins |
| Rubric-first (Nova Escola v1) | Feels complete | Labels for failures that never occur |

Hamel on **generic metrics**: not useful as product quality (BERTScore/ROUGE similarly). IR similarity metrics **are** useful for **retrieval** debugging (Week 10), not as a stand-in for this taxonomy.

---

## Necessity

Without a grounded taxonomy:

- Teams argue vibes instead of countable rates.  
- Evaluators multiply without ownership (“who owns helpfulness?”).  
- Prompt fixes and CI tests don’t map to observed production pain.  
- Criteria drift bites silently.  
- Judges trained on vague labels cannot reach high TPR/TNR (Week 17).

Without **quantifying** after coding:

- You cannot choose rate × impact.  
- You cannot show leadership a pivot (Hamel: this is the PM “superpower”).

---

## Industry Practice

**Common:** Spreadsheet of thumbs-up/down with ad-hoc tags that never stabilize.

**Strong:**

- Score configs: `open_coding` + `pass_fail` + later boolean per category (Langfuse).  
- Categories named after *what broke*.  
- After taxonomy: **fix / build evaluator / monitor only** (Langfuse step 5).  
- Revisit taxonomy when distribution shifts after model/prompt changes.  
- Binary + written critiques; critiques later become few-shots for judges and synthetic seeds ([Field Guide](https://hamel.dev/blog/posts/field-guide/)).  
- Nurture Boss custom UI includes a step that **drafts** axial codes—still human-owned.  
- Shreya LinkedIn/public talks: two mistakes with AI-assisted analysis—(1) asking the agent to “do evals” end-to-end instead of **analyze / measure / improve** split; (2) not feeding **new annotations** back so the agent can find similar cases. Use AI to **apply your judgment faster**.

---

## Concrete Scenario (URL)

**Dad Tech Support taxonomy (after two refinement rounds)** — `identity_not_disclosed`, `impersonates_child`, `missing_device_lookup`, `too_verbose`, `tone_persona_off`, `missing_clarifying_question`, `incomplete_resolution`, `denied_scope`. Hallucinated settings icon **grouped under** `missing_device_lookup` (same root cause), not a separate “hallucination” bucket.  
https://langfuse.com/guides/cookbook/error-analysis-llm-applications

**Nurture Boss pivot** — conversation flow, handoff, date handling; date success 33% → 95%.  
https://hamel.dev/blog/posts/field-guide/  
https://www.youtube.com/watch?v=BsWxPI9UM4c  
https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/

**Shankar et al., Who Validates the Validators?** — criteria drift, EvalGen.  
https://arxiv.org/abs/2404.12272  
https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf  
Ian Arawjo public follow-up on EvalGen UX (per-criteria grading, force a few grades before criteria): https://ianarawjo.medium.com/evalgen-helping-developers-create-llm-evals-aligned-to-their-preferences-26757f7e145d

**SPADE assertion synthesis from prompt diffs.**  
https://arxiv.org/abs/2401.03038

**YouTube: open notes before categories.**  
https://www.youtube.com/watch?v=qH1dZ8JLLdU  
https://www.youtube.com/watch?v=tqUDjc1HzO4

---

## Open Questions

- Best practices for multi-annotator agreement past a single benevolent dictator?  
- How to **version** taxonomies as products evolve without breaking historical dashboards?  
- When should failure modes be hierarchical vs flat?  
- How to handle **agent trajectories** (multi-span) vs single-generation annotation units (Week 15 vs Langfuse last-turn)?  
- Should first-failure-only remain the default for multi-agent graphs?  
- How to keep “none of the above” from becoming a junk drawer?

---

## Sources

- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- https://hamel.dev/blog/posts/evals-faq/  
- https://hamel.dev/blog/posts/field-guide/  
- https://langfuse.com/guides/cookbook/error-analysis-llm-applications  
- https://arxiv.org/abs/2404.12272  
- https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf  
- https://arxiv.org/abs/2401.03038  
- https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
- https://www.youtube.com/watch?v=qH1dZ8JLLdU  
- https://www.youtube.com/watch?v=tqUDjc1HzO4  
- https://ianarawjo.medium.com/evalgen-helping-developers-create-llm-evals-aligned-to-their-preferences-26757f7e145d  
