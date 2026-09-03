# 99 — Week 10 master source map

> Consolidated index of official docs, vendor blogs, papers, talks. Legal sources only.

**Jason Liu check (this pass):** `https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/` still the public URL used in Week 9 (fetched/cited 2026-09-03). If that URL 404s later, Hamel’s RAG FAQ restates Tier 1 IR + Q–C–A Tiers 2–3.

---

## RAGAS (formulas and APIs)

| Topic | URL |
|-------|-----|
| Faithfulness (claims / supported claims; HHEM option) | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ |
| Answer / Response Relevancy (reverse questions + cosine) | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/ |
| Context Precision (rank-aware P@k; Utilization; ID-based) | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/ |
| Context Recall (reference claims; Non-LLM; ID-based) | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/ |
| Available metrics index | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/ |
| Test data generation | https://docs.ragas.io/en/stable/concepts/test_data_generation/ |
| RAG evaluation how-to (applications) | https://docs.ragas.io/en/stable/howtos/applications/ |

---

## LangChain / LangSmith

| Topic | URL |
|-------|-----|
| **Evaluate a RAG application** (dataset → run → correctness, groundedness, relevance, retrieval_relevance) | https://docs.langchain.com/langsmith/evaluate-rag-tutorial |
| LangSmith evaluation overview (if tutorial links out) | https://docs.langchain.com/langsmith/evaluation |

---

## Azure AI Foundry — RAG evaluators

| Topic | URL |
|-------|-----|
| RAG evaluators (process vs system; NDCG, XDCG, Fidelity, Max Relevance, Holes; Groundedness vs Completeness vs Pro) | https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators |
| `GroundednessEvaluator` Python API | https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation.groundednessevaluator |

---

## NVIDIA NeMo

| Topic | URL |
|-------|-----|
| RAG evaluation flow (pytrec_eval `retriever_recall_k` / `ndcg_cut_k` + ragas faithfulness/relevancy; pre-generated answers) | https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html |
| RAG evaluation flow (25.12 snapshot) | https://docs.nvidia.com/nemo/microservices/25.12.0/evaluate/flows/rag.html |
| RAGAS-family RAG metrics (context_recall, faithfulness, response_groundedness, noise_sensitivity, …) | https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html |
| Retriever metrics (pytrec_eval catalog) | https://docs.nvidia.com/nemo/microservices/26.3.1/evaluator/metrics/retriever.html |
| RAG pipeline targets / cached retriever or answer outputs (25.9) | https://docs.nvidia.com/nemo/microservices/25.9.0/evaluate/evaluation-targets/rag-pipeline-targets.html |

---

## Databricks Mosaic / MLflow

| Topic | URL |
|-------|-----|
| What is AI Agent Evaluation (component vs E2E, offline vs online, golden datasets, judges) | https://www.databricks.com/blog/what-is-agent-evaluation |
| Building custom LLM judges | https://www.databricks.com/blog/building-custom-llm-judges-ai-agent-accuracy |
| `RetrievalGroundedness` / is_grounded | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_grounded |
| Agent Evaluation → MLflow 3 migration | https://docs.databricks.com/aws/en/mlflow3/genai/agent-eval-migration |
| `databricks-agents` eval API | https://api-docs.databricks.com/python/databricks-agents/latest/databricks_agent_eval.html |
| MLflow GenAI eval & monitor | https://mlflow.org/docs/latest/genai/eval-monitor/ |

---

## Hamel Husain / Shreya Shankar

| Topic | URL |
|-------|-----|
| AI Evals FAQ hub | https://hamel.dev/blog/posts/evals-faq/index.html |
| How should I approach evaluating my RAG system? | https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html |
| Best approach for generating synthetic data (dimensions → tuples → queries) | https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html |
| LLM-as-judge (targeted evals) | https://hamelhusain.substack.com/p/llm-judge |

---

## Jason Liu — 6 RAG evals (Q–C–A)

| Topic | URL |
|-------|-----|
| There Are Only 6 RAG Evals (jxnl.co, 2025-05-19) | https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/ |
| TWIML: Why Your RAG System Is Broken (Jason Liu) | https://twimlai.com/podcast/twimlai/why-your-rag-system-is-broken-and-how-to-fix-it |

---

## Papers (eval implications)

| Topic | URL |
|-------|-----|
| Barnett et al. Seven Failure Points arXiv:2401.05856 | https://arxiv.org/abs/2401.05856 · https://arxiv.org/html/2401.05856v1 |
| Liu et al. Lost in the Middle arXiv:2307.03172 (k / position × metrics) | https://arxiv.org/abs/2307.03172 |

---

## YouTube / talks

| Topic | URL |
|-------|-----|
| Hamel Husain & Shreya Shankar — Why AI evals are the hottest new skill for product builders | https://www.youtube.com/watch?v=BsWxPI9UM4c |
| Hamel Husain — How To Approach Your AI Evals | https://www.youtube.com/watch?v=DZxaPNYi_k0 |

---

## Concept → primary sources

| File | Primary citations |
|------|-------------------|
| 00 overview | RAGAS triad docs; LangSmith tutorial; Azure split; NeMo flow; Hamel RAG FAQ; interview before/after uses Weeks 7–9 logging |
| 01 retrieval metrics | pytrec / NeMo retriever metrics; Azure Document Retrieval; RAGAS context precision/recall; Hamel IR-first |
| 02 generation / RAGAS | Faithfulness, Answer Relevancy, Context Precision pages; Azure Groundedness vs Completeness; LangSmith four evaluators |
| 03 golden set | Hamel synthetic + RAG FAQs; YouTube eval talks; LangSmith datasets; Databricks golden/benchmarks; Barnett scarcity |
| 04 component vs E2E | Databricks hybrid eval; NeMo job types / cached answers; Azure process vs system; Hamel retrieval-then-generation |

---

## Not used (policy)

Pirate book sites, paywalled ebook dumps, or reconstructed copyrighted book chapters. Vendor docs, arXiv, public blogs, and YouTube talks only.
