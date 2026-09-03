# 04 — Component-level vs end-to-end evaluation

> Week 10 concept research (deep). Legal sources only.

---

## Fundamentals

RAG evaluation has **levels**. Mixing them produces numbers that cannot be actioned. Databricks (What is Agent Evaluation): use **component-level tests** (retrieval relevance, parameter formatting) **plus** **end-to-end** success; failing rows get **root-cause** analysis. MLflow tracing makes both possible on the same run. Azure’s docs use the same cut under different names: **process evaluation** (retrieval) vs **system evaluation** (final response). NVIDIA NeMo’s RAG flow literally offers different jobs: retrieval + generation + eval together; **answer evaluation on pre-generated answers**; generation+eval with **cached retrieved docs**.

| Level | What is measured | Example metrics | Primary use |
| --- | --- | --- | --- |
| **Component — retrieval** | Quality of candidate sets independent of final wording | P@k, R@k, MRR, NDCG, context precision/recall, Azure Document Retrieval, NeMo `pytrec_eval` | Tune embeddings, *k*, hybrid, rerankers |
| **Component — generation** | Reader behavior given **fixed** contexts | Faithfulness, format, citation ∈ C, completeness on frozen C | Tune prompts, models, decoding; fair A/B of generators |
| **End-to-end (system)** | User-visible outcome of the **full** pipeline | Correctness vs reference, task success, live groundedness, latency/cost | Release gates, product KPIs |
| **Trace / agent-level** | Multi-step tool/retrieve paths | Databricks/MLflow span scorers, tool-call correctness, trajectory | Debug agents (Phase 3); still relevant if RAG is a tool |

**Isolation techniques:**

- **Freeze retrieval:** store packed `ids[]` / `packed_text_hash` / NeMo cached retriever outputs / MLflow spans. Iterate the generator **without** re-retrieving.  
- **Freeze generation:** swap retrievers (Week 7–8 ablations) while keeping the **same** judge harness and gold answers.  
- **NeMo (docs):** (1) Retrieval + Answer Generation + Answer Evaluation (live pipeline, BEIR or custom); (2) Answer Evaluation on **pre-generated** answers; (3) cached retriever outputs + generate + eval. Older target schema named this `cached_outputs` (later versions prefer **dataset** targets holding those fields).  
- **RAGAS:** component-wise metrics that still **roll up** to system quality if you refuse to average away slices.  
- **Noise sensitivity** (RAGAS / NeMo): generation robustness when retrieval is imperfect — a **bridge** metric between component and E2E.

Barnett: many characteristics are only visible **at runtime** with live users — E2E **online** eval complements offline components. Databricks: **offline** curated datasets vs **online** scoring of production traces; production traces feed the next golden set (file 03).

Hamel: debug **retrieval first** with IR metrics; then generation with error analysis and validated judges. Jason Liu Tier 1 vs Tiers 2–3 is the same isolation.

---

## Alternatives & Tradeoffs

| Strategy | Pros | Cons |
| --- | --- | --- |
| E2E-only | Matches user experience | Confounded; slow attribution; expensive labels |
| Component-only | Fast debugging loops | Can over-optimize a stage that doesn’t move E2E (rerank NDCG↑, users still fail completeness) |
| Frozen-context generation harness | Fair LLM / prompt comparisons | Misses retrieval–generation **interactions** (noise sensitivity, LITM) |
| Online shadow eval | Real traffic | Privacy, judge cost, risk if writes |
| Single “quality” score | Exec-friendly | Hides regressions |
| Public agent benchmarks (OfficeQA, MiniWoB++, HLE) | Architecture sanity | Databricks: **not** production readiness |

**CI vs pre-release vs prod (budget):**

| Cadence | What runs | Spend |
| --- | --- | --- |
| **CI** (every PR) | ID Recall@k + P@k on pinned qrels; schema/citation **code** scorers; faithfulness on **frozen** good contexts (HHEM or small judge) | Cheap, deterministic preferred |
| **Pre-release** | Full golden E2E: correctness + triad + slices | Judge cost accepted |
| **Production** | Sampled reference-free triad + user feedback; periodic human review (Hamel 100+ traces / 2–4 weeks) | Sample rate is the knob |

Release processes that gate **only** on faithfulness can ship a retriever regression (faithful to the wrong C). Gating **only** on answer correctness can hide rising hallucination **masked by parametric knowledge** (correct but ungrounded).

---

## Necessity

Curriculum and production both need **both** levels:

