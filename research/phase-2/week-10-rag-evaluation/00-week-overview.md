# 00 — Week overview & syllabus mapping

> Week 10 — RAG evaluation  
> Research notes (raw).

---

## Fundamentals

Week 10 is the **measurement** week of Phase 2 RAG. Weeks 6–8 built chunks, hybrid candidates, and a reranked packed window. Week 9 **named** failures (recall / ranking / generation-grounding; Barnett FP1–7; Jason Liu Q–C–A). This week **quantifies** those names so a change to embeddings, *k*, reranker, or prompt has a before/after that can be repeated in CI and told in an interview.

The syllabus spine is a **RAGAS-style harness**, not a new retriever:

| Layer | Question | Default instruments |
| --- | --- | --- |
| **Retrieval (component)** | Did the right chunks enter the packed window, in a useful order? | P@k, R@k, MRR, NDCG@k; RAGAS Context Precision / Recall; Azure Document Retrieval; NeMo `pytrec_eval` |
| **Generation (component)** | Given those chunks, did the reader stay faithful and on-question? | RAGAS Faithfulness + Answer Relevancy; Azure Groundedness / Relevance / Completeness; Databricks `RetrievalGroundedness` |
| **System (E2E)** | Did the user-visible answer match business truth? | Reference correctness (LangSmith); task success; latency/cost |
| **Dataset** | Can we re-run this next week on the same world? | Versioned golden set + corpus hash + pipeline version |

**RAGAS** (docs.ragas.io) is the open vocabulary: Faithfulness = supported claims / claims; Answer Relevancy = mean cosine of reverse-engineered questions vs the user input; Context Precision = rank-aware mean of Precision@k at relevant ranks. NVIDIA NeMo’s RAG flow **embeds the same split**: `retriever_recall_k` / `retriever_ndcg_cut_k` via **pytrec_eval**, and `rag_faithfulness` / `rag_answer_relevancy` via **ragas**. Azure Foundry splits **process** (Document Retrieval, Retrieval LLM-judge) from **system** (Groundedness, Relevance, Response Completeness). LangSmith’s RAG tutorial runs **correctness, groundedness, relevance, retrieval_relevance** as parallel evaluators on one dataset.

Hamel Husain & Shreya Shankar (hamel.dev evals FAQ, updated through 2026): retrieval is a **search problem** — use IR metrics. Generation uses **error analysis → human labels → targeted judges → TPR/TNR**. Jason Liu (*There Are Only 6 RAG Evals*, 2025-05-19) is the relationship graph (Q, C, A); Hamel’s RAG FAQ maps it onto ops: **Tier 1 IR first**.

Barnett et al. (arXiv:2401.05856): **validation is only feasible in operation** because labelled Q/A often do not exist at index time. Week 10’s golden set is therefore an **engineering artifact you build**, not a download. Week 9’s debugging log is the labelling bootstrap.

**This week’s artifact is a numbered before/after table**, joined on the same queries and `pipeline_version`s as Weeks 7–9 — not a screenshot of a vendor dashboard.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| **RAGAS-style triad + IR@k** (syllabus default) | Debuggable components; portable formulas | Judge cost; need qrels or ID lists |
| E2E accuracy / “thumbs up” only | One slide | Confounds FP2 vs FP4; cannot tune hybrid vs prompt |
| Vendor default fluency/coherence | Easy UI | Hamel: platform defaults ≠ product failures |
| BLEU/ROUGE vs reference answers | Cheap, deterministic | Poor for paraphrase; not groundedness |
| LLM-judge everything (no IR) | Scales without qrels | Rank regressions invisible; uncalibrated TPR/TNR |
| IR only (no generation judges) | Fast CI on retrievers | Ships faithful-wrong and off-topic answers |
| Single aggregated “RAG score” | Exec-friendly | Hides opposing movements (recall↑ faithfulness↓) |

| Harness choice | Pros | Cons |
|----------------|------|------|
| RAGAS `evaluate` / collections API | Canonical triad formulas; open | You still own dataset versioning and judge calibration |
| LangSmith experiment | Dataset + traces + parallel evaluators | Tutorial judges are starting prompts, not validated |
| Azure AI Evaluation | Process vs system; NDCG/fidelity/holes | Azure-centric; Groundedness 1–5 ≠ RAGAS 0–1 |
| NeMo RAG flow | BEIR + pytrec_eval + ragas in one job; cached answer eval | Infra; metric name prefixes |
| MLflow / Databricks Agent Evaluation | Trace-tied `RetrievalGroundedness`; Review App | Judge lives on RETRIEVER span, not a later re-fetch |

