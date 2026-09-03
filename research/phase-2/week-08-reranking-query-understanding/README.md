# Week 8 Research Corpus — Reranking & query understanding

> Phase 2 — RAG Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; Chip Huyen via public blog/talks only (no pirated book).

This directory is the Week 8 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: retrieve 50–100 → rerank → top 5–10; one query transform; measure delta |
| 01 | [01-two-stage-retrieval.md](01-two-stage-retrieval.md) | Cheap high-recall stage-1 then expensive high-precision stage-2 |
| 02 | [02-cross-encoder-rerankers.md](02-cross-encoder-rerankers.md) | Cohere Rerank, BGE-reranker, latency/quality, LangChain/LlamaIndex wiring |
| 03 | [03-lost-in-the-middle.md](03-lost-in-the-middle.md) | Liu et al. arXiv 2307.03172; why rerank (and edge-ordering) mitigates |
| 04 | [04-query-transformation.md](04-query-transformation.md) | HyDE (Gao et al.), query decomposition, query expansion — **one** transform, measured |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog / YouTube index |

## Completeness checklist (Week 8)

- [x] All syllabus Week 8 concepts covered with 7 required fields  
- [x] Two-stage retrieval: retrieve **50–100** → rerank → pack **top 5–10** for the generator  
- [x] Cross-encoder rerankers: **Cohere Rerank** (`/v2/rerank`) + **BGE-reranker** (`BAAI/bge-reranker-v2-m3`) latency/quality  
- [x] Lost in the Middle: Liu et al. **arXiv:2307.03172** / TACL; why rerank shrinks and reorders context  
- [x] Query transformation: **HyDE** Gao et al. **arXiv:2212.10496**; decomposition; expansion; syllabus rule = **one** transform + measure delta  
- [x] LangChain `ContextualCompressionRetriever` / `CohereRerank` / `CrossEncoderReranker` cited  
- [x] LlamaIndex `CohereRerank`, `SentenceTransformerRerank`, `LongContextReorder`, `SubQuestionQueryEngine` cited  
- [x] Sentence-Transformers Retrieve & Re-Rank (~100 then CrossEncoder) cited  
- [x] Pinecone two-stage / rerankers chapter + hosted `bge-reranker-v2-m3` docs cited  
- [x] Chip Huyen **public blog only** (`llm-research-open-challenges`, `genai-platform`) — no book scrape  
- [x] YouTube talks cited (query transforms, cross-encoder/Cohere rerank)  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 8)

On the Week 7 hybrid candidate API, ship **two-stage retrieval**:

1. Stage-1: hybrid + RRF (or equivalent) returning **50–100** candidates (`fetch_k`).  
2. Stage-2: cross-encoder rerank (Cohere **or** self-hosted BGE) keeping **top 5–10** for generation.  
3. Add **exactly one** query transform (HyDE *or* multi-query expansion *or* decomposition) on a **routed** slice — not on every request.  
4. **Measure delta** against the Week 7 baseline: recall@k of stage-1, nDCG/MRR after rerank, answer accuracy / groundedness after packing 5–10, plus p95 latency of retrieve vs rerank vs generate.

Do not skip this week for “long-context models can eat top-20 cosine hits.” Liu et al. show more retrieved docs eventually stop helping; Pinecone restates the same as maximize retriever recall then minimize what the LLM sees.

## Default path (synthesis)

1. Keep Week 7 candidate logs; **append** `rerank.ids[]`, `rerank.scores[]`, `rerank.model`, `top_n`.  
2. Tune `fetch_k` on **stage-1 recall@k** until gold is usually in the 50–100 pool; only then tune the reranker.  
3. Pack **few** docs; put the highest-rerank hit first (optionally first+last via `LongContextReorder`).  
4. Enable one query transform only where eval slices show vocabulary mismatch or multi-hop failure.  
5. Compare Cohere vs BGE on **your** corpus; BEIR/MTEB are directional.  
