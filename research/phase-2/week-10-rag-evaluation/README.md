# Week 10 Research Corpus — RAG evaluation

> Phase 2 — RAG Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only.

This directory is the Week 10 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | RAGAS-style harness; before/after Weeks 7–9; quantified interview story |
| 01 | [01-retrieval-metrics.md](01-retrieval-metrics.md) | P@k, R@k, MRR, NDCG (and Azure/NeMo cousins) |
| 02 | [02-generation-metrics-ragas.md](02-generation-metrics-ragas.md) | Groundedness, answer relevance, context precision (RAG triad) |
| 03 | [03-golden-set-from-usage.md](03-golden-set-from-usage.md) | Golden set from production + structured synthetic bootstrap |
| 04 | [04-component-vs-e2e-eval.md](04-component-vs-e2e-eval.md) | Component isolation vs end-to-end gates |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 10)

- [x] All syllabus Week 10 concepts covered with 7 required fields  
- [x] **Retrieval metrics:** Precision@k, Recall@k, MRR, NDCG@k (formulas + RAG packing *k*)  
- [x] **Azure Document Retrieval:** NDCG, XDCG, Fidelity, Max Relevance, Holes  
- [x] **NVIDIA NeMo:** `pytrec_eval` `retriever_recall_k` / `retriever_ndcg_cut_k` vs RAGAS generation metrics  
- [x] **RAGAS triad:** Faithfulness, Answer/Response Relevancy, Context Precision (+ Context Recall, Utilization, ID-based)  
- [x] **LangSmith RAG tutorial:** correctness, groundedness, relevance, retrieval_relevance in one experiment  
- [x] **Hamel / Shreya:** IR metrics for retrieval; error analysis → validated judges; dimensions → tuples → queries  
- [x] **Jason Liu** six Q–C–A evals (Tier 1 IR / Tier 2 triad / Tier 3 extras) still public (`jxnl.co`)  
- [x] **Databricks Mosaic / MLflow:** component + E2E, `RetrievalGroundedness`, golden datasets, root-cause  
- [x] Golden-set construction from usage + unanswerable / ACL slices (Barnett FP1)  
- [x] Component vs E2E (frozen-context harness; NeMo cached / dataset targets; CI vs pre-release vs online)  
- [x] YouTube eval talks cited (Hamel & Shreya; Hamel “How To Approach Your AI Evals”)  
- [x] Quantified **before/after Weeks 7–9** interview story in overview  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 10)

On the **same** Week 7–9 logged stack (do **not** swap retrievers this week):

1. Pin a **golden set** (queries + gold `chunk_id`s / `expected_facts` + unanswerable slice) to `corpus_hash` + `pipeline_version`.  
2. Stand up a **RAGAS-style harness** (or LangSmith / Azure `evaluate()` / NeMo RAG flow / MLflow scorers — one primary, others as mapping tables).  
3. Score **retrieval** at production packed *k* and at `fetch_k` (Recall@k, P@k, MRR, NDCG).  
4. Score **generation** (faithfulness / answer relevancy / context precision; plus reference correctness on the golden slice).  
5. Produce a **before/after table** vs Weeks 7–9 ablations (cosine-only → hybrid → +rerank → taxonomy-informed packing). That table is the interview artifact.

Do not skip this week for “we’ll just look at chat.” E2E accuracy **confounds** recall, rank, and grounding. Hamel: **debug retrieval with IR metrics first**, then generation with **judges validated against humans**.

## Default path (synthesis)

1. Join Week 9 debugging log on `retrieval_id`. Convert labels into **stratified slices** (recall / rank / ground / unanswerable / lexical-precision).  
2. Prefer **ID-based** retrieval metrics when qrels exist; use LLM retrieval-relevance only when labels are missing — then calibrate.  
3. Freeze packed contexts for generator A/B; freeze generator for retriever A/B.  
4. Report metrics **disaggregated** (never a single “quality” number as the deliverable).  
5. Interview story = **numbers + owner + next lever**, not “we added RAGAS.”
