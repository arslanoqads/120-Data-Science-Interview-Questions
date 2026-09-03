# 99 — Week 7 master source map

> Consolidated index of official docs, vendor blogs, papers, talks. Legal sources only. Chip Huyen via **public blog only** (no pirated *AI Engineering* book).

---

## Chip Huyen (public blog)

| Topic | URL |
|-------|-----|
| GenAI platform: term-based vs embedding vs **hybrid**; sequential vs ensemble retrieval; rerank vs lost-in-the-middle | https://huyenchip.com/2024/07/25/genai-platform.html |
| Pitfalls: **start too complex** — agonize over vectordb when term-based retrieval (no vectordb) works | https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html |

---

## Sentence-Transformers (bi-encoder vs cross-encoder)

| Topic | URL |
|-------|-----|
| **Retrieve & Re-Rank** (lexical *or* bi-encoder → CrossEncoder; ~100 candidates; lexical vs semantic contrast) | https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html |
| Semantic search (keyword vs meaning; ANN at ~1M; encode_query / encode_document) | https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html |
| Cross-encoder applications README (diagrams; clustering 65h vs bi-encoder 5s; no indexable embeddings) | https://github.com/huggingface/sentence-transformers/blob/main/examples/cross_encoder/applications/README.md |
| Quickstart (SentenceTransformer vs CrossEncoder vs Sparse vs multi-vector) | https://sbert.net/docs/quickstart.html |
| Sparse retrieve & rerank (hybrid + RRF mention in family of guides) | https://sbert.net/examples/sparse_encoder/applications/retrieve_rerank/README.html |
| SBERT paper (Cross-Encoder vs Bi-Encoder quality) | https://huggingface.co/papers/1908.10084 |
| Osanseviero public explainer | https://osanseviero.github.io/hackerllama/blog/posts/sentence_embeddings2/ |

---

## Reciprocal Rank Fusion (original + engines)

| Topic | URL |
|-------|-----|
| Cormack, Clarke, Buettcher, SIGIR 2009 (DOI) | https://doi.org/10.1145/1571941.1572114 |
| Google Research pubs page | https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/ |
| Elasticsearch RRF (current docs) | https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion |
| Elasticsearch `rrf` retriever | https://www.elastic.co/docs/reference/elasticsearch/rest-apis/retrievers/rrf-retriever |
| Elasticsearch Guide 8.19 RRF | https://www.elastic.co/guide/en/elasticsearch/reference/8.19/rrf.html |
| OpenSearch RRF hybrid | https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/ |
| OpenSearch score-ranker-processor | https://docs.opensearch.org/latest/search-plugins/search-pipelines/score-ranker-processor/ |
| OpenSearch introducing RRF blog | https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/ |
| Redis explainer (secondary; why not add scores) | https://redis.io/blog/reciprocal-rank-fusion/ |

---

## Elasticsearch / OpenSearch hybrid

| Topic | URL |
|-------|-----|
| Elastic hybrid search (solution; recommend RRF) | https://www.elastic.co/docs/solutions/search/hybrid-search |
| Elastic “what is hybrid search” | https://www.elastic.co/what-is/hybrid-search |
| Elastic hybrid product page | https://www.elastic.co/elasticsearch/hybrid-search |
| OpenSearch hybrid search | https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/ |
| OpenSearch hybrid query DSL | https://docs.opensearch.org/latest/query-dsl/compound/hybrid/ |
| OpenSearch normalization-processor | https://docs.opensearch.org/latest/search-plugins/search-pipelines/normalization-processor/ |
| OpenSearch hybrid techniques blog | https://opensearch.org/blog/building-effective-hybrid-search-in-opensearch-techniques-and-best-practices/ |

---

## Weaviate / Qdrant / Pinecone hybrid

| Topic | URL |
|-------|-----|
| Weaviate hybrid concepts (`relativeScoreFusion` vs `rankedFusion`) | https://docs.weaviate.io/weaviate/concepts/search/hybrid-search |
| Weaviate hybrid search how-to (`alpha`, fusion) | https://docs.weaviate.io/weaviate/search/hybrid |
| Hybrid Search Explained (blog) | https://weaviate.io/blog/hybrid-search-explained |
| Fusion algorithms deep dive (blog) | https://weaviate.io/blog/hybrid-search-fusion-algorithms |
| Qdrant Hybrid / Query API (`rrf`, `dbsf`, prefetch) | https://qdrant.tech/documentation/search/hybrid-queries/ |
| Qdrant hybrid course demo | https://qdrant.tech/course/essentials/day-3/hybrid-search-demo/ |
| Pinecone hybrid search docs | https://docs.pinecone.io/guides/search/hybrid-search |
| Pinecone getting started with hybrid search | https://www.pinecone.io/learn/hybrid-search-intro/ |
| Pinecone rerankers / two-stage | https://www.pinecone.io/learn/series/rag/rerankers/ |

---

## pgvector

| Topic | URL |
|-------|-----|
| **Official README** (operators, HNSW, IVFFlat, types) | https://github.com/pgvector/pgvector |
| 0.8.0 iterative scans / filtering | https://www.postgresql.org/about/news/pgvector-080-released-2952/ |
| Supabase pgvector (filtered search short results) | https://supabase.com/docs/guides/database/extensions/pgvector |
| Neon optimize pgvector | https://neon.com/docs/ai/ai-vector-search-optimization |
| AWS RDS/Aurora HNSW vs IVFFlat | https://aws.amazon.com/blogs/database/optimize-generative-ai-applications-with-pgvector-indexing-a-deep-dive-into-ivfflat-and-hnsw-techniques/ |

---

## Talks / labs (lexical precision)

| Topic | URL |
|-------|-----|
| “Vector Isn’t Enough” hybrid search lab framing (error codes, versions) | https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a |
| Greg Kamradt chunking (upstream of retrieval; Week 6) | https://youtu.be/8OJC21T2SL4 |

---

## Coverage matrix (syllabus concepts → primary URLs)

| Concept file | Must-cite |
|--------------|-----------|
| 01 bi vs cross | SBERT retrieve_rerank + cross_encoder applications README + Pinecone rerankers |
| 02 hybrid | Huyen genai-platform + Weaviate hybrid + Elastic hybrid + OpenSearch hybrid + Qdrant + Pinecone hybrid |
| 03 RRF | Cormack DOI + Elastic RRF + OpenSearch RRF + Weaviate rankedFusion + Qdrant rrf |
| 04 lexical precision | SBERT lexical vs semantic + Huyen + Elastic/Pinecone rare-term hybrid + Vector Isn’t Enough talk |
| 05 store selection | pgvector GitHub + Huyen pitfalls + ES/OS/Weaviate/Qdrant/Pinecone as above |

**Not used:** pirate book/PDF sites; Chip Huyen *AI Engineering* book text.