- Component metrics answer **“what to fix.”**  
- E2E metrics answer **“did the fix matter?”**

Week 7 hybrid can raise Recall@40 without moving E2E if packed k still misses gold — **only the two-level table shows that** (overview interview story). Week 8 rerank can raise NDCG and E2E together — then you know ranking was the bottleneck. A prompt change that raises frozen-context faithfulness but **drops** E2E on live retrieval is a noise-sensitivity / LITM issue, not a “prompt win.”

Databricks failure taxonomy (agents): hallucinated tool calls, loops, missing context/retrieval, stale memory — E2E success can hide inefficient or unsafe trajectories. Single-shot RAG still needs the retrieval vs generation split; agents need traces.

---

## Industry Practice

- **CI:** retrieval unit tests on pinned qrels + prompt regression on frozen contexts.  
- **Pre-release:** full golden E2E with reference correctness + triad.  
- **Production:** sampled online triad + thumbs; Review App / human sessions.  
- **Tooling matrix:** LangSmith experiments; `mlflow.genai.evaluate`; Azure AI Evaluation `evaluate()` / Foundry evaluators; RAGAS collections; NeMo Evaluator RAG flow.  
- Databricks: hybrid evaluation; root-cause judges on failing rows; custom `@scorer` for deterministic constraints. Prefer deterministic scorers for citations-present, JSON schema, refusals; LLM judges for fuzzy quality.  
- Azure: Document Retrieval for **parameter sweep** of search; system evaluators for the answer; do not use Groundedness as a search metric.  
- NeMo: `retriever_*` metrics **only** when a retriever pipeline is in the target — if you only pass cached answers, you are not measuring retrieval this run.  
- LangSmith: one `evaluate()` with **four** evaluators so component vs E2E appear on the **same** rows.

**Common:** one E2E % on 12 questions.  
**Strong:** two-level dashboard + frozen harness.  
**FDE:** name which NVIDIA job type they ran; why Azure process ≠ system; why MLflow groundedness must use the RETRIEVER span.

---

## Concrete Scenario

**Change:** swap `gpt-4.1-mini` for a cheaper reader.

| Harness | Result | Interpretation |
| --- | --- | --- |
| E2E-only on live hybrid | Correctness 0.68 → 0.61 | “Worse model” — maybe |
| Frozen C from Week 8 packed gold | Faithfulness 0.84 → 0.70, completeness ↓ | Generator regression (real) |
| Same cheap model, **oracle** gold chunks packed | Correctness back to 0.74 | Model is OK **if** C is clean; live drop is noise sensitivity |
| Retrieval metrics unchanged | Recall@8 = 0.74 both | Don’t retune RRF |

NVIDIA isolation: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html — sections “Retrieval + Answer Generation + Answer Evaluation” vs “Answer Evaluation (Pre-generated Answers).”  
Databricks hybrid + offline/online: https://www.databricks.com/blog/what-is-agent-evaluation  
LangSmith parallel evaluators: https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
YouTube operationalizing the loop: https://www.youtube.com/watch?v=BsWxPI9UM4c  

---

## Open Questions

- How to budget eval spend across component CI vs weekly E2E vs online sampling?  
- When an agent has **multiple** retrieve calls, which span is “the context” for groundedness? (Databricks: defined RETRIEVER span; Azure: tool results.)  
- Can automated root-cause classifiers reliably map E2E fails → Barnett FPs (Week 9)?  
- Should latency/cost be first-class **E2E** metrics in the same table as correctness (Databricks efficiency metrics: cost/run, latency, iteration count, tokens)? **Yes for FDE interviews.**  
- Deprecation: NeMo `cached_outputs` vs dataset targets — pin the version you cite.

---

## Sources

- RAGAS metrics (component-wise): https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
- LangSmith RAG tutorial: https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- Databricks Agent Evaluation: https://www.databricks.com/blog/what-is-agent-evaluation  
- Databricks Agent Eval → MLflow 3: https://docs.databricks.com/aws/en/mlflow3/genai/agent-eval-migration  
- NVIDIA NeMo RAG flow: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
- NVIDIA RAG pipeline targets / cached outputs (25.9): https://docs.nvidia.com/nemo/microservices/25.9.0/evaluate/evaluation-targets/rag-pipeline-targets.html  
- Azure RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- Hamel RAG FAQ: https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
- Jason Liu: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- MLflow GenAI: https://mlflow.org/docs/latest/genai/eval-monitor/  
