# 99 — Week 9 master source map

> Consolidated index of official docs, vendor blogs, papers, talks. Legal sources only.

**Jason Liu check (this pass):** `https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/` still served public HTML (fetched 2026-09-03). If that URL 404s later, Hamel’s FAQ still restates the six Q–C–A relationships and Tiers 1–3.

---

## Barnett — Seven Failure Points

| Topic | URL |
|-------|-----|
| arXiv abs | https://arxiv.org/abs/2401.05856 |
| HTML full text v1 | https://arxiv.org/html/2401.05856v1 |
| PDF | https://arxiv.org/pdf/2401.05856 |
| CAIN 2024 DOI | https://doi.org/10.1145/3644815.3644945 |
| BioASQ FP examples / scripts (figshare) | https://figshare.com/s/fbf7805b5f20d7f7e356 |

---

## Lost in the Middle / long context × RAG

| Topic | URL |
|-------|-----|
| Liu et al. **Lost in the Middle** arXiv:2307.03172 | https://arxiv.org/abs/2307.03172 · https://arxiv.org/pdf/2307.03172 |
| TACL 2024 anthology | https://aclanthology.org/2024.tacl-1.9/ |
| DOI | https://doi.org/10.1162/tacl_a_00638 |
| Databricks **Long Context RAG Performance of LLMs** (blog) | https://www.databricks.com/blog/long-context-rag-performance-llms |
| Leng et al. arXiv:2411.03538 | https://arxiv.org/abs/2411.03538 |
| Xu et al. LC vs RAG arXiv:2501.01880 | https://arxiv.org/abs/2501.01880 |
| Chip Huyen (public): context length ≠ use; cites LITM | https://huyenchip.com/2023/08/16/llm-research-open-challenges.html |
| Chip Huyen (public): rank vs inclusion / LITM | https://huyenchip.com/2024/07/25/genai-platform.html |
| Pinecone rerankers (LITM motivation; Week 8 pair) | https://www.pinecone.io/learn/series/rag/rerankers/ |
| LlamaIndex `LongContextReorder` | https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/ |

---

## Jason Liu — 6 RAG evals (Q–C–A)

| Topic | URL |
|-------|-----|
| **There Are Only 6 RAG Evals** (jxnl.co, 2025-05-19) | https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/ |
| TWIML: Why Your RAG System Is Broken (Jason Liu) | https://twimlai.com/podcast/twimlai/why-your-rag-system-is-broken-and-how-to-fix-it |

---

## Hamel Husain — evals / RAG

| Topic | URL |
|-------|-----|
| AI Evals FAQ (index; includes RAG + “Is RAG dead?”) | https://hamel.dev/blog/posts/evals-faq/index.html |
| Q: How should I approach evaluating my RAG system? | https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html |
| LLM-as-judge (targeted citation evals) | https://hamelhusain.substack.com/p/llm-judge |

---

## Azure / NVIDIA / Databricks / RAGAS evaluators

| Topic | URL |
|-------|-----|
| Azure AI Foundry **RAG evaluators** (process vs system; NDCG/fidelity/holes; Groundedness vs Completeness vs Pro) | https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators |
| Azure `GroundednessEvaluator` Python API | https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation.groundednessevaluator |
| NVIDIA NeMo **RAG evaluation flow** (`pytrec_eval` recall/ndcg vs `ragas` faithfulness/relevancy) | https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html |
| NVIDIA RAG metrics (context_recall, faithfulness, response_groundedness, …) | https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html |
| Databricks `RetrievalGroundedness` judge | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_grounded |
| RAGAS Faithfulness | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ |
| RAGAS Context Precision (Week 10 pairing) | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/ |

---

## Grounding / citations / drift (practitioner + vendor)

| Topic | URL |
|-------|-----|
| Grounded RAG pattern (`retrievedReferences`) | https://aiarch.dev/patterns/grounded-rag |
| Attribution & citation overview | https://mbrenndoerfer.com/writing/attribution-and-citation |
| Citation drift / content-addressed IDs | https://medium.com/@npavfan2facts/rag-citations-backfire-when-chunks-keep-changing-850f4336d882 |

---

## YouTube / talks (public)

| Topic | URL |
|-------|-----|
| Hamel Husain — How To Approach Your AI Evals | https://www.youtube.com/watch?v=DZxaPNYi_k0 |
| Hamel & Shreya — How to Automate AI Evals (Correctly) | https://www.youtube.com/watch?v=tqUDjc1HzO4 |
| Hamel & Shreya — Why AI evals are the hottest new skill (Lenny’s Podcast) | https://www.youtube.com/watch?v=BsWxPI9UM4c |
| Lost in the Middle explainer (U-curve, RAG stuffing) | https://www.youtube.com/watch?v=jt_PAZ5zLq4 |

---

## Secondary / related (do not substitute for the core papers)

| Topic | URL |
|-------|-----|
| Lewis et al. RAG (NeurIPS 2020) | cited inside Barnett related work |
| OpenAI Evals (BioASQ scoring in Barnett) | https://github.com/openai/evals |
| BioASQ-QA corpus (Scientific Data) | Krithara et al. 2023 — cited in Barnett |

---

## Coverage matrix (syllabus concepts → primary URLs)

| Concept file | Must-cite |
|--------------|-----------|
| 00 overview | Barnett 2401.05856 + fault-injection log schema + Azure/NVIDIA split + Jason Liu + Hamel |
| 01 three modes | Barnett FP1–FP7 map + Jason Liu 6 evals (still public) + Hamel RAG FAQ + Azure/NVIDIA |
| 02 citation/grounding | RAGAS Faithfulness + Azure Groundedness/Pro + Databricks RetrievalGroundedness + Bedrock-style references |
| 03 drift/reindex | Barnett embedding⇒full reindex + Databricks LC RAG (packing interaction) + content-addressed IDs |
| 04 RAG vs LC | Liu 2307.03172 + Databricks 2411.03538 + Xu 2501.01880 + Huyen public LITM |

**Not used:** pirate book/PDF sites; unauthorized copyrighted book extracts; Chip Huyen *AI Engineering* book text (public blog only).

**Out of scope this week:** Week 10 metric cookbook (formulas, golden-set construction as the *primary* deliverable). This week **classifies**; Week 10 **scores**.
