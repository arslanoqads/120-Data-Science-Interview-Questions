# Week 16 Research Corpus — Error analysis & the data flywheel

> Phase 4 — Evals and Observability  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (hamel.dev, Shreya Shankar papers, Langfuse docs, OpenAI public guides, YouTube AI evals talks). **No pirate Maven PDFs, no libgen/pdfcoffee.**

This directory is the Week 16 research repository. Read concept files in order, then the source map. **Do not start Week 17 (LLM-as-judge / observability platforms) from this corpus** — this week **mines traces** into a **custom failure taxonomy**, **quantifies frequency**, **bootstraps edges with synthetic inputs**, and **closes the production → labels → eval set → regression** flywheel. Judge *calibration*, code-vs-model evals, and tracing product choices are next week.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Error-analysis **pass**; custom failure taxonomy; **frequency** (rate × impact) |
| 01 | [01-error-analysis-first-workflow.md](01-error-analysis-first-workflow.md) | Read **20–50** outputs before metrics; benevolent dictator; cadence |
| 02 | [02-open-coding-taxonomy.md](02-open-coding-taxonomy.md) | Open coding → axial coding → boolean labels; criteria drift |
| 03 | [03-synthetic-data-edge-cases.md](03-synthetic-data-edge-cases.md) | Dimension tuples → queries through the **real** system; not fake gold answers |
| 04 | [04-data-flywheel.md](04-data-flywheel.md) | Production → labels → eval set → regression prevention |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 16)

- [x] All syllabus Week 16 concepts covered with **7 required fields**  
- [x] **Error-analysis-first:** 20–50 traces after significant changes; ≥30 human-open-coded before agent; ~100 working pool  
- [x] **Custom failure taxonomy** (not generic helpfulness/hallucination/toxicity as product scores)  
- [x] **Frequency:** failure rates + rate × business impact; Langfuse Dad Tech Support chart; Nurture Boss 3 issues ≈ 60%  
- [x] Open coding vs axial coding; first-failure vs multi-label; theoretical saturation  
- [x] **Criteria drift** (Shankar et al., UIST 2024 / arXiv:2404.12272)  
- [x] Synthetic **inputs** (features × scenarios × personas; two-step generation); Hex / Rechat / Lucy cases  
- [x] Flywheel: traces → taxonomy → targeted evals → golden set → CI / sampled production → new failures  
- [x] Nova Escola: rubric-before-analysis waste; IAA worse than chance; daily **2%** production suite  
- [x] Langfuse five-step cookbook (sample, open code, cluster, quantify, fix/judge/monitor)  
- [x] Hamel FAQ: budget 60–80% looking at data; binary pass/fail; do **not** eval-driven-develop imagined failures  
- [x] OpenAI evaluation best practices (log everything; complementary data sources; continuous eval) cited as public docs, not as a substitute for error analysis  
- [x] YouTube: Lenny’s Podcast (`BsWxPI9UM4c`); Hamel/Shreya error-analysis annotation (`qH1dZ8JLLdU`); Shreya automate-evals (`tqUDjc1HzO4`)  
- [x] Public talk write-ups: Aakash Gupta masterclass; Lenny newsletter chapter timestamps  
- [x] SPADE (Shankar et al., arXiv:2401.03038) as assertion-synthesis context — not Maven course notes  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 16)

Do **not** skip to LLM-as-judge dashboards. You already have **structured traces** from Week 15. This week you **read them**.

1. **Error-analysis pass.** Sample ~100 diverse traces (or synthetic-through-prod if cold start). Personally open-code **≥30**, preferably **20–50 in ~30 minutes** after every significant prompt/model/feature change (Hamel minimum viable setup). One **benevolent dictator** (domain expert) owns pass/fail + free-text notes.  
2. **Custom taxonomy.** Axial-code notes into **5–10** binary, named, one-sentence categories grounded in *this* app (`missing_device_lookup`, not `hallucination`). Split surface-similar failures with different root causes.  
3. **Frequency.** Relabel the sample with boolean flags; compute **failure rate per category**; prioritize **rate × impact**. Fix prompt/tool bugs **before** building judges (Langfuse decision tree; Nova Escola two-goals-in-one-output).  
4. **Synthetic edges.** If production undersamples a known combo, generate **dimension tuples → natural-language queries**, run them through the **live stack**, open-code the traces. Do **not** use synthetic completions as gold.  
5. **Flywheel.** Promote labeled failures into a **regression eval set**; run on change (CI) and on a **production sample** (Nova Escola 2% daily). New incidents become new rows. Week 17 is when you **calibrate** residual LLM judges.

Interview artifact = **taxonomy table with rates** + one **prompt fix that killed a high-rate category** + one **failure reserved for a judge** + a sentence on how production sampling refills the set.

## Default path (synthesis)

1. **Read before you measure.** 20–50 manual reviews beat premature automation ([Hamel FAQ](https://hamel.dev/blog/posts/evals-faq/); [Lenny’s Podcast](https://www.youtube.com/watch?v=BsWxPI9UM4c)).  
2. **Taxonomies emerge from data** via open → axial coding ([error-analysis FAQ](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html); [Langfuse cookbook](https://langfuse.com/guides/cookbook/error-analysis-llm-applications)). Generic vendor metrics are exploration signals, not quality scores.  
3. **Count.** Pivot tables / boolean score averages are the product decision ([Aakash Gupta write-up](https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/); Nurture Boss [field guide](https://hamel.dev/blog/posts/field-guide/)).  
4. **Synthetic inputs bootstrap and stress**; production **rates** still require production samples ([synthetic FAQ](https://hamel.dev/blog/posts/evals-faq/); [OpenAI best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)).  
5. **Flywheel closes the loop:** labeled production failures become the regression suite and (later) judge-calibration set ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/); [Nova Escola](https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html)).  
6. **Fix first, evaluate second** for clear prompt/tool bugs; reserve judges for subjective residual failures (Week 17).
