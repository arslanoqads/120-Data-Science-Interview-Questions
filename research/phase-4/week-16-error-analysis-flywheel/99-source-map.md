# 99 — Week 16 master source map

> Consolidated index of official docs, papers, talks, YouTube. Legal sources only; no pirate book sites, no unauthorized Maven course PDFs.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — Langfuse cookbook numbers, OpenAI Evals **platform** deprecation dates, and hamel.dev FAQ wording move.

**Not used:** Maven paid-course slide decks or leaked PDFs. Public Hamel/Shreya writing, arXiv, conference PDFs, YouTube, Langfuse, OpenAI, and independent talk write-ups only.

---

## Hamel Husain (hamel.dev)

| Topic | URL |
|-------|-----|
| AI Evals FAQ hub (MVP setup, 20–50/30min, 60–80% time, sample sizes, synthetic, cadence, binary vs Likert, outsourcing, automation cost) | https://hamel.dev/blog/posts/evals-faq/ |
| Why is error analysis so important / how performed (open/axial, 30 then agent, ~100 pool, saturation) | https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html |
| Your AI Product Needs Evals (Lucy/Rechat flywheel, Level 1–3, synthetic contacts, traces) | https://hamel.dev/blog/posts/evals/ |
| Field Guide (skip-error-analysis trap, Nurture Boss 33%→95% dates, data viewer, synthetic dimensions, criteria drift, AlignEval, experiment roadmaps) | https://hamel.dev/blog/posts/field-guide/ |
| LLM-as-a-Judge complete guide (synthetic inputs, critiques, alignment) | https://hamel.dev/blog/posts/llm-judge/ |
| Nova Escola / Lucas Machado — evals in production (rubric-before-analysis, IAA, daily 2%) | https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html |

---

## Shreya Shankar — papers & public writing

| Topic | URL |
|-------|-----|
| Who Validates the Validators? (UIST 2024) — EvalGen, **criteria drift** | https://arxiv.org/abs/2404.12272 |
| Same paper PDF (Berkeley) | https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf |
| ACM page | https://dl.acm.org/doi/10.1145/3654777.3676450 |
| SPADE — synthesizing assertions from prompt version deltas | https://arxiv.org/abs/2401.03038 |
| SPADE HTML | https://arxiv.org/html/2401.03038 |
| Ian Arawjo (coauthor) — EvalGen follow-up, public | https://ianarawjo.medium.com/evalgen-helping-developers-create-llm-evals-aligned-to-their-preferences-26757f7e145d |

Co-authored FAQ/field material is listed under hamel.dev (Hamel + Shreya).

---

## YouTube — AI evals talks (Hamel / Shreya)

| Topic | URL |
|-------|-----|
| Why AI evals are the hottest new skill — Hamel Husain & Shreya Shankar (Lenny’s Podcast) | https://www.youtube.com/watch?v=BsWxPI9UM4c |
| Intro to error analysis: custom data annotation apps | https://www.youtube.com/watch?v=qH1dZ8JLLdU |
| How to Automate AI Evals (Correctly) — Shreya (analyze → measure → improve; don’t one-shot “do evals”) | https://www.youtube.com/watch?v=tqUDjc1HzO4 |

---

## Public talk write-ups (not course PDFs)

| Topic | URL |
|-------|-----|
| Aakash Gupta — step-by-step masterclass notes (Nurture Boss traces, open/axial, pivot, TPR/TNR trap) | https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/ |
| Alternate path if the above 404s | https://www.aakashg.com/ai-evals-masterclass-with-hamel-shreya/ |
| Lenny’s Newsletter — episode notes / chapter timestamps (error analysis ~16:51) | https://www.lennysnewsletter.com/p/why-ai-evals-are-the-hottest-new-skill |

---

## Langfuse

| Topic | URL |
|-------|-----|
| Error analysis cookbook (Dad Tech Support; five steps; taxonomy; rates; fix/judge/monitor) | https://langfuse.com/guides/cookbook/error-analysis-llm-applications |
| Markdown twin | https://langfuse.com/guides/cookbook/error-analysis-llm-applications.md |
| Evals product blog (human/code/judge unification, online sampling) | https://langfuse.com/blog/2025-11-12-evals |
| LLM-as-a-judge docs (online evaluators; Week 17 adjacency) | https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge |
| Docs index | https://langfuse.com/llms.txt |

---

## OpenAI (public)

| Topic | URL |
|-------|-----|
| Evaluation best practices (task-specific evals, log mining, complementary data sources, CE, anti-patterns) | https://developers.openai.com/api/docs/guides/evaluation-best-practices |
| Markdown twin | https://developers.openai.com/api/docs/guides/evaluation-best-practices.md |

Note: OpenAI still mentions generic scores (ROUGE, G-Eval) in examples. Hamel/Shreya: treat those as **non-default product metrics**; this week prefers taxonomy-derived binary checks. Evals **platform** deprecation (read-only 2026-10-31, shutdown 2026-11-30) is operational—concepts of continuous eval remain.

---

## Mapping: source → Week 16 file

| File | Primary sources |
|------|-----------------|
| [00-week-overview.md](00-week-overview.md) | FAQ error-analysis + MVP; Langfuse cookbook; Field Guide Nurture Boss; Nova Escola; criteria-drift paper |
| [01-error-analysis-first-workflow.md](01-error-analysis-first-workflow.md) | FAQ MVP / cadence / sampling / annotators; Lenny YouTube; annotation-app YouTube; Langfuse step 1; evals post viewers |
| [02-open-coding-taxonomy.md](02-open-coding-taxonomy.md) | Error-analysis FAQ; Langfuse steps 2–5; Field Guide bottom-up; Aakash axial/pivot; arXiv 2404.12272; SPADE |
| [03-synthetic-data-edge-cases.md](03-synthetic-data-edge-cases.md) | FAQ synthetic + unreliability; Field Guide §4; llm-judge; Lucy synthetic contacts; OpenAI data mix |
| [04-data-flywheel.md](04-data-flywheel.md) | evals post levels; FAQ sample sizes; Field Guide trust/roadmaps; Nova Escola 2%; Langfuse online evals; OpenAI CE |

---

## Explicitly out of scope (Week 17+)

Judge **calibration recipes**, observation-level vs trace-level judges, Phoenix vs Langfuse vs Braintrust bake-offs, OpenAI Evals API migration. Cited only where they **close** the flywheel or explain why error analysis comes first.
