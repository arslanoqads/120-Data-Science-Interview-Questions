# 99 — Week 17 master source map

> Consolidated index of official docs, papers, talks, YouTube. Legal sources only; no pirate book sites, no unauthorized Maven course PDFs.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — Langfuse v4 evaluator cutover, OpenAI Evals **platform** deprecation dates, Phoenix UI paths, and hamel.dev wording move.

**Not used:** Maven paid-course slide decks or leaked PDFs. Public Hamel/Shreya writing, ACL/arXiv, YouTube, Langfuse, Phoenix/OpenInference, OpenAI, Anthropic public PDF, GitHub discussions, independent talk write-ups only.

---

## Hamel Husain (hamel.dev)

| Topic | URL |
|-------|-----|
| Using LLM-as-a-Judge (critique shadowing, Honeycomb, binary+critique, TPR/TNR warning) | https://hamel.dev/blog/posts/llm-judge/ |
| Your AI Product Needs Evals (Level 1–3, Lucy/Rechat, assertions) | https://hamel.dev/blog/posts/evals/ |
| Field Guide (trust, AlignEval, Nurture Boss, synthetic dimensions) | https://hamel.dev/blog/posts/field-guide/ |
| Evals FAQ hub (code vs judge, sample sizes, cadence, CI) | https://hamel.dev/blog/posts/evals-faq/ |
| Same model for task and judge? | https://hamel.dev/blog/posts/evals-faq/can-i-use-the-same-model-for-both-the-main-task-and-evaluation.html |
| Nova Escola / Lucas Machado — production evals, IAA, daily 2% | https://hamel.dev/notes/llm/ai-product-engineering/evals-production.html |

---

## Papers (legal PDFs / anthology)

| Topic | URL |
|-------|-----|
| **G-Eval** — Liu et al., EMNLP 2023; CoT + form-fill; Spearman 0.514; LLM-text bias | https://aclanthology.org/2023.emnlp-main.153/ |
| Same — DOI | https://doi.org/10.18653/v1/2023.emnlp-main.153 |
| Who Validates the Validators? (UIST 2024) — EvalGen, **criteria drift** | https://arxiv.org/abs/2404.12272 |
| Same paper PDF (Berkeley) | https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf |

---

## YouTube

| Topic | URL |
|-------|-----|
| Why AI evals are the hottest new skill — Hamel Husain & Shreya Shankar (Lenny’s Podcast); code vs LLM evals, error-analysis-first | https://www.youtube.com/watch?v=BsWxPI9UM4c |
| How To Approach Your AI Evals — Hamel; LLM-as-judge as **classifier**; measure vs humans | https://www.youtube.com/watch?v=DZxaPNYi_k0 |
| How to Automate AI Evals (Correctly) — Shreya (analyze → measure → improve) | https://www.youtube.com/watch?v=tqUDjc1HzO4 |

---

## Public talk write-ups (not course PDFs)

| Topic | URL |
|-------|-----|
| Aakash Gupta — masterclass notes (TPR/TNR trap, CI pattern) | https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/ |
| Alternate path | https://www.aakashg.com/ai-evals-masterclass-with-hamel-shreya/ |
| Lenny’s Newsletter — episode notes | https://www.lennysnewsletter.com/p/why-ai-evals-are-the-hottest-new-skill |

---

## Langfuse

| Topic | URL |
|-------|-----|
| Observability overview (tracing vs observability, async SDK, dashboards, alerts) | https://langfuse.com/docs/observability/overview |
| Markdown twin | https://langfuse.com/docs/observability/overview.md |
| SDK / generations / OTEL mapping / `should_export_span` | https://langfuse.com/docs/observability/sdk/overview |
| LLM-as-a-Judge (observation-level, cost $0.01–0.10, debug traces, v4 deprecation of trace-level) | https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge |
| Evals blog (code vs judge vs human, offline/online, sampling) | https://langfuse.com/blog/2025-11-12-evals |
| Error analysis cookbook (fix / judge / monitor) | https://langfuse.com/guides/cookbook/error-analysis-llm-applications |
| RAG faithfulness (claim-level judge, 5–10% sample, context on observation, guardrail vs monitor) | https://langfuse.com/resources/engineering/rag-faithfulness-evaluation |
| Product home | https://langfuse.com/ |

---

## Arize Phoenix / OpenInference

| Topic | URL |
|-------|-----|
| Phoenix LLM traces (latency, tokens, exceptions, retrieved docs, embeddings) | https://arize.com/docs/phoenix/tracing/llm-traces |
| OpenInference best practices (hybrid instrumentation, span kinds) | https://arize.com/docs/phoenix/cookbook/tracing/openinference-best-practices |
| OpenInference specification | https://arize-ai.github.io/openinference/spec/ |
| Semantic conventions | https://arize-ai.github.io/openinference/spec/semantic_conventions.html |
| Drift discussion (accuracy stable, behavior shifts) | https://github.com/Arize-ai/phoenix/discussions/10442 |

---

## OpenAI (public)

| Topic | URL |
|-------|-----|
| Evaluation best practices (CE, human agreement, anti-patterns, G-Eval mentioned in an example) | https://developers.openai.com/api/docs/guides/evaluation-best-practices |
| Working with evals API (`string_check` graders, `testing_criteria`; **platform deprecation** 2026-10-31 / 2026-11-30) | https://developers.openai.com/api/docs/guides/evals |
| Getting started with OpenAI evals cookbook | https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals |
| openai/evals GitHub | https://github.com/openai/evals |

---

## Anthropic (public)

| Topic | URL |
|-------|-----|
| Planning to production — rule-based + model-based + targeted human grading | https://www-cdn.anthropic.com/2db91550aa050eae0f205b04c908cd32ec1dab4b.pdf |

---

## Mapping: source → Week 17 file

| File | Primary sources |
|------|-----------------|
| [00-week-overview.md](00-week-overview.md) | Hamel llm-judge; G-Eval; Langfuse observability + judge; Phoenix traces; YouTube BsWxPI9UM4c + DZxaPNYi_k0 |
| [01-llm-as-judge-design.md](01-llm-as-judge-design.md) | hamel.dev/llm-judge; G-Eval ACL; Langfuse judge + faithfulness; OpenAI cookbook; same-model FAQ |
| [02-judge-alignment-calibration.md](02-judge-alignment-calibration.md) | llm-judge TPR/TNR; FAQ splits; Field Guide AlignEval; Nova Escola; arXiv 2404.12272; OpenAI best practices; Anthropic PDF |
| [03-code-based-vs-model-based-evals.md](03-code-based-vs-model-based-evals.md) | FAQ; Lenny YouTube; Langfuse evals blog + cookbook; OpenAI evals API + github.com/openai/evals |
| [04-observability-platforms.md](04-observability-platforms.md) | Langfuse observability + SDK; Phoenix traces; OpenInference spec + best practices |
| [05-production-monitoring-dashboards.md](05-production-monitoring-dashboards.md) | Langfuse dashboards/alerts/faithfulness sampling; Phoenix; discussion 10442; Nova Escola 2%; Field Guide |

---

## Explicitly out of scope (Week 18+)

Kubernetes, Terraform, GitHub Actions as the **main** deliverable, LiteLLM/RouteLLM cost routing (Week 20), enterprise OIDC (Week 19). Cited only where they explain **why** traces/cost tiles exist. Week 16 error-analysis procedure is **prerequisite**, not duplicated as the focus.
