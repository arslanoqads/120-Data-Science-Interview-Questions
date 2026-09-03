# Week 8 Textbook Chapter — Reranking and query understanding

> **Compile:** COMPLETE  
> **Edit:** COMPLETE  
> **Source:** `research/phase-2/week-08-reranking-query-understanding/`  
> **Chapter:** [chapter.md](chapter.md)

## Editorial checklist

- [x] Continuity reviewed (Week 7 hybrid dense+BM25, RRF, candidate logging, vector DB tradeoffs)  
- [x] Prerequisites Recap added  
- [x] Framing standardized to **What this week builds**  
- [x] Looking ahead → Week 9  
- [x] Concept structure preserved (6 fields)  
- [x] Language pass for coherence and simplicity  

## Concepts covered

- [x] Two-stage retrieval (retrieve 50–100 → rerank → top 5–10)
- [x] Cross-encoder rerankers (Cohere Rerank, BGE-reranker)
- [x] Lost in the middle (Liu et al.) and why reranking mitigates
- [x] Query transformation (HyDE, decomposition, expansion — one transform, measured)

## Syllabus build

Two-stage retrieval on the Week 7 hybrid candidate API: stage-1 returns 50–100 candidates; cross-encoder rerank (Cohere or BGE) keeps top 5–10 for generation; add exactly one routed query transform (HyDE or multi-query expansion or decomposition); measure delta vs the Week 7 baseline (recall@k, nDCG/MRR, answer quality, p95 latency).
