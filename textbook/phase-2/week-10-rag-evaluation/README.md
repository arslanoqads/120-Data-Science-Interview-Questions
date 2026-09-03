# Week 10 Textbook Chapter — RAG evaluation

> **Status:** COMPLETE  
> **Source:** `research/phase-2/week-10-rag-evaluation/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Retrieval metrics (P@k, R@k, MRR, NDCG — and Azure/NeMo cousins)
- [x] Generation metrics / RAGAS triad (faithfulness, answer relevancy, context precision)
- [x] Golden set from usage (production + structured synthetic bootstrap)
- [x] Component-level vs end-to-end evaluation

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

On the **same** Week 7–9 logged stack (do **not** swap retrievers this week): pin a golden set to `corpus_hash` + `pipeline_version`; stand up a RAGAS-style harness (or LangSmith / Azure / NeMo / MLflow — one primary); score retrieval at production packed *k* and at `fetch_k`; score generation (faithfulness / answer relevancy / context precision + reference correctness); produce a **before/after table** vs Weeks 7–9 ablations. That table is the interview artifact.