Do not start Week 10 by regenerating the index. If gold is absent from `fetch_k`, that is **Recall@k = 0** — faithfulness of the answer is not a retriever score.

---

## Necessity

Concrete failure modes if Week 10 is skipped:

- Week 9 labels never become **release gates**. The next embedding upgrade is argued in Slack.  
- Teams “improve RAGAS faithfulness” while **Recall@k is 0** (Barnett FP1/FP2): the model is faithful to the wrong chunks.  
- Raising packed *k* after Week 8 looks better on recall and worse on context precision / LITM — **without both metrics you pick the wrong k**.  
- Interview answer collapses to “we used RAGAS” with **no denominator, no k, no slice**. Hiring FDEs ask for Recall@k at production k vs fetch_k.  
- Barnett: offline eval needs labels that “don’t exist” — without a golden-set practice, you cannot detect corpus drift (Week 9) because there is nothing pinned.  
- Judge drift: off-the-shelf LangSmith/RAGAS prompts disagree with domain experts; CI gates on a metric that does not match the product.

Without this week, Weeks 16–17 (error-analysis flywheel, LLM-as-judge) have no RAG-specific metric cookbook.

---

## Industry Practice

- **Common (demo AI):** one LangSmith run with a single “quality” LLM-as-judge; no qrels; *k* unspecified; no corpus hash.  
- **Strong:** TREC-style qrels or gold `chunk_id`s; metrics at **production packed k** and **fetch_k**; triad + correctness; unanswerable slice; hybrid/rerank **ablation table**; binary pass/fail for triage (Databricks style) plus continuous scores for tuning.  
- **FDE bar:** tell a **quantified before/after** (below); name which metric moved for which owner; cite RAGAS formulas, Azure process vs system, NeMo pytrec vs ragas; state judge–human agreement or that judges are **not** yet gating.

Hamel heuristic: 60–80% of eval effort is **looking at traces**, not wiring dashboards. Wire the harness so error analysis is cheap (row-level rationales), not so you can skip it.

---

## Concrete Scenario

**Product:** same internal runbook / FAQ RAG as Weeks 6–9. Pin **N ≈ 40–80** queries: semantic FAQ, lexical-precision (SKU / error code / version), multi-hop, **unanswerable**, ACL-denied. Gold = supporting `chunk_id`s (and `expected_facts` where the answer is a list).

### Harness (minimum)

```text
for each row in golden.jsonl  # pinned: corpus_hash, pipeline_version
  run retriever @ fetch_k, rerank, pack @ k_prod
  log retrieval_id, ids[], ranks, packed_text_hash
  generate answer
  score:
    ID Recall@k_prod, Recall@fetch_k, P@k, MRR, NDCG@k   # component retrieval
    RAGAS faithfulness, answer_relevancy, context_precision
    reference correctness (if reference exists)
    refusal_ok on unanswerable slice
```

LangSmith tutorial equivalent: dataset of questions + expected answers → `evaluate(..., evaluators=[correctness, groundedness, relevance, retrieval_relevance])`.  
URL: https://docs.langchain.com/langsmith/evaluate-rag-tutorial

### Quantified interview story (before / after Weeks 7–9)

Fill the **your numbers** column from the actual Week 7–9 logs. The **illustrative** column is a teaching shape (order of magnitude and **which way** metrics move), not a published benchmark. Never cite the illustrative column as a paper result.

| Stage | What changed | Retrieval (illustrative) | Generation / E2E (illustrative) | Owner of the delta |
| --- | --- | --- | --- | --- |
| **W6 baseline** | Recursive chunks; dense cosine `k=5`; no BM25; no candidate log | Recall@5 **~0.41** overall; lexical slice Recall@5 **~0.18**; MRR **~0.33** | E2E correctness **~0.48**; faithfulness **~0.71** (faithful to junk); answer relevancy **~0.80** | — |
| **After W7** | Dense+BM25 → RRF `fetch_k≈40`; identifier analyzer; candidate logs | Recall@40 **~0.78** / lexical Recall@40 **~0.71**; Recall@5 still **~0.50** (gold in pool, not packed) | Correctness **~0.55** (more evidence, still noisy window); faithfulness **may dip** (more FP4 noise) | Search: recall; packing still Week 8 |
| **After W8** | CE rerank → pack 8; LITM-aware order; one query transform on hard slice | NDCG@8 **~0.62 → ~0.79**; MRR **~0.52 → ~0.70**; Recall@8 **~0.74** | Correctness **~0.68**; context precision **up**; faithfulness **up** if noise dropped | Ranking / packing |
| **After W9** | Fault matrix; refuse on FP1; citation snapshot; don’t punish faithfulness when Recall@k=0 | Same IR on answerable slice; **new** slice metrics: refusal precision on unanswerable | Correctness on answerable **~0.72**; unanswerable “I don’t know” **pass rate ~0.90**; groundedness **not** averaged with FP1 | Taxonomy + policy |
| **W10 harness** | Pin golden set; report **disaggregated** + CI; judge calibration n≥30 | Publish Recall@k at **k_prod and fetch_k**; holes/fidelity if using Azure labels | Triad + correctness; TPR/TNR of faithfulness judge vs human | Eval engineering |

