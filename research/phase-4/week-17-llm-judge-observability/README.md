# Week 17 Research Corpus — LLM-as-judge & observability

> Phase 4 — Evals and Observability  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (hamel.dev, G-Eval / ACL Anthology, Shreya Shankar papers, Langfuse / Arize Phoenix docs, OpenAI evals, YouTube talks). **No pirate PDFs, no libgen/pdfcoffee, no unauthorized Maven decks.**

This directory is the Week 17 research repository. Read concept files in order, then the source map. **Do not start Week 18 (deployment / infra) from this corpus** — this week **calibrates LLM judges against Week 16 expert labels**, **chooses code vs model evals**, **instruments tracing (Langfuse / Phoenix)**, and **ships production dashboards** (cost, latency, error, quality, drift). Container/K8s/CI/CD/Terraform is next week.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | LLM-as-judge **validated vs Week 16 labels**; tracing dashboard as the substrate |
| 01 | [01-llm-as-judge-design.md](01-llm-as-judge-design.md) | Critique shadowing; binary + critique; G-Eval; scoped failure modes |
| 02 | [02-judge-alignment-calibration.md](02-judge-alignment-calibration.md) | TPR/TNR gates; splits; criteria drift; AlignEval; recalibration |
| 03 | [03-code-based-vs-model-based-evals.md](03-code-based-vs-model-based-evals.md) | Decision tree; OpenAI graders; CI vs sampled online |
| 04 | [04-observability-platforms.md](04-observability-platforms.md) | Langfuse + Arize Phoenix; OTEL; spans/generations; OpenInference |
| 05 | [05-production-monitoring-dashboards.md](05-production-monitoring-dashboards.md) | Cost, latency, error rate, quality scores, drift; alerts vs guardrails |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 17)

- [x] All syllabus Week 17 concepts covered with **7 required fields**  
- [x] **LLM-as-judge design** that is meant to correlate with **human** (principal domain expert) judgment — not vendor kitchen-sink scores  
- [x] **Critique shadowing** (Hamel): expert Pass/Fail + critique → few-shot judge → iterate  
- [x] **G-Eval** (Liu et al., EMNLP 2023): CoT + form-filling; Spearman **~0.514** on SummEval; **bias toward LLM-generated text**  
- [x] **Alignment / calibration** vs Week 16 expert labels: TPR & TNR (not raw accuracy under imbalance); train/dev/held-out splits  
- [x] **Criteria drift** (Shankar et al., *Who Validates the Validators?*, arXiv:2404.12272) as a reason calibration is continuous  
- [x] **Code-based vs model-based evals:** fix first → deterministic if possible → judge for residual judgment → humans as ground truth  
- [x] OpenAI evals: `string_check` / deterministic graders vs model graders; cookbook + evals API + openai/evals; platform deprecation noted  
- [x] **Observability platforms:** Langfuse (traces, generations, scores, experiments, prompt mgmt) and Arize Phoenix (OTEL + OpenInference)  
- [x] Spans vs generations; OpenInference span kinds (`LLM`, `RETRIEVER`, `TOOL`, `EVALUATOR`, …)  
- [x] **Production dashboards:** cost/tokens, p50/p95/p99 latency, error rate, sampled quality scores, drift  
- [x] Sampling (Nova Escola ~2%; Langfuse faithfulness **5–10%** typical); online evals **async** ≠ blocking guardrails  
- [x] YouTube: Lenny’s Podcast Hamel & Shreya (`BsWxPI9UM4c`); Hamel *How To Approach Your AI Evals* (`DZxaPNYi_k0`)  
- [x] Langfuse: observation-level judges; judge executions are traces (`langfuse-llm-as-a-judge`); ~$0.01–0.10 per assessment  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 17)

You already have **Week 16 labels and a custom taxonomy**. This week you **automate residual subjective failures** and **make traces usable as a product**.

1. **Design judges, not dashboards of 1–5s.** One **binary** judge per high-impact Week 16 failure mode that needs judgment (`should_have_clarified`, faithfulness given retrieved docs). Pass/Fail + written critique. Principal domain expert owns the standard.  
2. **Calibrate against Week 16 labels.** Split labeled examples (Hamel: ~10–20% few-shot train, ~40–45% dev, ~40–45% held-out test; aim 30–50 Pass and Fail in dev and test). Gate on **TPR and TNR**. Do not ship a judge that fails the gate. Recalibrate when the app model, judge model, or product criteria change.  
3. **Prefer code evals** for objective failures (JSON, schema, citation IDs ⊆ retrieved IDs, tool name). Reserve LLM judges for the rest. Put several code evals in CI; LLM judges sparingly in CI or on a **sampled schedule**.  
4. **Tracing dashboard.** Instrument hierarchical traces (Langfuse **and/or** Phoenix). Generations carry `model`, params, tokens, cost. Attach retrieved context on the observation you will judge. Tag `userId` / `sessionId` / `version` / `env`.  
5. **Production monitoring.** Dashboards for volume, errors, p95 latency, cost/day and cost/successful-task, and **1–3 calibrated** quality timeseries. Alerts open **traces**, not just pages. Sample online judges (2–10%). Blocking safety stays **in-request**; async evaluators are for trends and triage.

Interview artifact = **one calibrated binary judge** with TPR/TNR on a held-out Week 16 set + **a screenshot/description of a tracing dashboard** that shows a generation with tokens/cost and a score attached + **one code eval that replaced a would-be judge**.

## Default path (synthesis)

1. **Judges are products.** Scope to one failure mode; binary + critique; expert first ([Hamel LLM-as-a-Judge](https://hamel.dev/blog/posts/llm-judge/)).  
2. **Alignment is TPR/TNR on held-out humans**, not vibes or raw agreement ([FAQ: same model](https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html); YouTube [`DZxaPNYi_k0`](https://www.youtube.com/watch?v=DZxaPNYi_k0)).  
3. **G-Eval is research evidence that CoT judges can beat ROUGE**, not a product score you drop in uncalibrated ([ACL Anthology](https://aclanthology.org/2023.emnlp-main.153/)).  
4. **Code first, judge second, human as truth** ([Langfuse evals blog](https://langfuse.com/blog/2025-11-12-evals); Lenny [`BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c); [OpenAI evals](https://developers.openai.com/api/docs/guides/evals)).  
5. **Tracing is the substrate** — generations, OpenInference kinds, attach context for faithfulness ([Langfuse observability](https://langfuse.com/docs/observability/overview); [Phoenix traces](https://arize.com/docs/phoenix/tracing/llm-traces); [OpenInference spec](https://arize-ai.github.io/openinference/spec/)).  
6. **Dashboards mix cost + latency + errors + calibrated quality + drift**; sample online; guardrails ≠ monitors ([faithfulness engineering](https://langfuse.com/resources/engineering/rag-faithfulness-evaluation); [Nova Escola](https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html)).
