# Week 7 Research Corpus — Retrieval beyond cosine

> Phase 2 — RAG Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; Chip Huyen via public blog only (no pirated book).

This directory is the Week 7 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: hybrid retrieval + RRF; instrument candidate logging |
| 01 | [01-bi-encoder-vs-cross-encoder.md](01-bi-encoder-vs-cross-encoder.md) | Dual-encoder ANN retrieval vs pair-scoring rerankers |
| 02 | [02-hybrid-search-dense-bm25.md](02-hybrid-search-dense-bm25.md) | Dense + BM25/learned-sparse in parallel, then fuse |
| 03 | [03-reciprocal-rank-fusion.md](03-reciprocal-rank-fusion.md) | Rank-based merge when BM25 and cosine scores are incommensurable |
| 04 | [04-lexical-precision-failures.md](04-lexical-precision-failures.md) | Why pure cosine fails on SKUs, names, error codes, versions |
| 05 | [05-vector-db-selection.md](05-vector-db-selection.md) | pgvector vs dedicated vector DBs vs ES/OpenSearch/Weaviate/Qdrant/Pinecone |
| — | [99-source-map.md](99-source-map.md) | Master URL / paper / blog index |

## Completeness checklist (Week 7)

- [x] All syllabus Week 7 concepts covered with 7 required fields  
- [x] Bi-encoder vs cross-encoder; Sentence-Transformers retrieve & re-rank docs  
- [x] Hybrid search: dense + BM25 (and learned sparse / ELSER / SPLADE as alternatives)  
- [x] Reciprocal Rank Fusion: Cormack et al. 2009 + Elastic/OpenSearch/Qdrant/Weaviate implementations  
- [x] Lexical-precision failure class: SKUs, proper names, error codes, version pins  
- [x] Vector store tradeoffs: pgvector, dedicated vector DBs, hybrid-native search engines  
- [x] Elasticsearch **and** OpenSearch hybrid/RRF docs cited  
- [x] Pinecone / Weaviate / Qdrant hybrid blogs and docs cited  
- [x] pgvector official GitHub README cited  
- [x] Chip Huyen **public blog only** (`genai-platform`, `ai-engineering-pitfalls`) — no book scrape  
- [x] Syllabus build: hybrid retrieval + RRF; **instrument candidate logging**  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 7)

Ship **hybrid retrieval** for the FastAPI RAG chatbot: dense ANN (bi-encoder embeddings) **and** BM25 (or equivalent sparse) over the same chunk IDs, fused with **RRF** (`k=60` unless evals say otherwise). Do **not** stop at cosine-only `top_k`.

**Instrument candidate logging** on every query: query text + query class (semantic vs identifier-like), per-leg ranked IDs and raw scores, fused ranks, fusion method/params, latency of each leg, tenant/filter applied. Persist enough to reproduce “why this chunk was in context.” Week 8 reranking is useless if you cannot see whether the gold chunk never entered the candidate set.

Do not skip this week for “the embedding model is good enough now.” Week 6 chunks that lack SKUs/error codes in the *text* still fail here; Week 9 taxonomies need these logs.

## Default path (synthesis)

1. Index chunks twice: dense vectors + inverted/sparse lexical field (same `chunk_id`).  
2. Retrieve independently (e.g. 50–100 per leg).  
3. Fuse with RRF; log both lists.  
4. Keep metadata filters (tenant, version, product) as **hard** constraints, not “hope cosine notices.”  
5. Escalate fusion (`alpha`, relative-score, learned sparse) only after labeled slices exist.  
6. Cross-encoder rerank is **Week 8** — this week owns recall of the candidate set.