**How to say it in an interview (STAR-shaped):**

> “On 60 labelled queries pinned to corpus `abc123`, cosine-only `k=5` had Recall@5 = 0.41 (0.18 on SKU/error-code). Hybrid RRF at 40 lifted Recall@40 to 0.78 but packed-window Recall@5 only to 0.50 — so generation was still starved. Cross-encoder packing to 8 moved NDCG@8 from 0.62 to 0.79 and E2E correctness from 0.55 to 0.68. Faithfulness stayed high on a retrieval miss until we **stopped averaging** FP1 rows into the generator score and added an unanswerable slice (refusal pass 0.90). We gate CI on Recall@8 + faithfulness on **frozen good contexts**, and gate release on E2E correctness + triad.”

That paragraph is the Week 10 deliverable. Swap in **your** logged numbers.

Public bar: RAGAS faithfulness / answer relevancy / context precision docs; LangSmith RAG eval tutorial; Azure RAG evaluators; NeMo RAG flow; Hamel RAG FAQ; Jason Liu six evals.

URL: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
Companions: https://docs.langchain.com/langsmith/evaluate-rag-tutorial · https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators · https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html · https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html · https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/

---

## Open Questions

- How large a golden set is enough to **gate** a retriever change at startup (n=40 vs n=200) vs to **estimate** a rate?  
- Should interview numbers be reported with bootstrap CIs, or is a point estimate + slice table enough?  
- When Weeks 7–9 used different *k*, which *k* is the honest “before”? (Answer: always name *k*; never compare Recall@5 to Recall@40 as if they were the same metric.)  
- How to credit **partial** multi-chunk gold in Recall@k (set recall vs all-or-nothing)?  
- Online vs offline mix: what fraction of weekly eval spend is production-sampled triad vs pinned golden E2E?

---

## Week 10 metric ↔ Week 9 failure map

| Failure mode (Week 9) | Component metric | E2E metric |
| --- | --- | --- |
| Recall failure (FP1/FP2 miss) | Recall@k, Context Recall, Azure Fidelity, Retrieval Sufficiency | Correctness ↓; Faithfulness **do not use** as retriever debug |
| Ranking / assembly (FP2 near-miss, FP3, LITM) | NDCG, MRR, Context Precision, P@k | Correctness ↓; noise sensitivity / faithfulness may move |
| Generation-grounding (FP4–7) | Faithfulness on **frozen good C**; completeness; citation ∈ retrieved IDs | Faithfulness ↓, Completeness ↓, format assertions fail |
| Corpus drift | Recall@k on time-sensitive slice; `content_hash` mismatch | Correctness vs world ↓ while Faithfulness stays high |

---

## Sources

- RAGAS Faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/  
- RAGAS Answer Relevancy: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/  
- RAGAS Context Precision: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/  
- RAGAS Context Recall: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/  
- LangSmith Evaluate a RAG application: https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- Azure RAG evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- NVIDIA NeMo RAG evaluation flow: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
- NVIDIA RAGAS-family metrics: https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html  
- Databricks What is Agent Evaluation: https://www.databricks.com/blog/what-is-agent-evaluation  
- Hamel RAG FAQ: https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
- Hamel synthetic data: https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html  
- Jason Liu six evals: https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Barnett et al.: https://arxiv.org/abs/2401.05856  
- YouTube: Hamel & Shreya “Why AI evals are the hottest new skill…” https://www.youtube.com/watch?v=BsWxPI9UM4c  
- YouTube: Hamel “How To Approach Your AI Evals” https://www.youtube.com/watch?v=DZxaPNYi_k0  
