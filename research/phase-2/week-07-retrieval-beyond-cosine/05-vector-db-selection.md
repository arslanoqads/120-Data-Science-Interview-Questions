# 05 — Vector database selection (pgvector vs dedicated vs hybrid-native)

> Week 7 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

Three practical **buckets** — not a leaderboard of HNSW QPS:

1. **pgvector (Postgres extension)** — vectors **beside** relational data; ACID, PITR, JOINs, RLS, one operational plane if you already run Postgres. Official GitHub README (pgvector/pgvector): exact and approximate NN; types `vector`, `halfvec`, `bit`, `sparsevec`; distances `<->` L2, `<#>` negative inner product, `<=>` cosine, `<+>` L1, Hamming/Jaccard for binary. Indexes: **HNSW** (better speed-recall, slower build, more memory; can build empty) and **IVFFlat** (faster build, less memory, needs data for k-means `lists`). Operator class must match the query operator (`vector_cosine_ops` with `<=>`, not `<->`). Cosine **similarity** is `1 - (embedding <=> query)`. Hybrid BM25 is **not** native: use `tsvector`/`tsquery` (or a sidecar search engine) and **fuse in the application** (RRF). Filtered ANN historically **post-filters** HNSW candidates → **fewer than LIMIT** rows; **0.8.0** added **iterative index scans** (`hnsw.iterative_scan` = `strict_order` | `relaxed_order`, `hnsw.max_scan_tuples` default 20000) so the scan expands until enough rows match `WHERE` or a cap. Supabase/Neon docs reiterate the short-result filtered-search footgun.

2. **Dedicated vector DBs** (Qdrant, Weaviate, Milvus, Pinecone, …) — ANN + **payload filters** as a first-class product; often **native sparse/hybrid**; scale and filtered-search performance beyond the comfort zone of a general-purpose DB. You buy (or operate) a second system and a **sync pipeline** from OLTP/object storage.

3. **Hybrid-native search engines** (Elasticsearch, OpenSearch) — decades of **BM25/BM25F**, analyzers, synonyms, aggregations, plus kNN/semantic + **RRF retrievers / hybrid queries**. Attractive if the team already operates ES for logs/search. Vector features are **version-sensitive**; cluster ops are real.

Huyen (pitfalls): **agonize over what vector database to use** when a simple **term-based** solution that **doesn’t require a vectordb** works — classified under “start too complex.” Platform post: retrieval quality comes from **combining mechanisms**, not from the brand of ANN. Selection is **filters, hybrid, scale, consistency, team ops**.

Pinecone: managed, serverless narrative; hybrid via dense+sparse `dotproduct` index (see concept 02); rerank API. Lowest ops, highest lock-in/cost sensitivity at volume.

Weaviate: first-class `hybrid` BM25F+vector, `alpha`, fusion types, modules; schema learning curve.

Qdrant: Query API prefetch + `rrf`/`dbsf`; strong filtered-vector story; self-host or cloud.

Milvus / Zilliz: large-scale distributed ANN; heavier ops; hybrid features exist but the “why” is usually **scale**.

---

## Alternatives & Tradeoffs

| Option | Choose when | Watch outs |
|--------|-------------|------------|
| **pgvector** | Existing Postgres, moderate scale (often cited informally as low–mid millions if hardware/index fit), need joins/transactions/RLS | DIY hybrid; filtered ANN needs iterative scans / planning; HNSW RAM; vacuum/index build windows |
| **Qdrant** | Filtered vector performance, self-host control, native sparse/hybrid Query API | You own ops (or pay cloud); second store to sync |
| **Weaviate** | Built-in hybrid BM25+vector, GraphQL/modules | Ops/schema; fusion default changed v1.24 |
| **Pinecone** | Zero-ops managed; speed to prod; hybrid sparse+dense | Vendor lock-in; cost at volume; `dotproduct`+client `alpha` for hybrid; less analyzer control than Lucene |
| **Elasticsearch** | Already ES; RRF + BM25 + kNN + ELSER in one engine; relevance engineering culture | Cluster ops; license/distro choices; vector feature matrix by version |
| **OpenSearch** | ES-like, Apache 2.0 lineage; hybrid query + pipelines (norm or RRF) | Plugin/version matrix (Neural Search); hybrid `from`/`size` pagination caveats in docs |
| **Milvus** | Very large scale | Distributed ops |
| **FAISS/Chroma in-process** | Notebooks, tests | Not multi-tenant production by itself |

**pgvectorscale / DiskANN** and similar Postgres accelerators try to close the dedicated-engine gap; treat as evolving — measure on **your** filtered queries.

**Sync tax:** dual-write embeddings vs OLTP; exactly-once chunk IDs; rebuilds when the embed model changes. pgvector avoids a second database but not embed rebuilds.

**Multi-tenancy:** Postgres RLS + `tenant_id` btree vs payload filters on HNSW. Noisy neighbor and **filter selectivity** (post-filter vs pre-filter) dominate more than raw QPS tables.

---

## Necessity

Wrong store creates accidental complexity: **ETL to a vectordb** you didn’t need, or **billion-scale ANN through Postgres** until latency SLOs break. It also creates **fake** hybrid (cosine-only) because the dedicated store was sold as “the RAG database.” Conversely, putting RAG on ES without anyone who understands analyzers yields a worse BM25 than `rank_bm25` in the app.

Huyen’s warning is **necessity of delay**: choosing a vectordb is often premature. Necessity of **eventually choosing well** appears when filters + hybrid + scale interact.

If you skip iterative scans on pgvector, tenant filters **silently under-return** — looks like “RAG missed the doc” (Week 9) when the index never visited it.

---

## Industry Practice

**Common:** Chroma/FAISS in notebooks → Pinecone or Weaviate on first deploy → surprise invoice or surprise ops.

**Strong:** Default **pgvector** if Postgres + modest vectors + SQL filters/joins + willingness to RRF in app (or add OpenSearch later for lexical). Move to **Qdrant/Weaviate/Milvus** when filtered recall/latency or native hybrid dominate. Use **Elasticsearch/OpenSearch** when lexical relevance (synonyms, BM25F field boosts, facets) is already a competency or the corpus **is** the search platform. Measure **end-to-end RAG quality and p95**, not only ANN QPS.

**FDE bar:** explain operator classes; why Pinecone hybrid wants `dotproduct`; why Weaviate `alpha=0.75` is not Elastic RRF; why OpenSearch needs a **pipeline** for hybrid combination; why “just pgvector” still needs `tsvector` for Week 7 syllabus.

---

## Concrete Scenario

pgvector README — types, operators, HNSW vs IVFFlat:

https://github.com/pgvector/pgvector  

Iterative scans / filtering (0.8.0 announcement + README behavior; pgEdge mirror of iterative scan SQL):

https://www.postgresql.org/about/news/pgvector-080-released-2952/  
https://github.com/pgvector/pgvector  

Supabase filtered-search short-result warning:

https://supabase.com/docs/guides/database/extensions/pgvector  

Elasticsearch RRF (hybrid-native engine path):

https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  
https://www.elastic.co/docs/solutions/search/hybrid-search  

OpenSearch hybrid:

https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/  

Qdrant hybrid Query API:

https://qdrant.tech/documentation/search/hybrid-queries/  

Weaviate first-class hybrid:

https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  

Pinecone hybrid:

https://docs.pinecone.io/guides/search/hybrid-search  

Huyen:

https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
https://huyenchip.com/2024/07/25/genai-platform.html  

AWS Database Blog (RDS/Aurora pgvector HNSW/IVFFlat) as a managed-Postgres secondary:

https://aws.amazon.com/blogs/database/optimize-generative-ai-applications-with-pgvector-indexing-a-deep-dive-into-ivfflat-and-hnsw-techniques/

Syllabus: if the chatbot already uses Postgres, implement Week 7 hybrid **in-process RRF** on pgvector + `tsvector` **before** introducing a dedicated engine. Log store name and index params next to candidate lists.

---

## Open Questions

- When do Postgres + `pgvectorscale` / DiskANN close the gap with dedicated engines on **filtered** recall?  
- Should “vector DB” disappear into the **search platform** (ES/OS) or the **OLTP DB** (pgvector)?  
- Multi-tenant noisy-neighbor behavior under HNSW + heavy filters?  
- Embed-model swap: which stores make blue/green vector columns least painful?  
- Sparse vectors in pgvector (`sparsevec`) vs Lucene BM25 as the lexical leg?

---

## Sources

- https://github.com/pgvector/pgvector  
- https://www.postgresql.org/about/news/pgvector-080-released-2952/  
- https://supabase.com/docs/guides/database/extensions/pgvector  
- https://neon.com/docs/ai/ai-vector-search-optimization  
- https://aws.amazon.com/blogs/database/optimize-generative-ai-applications-with-pgvector-indexing-a-deep-dive-into-ivfflat-and-hnsw-techniques/  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  
- https://www.elastic.co/docs/solutions/search/hybrid-search  
- https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/  
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
- https://qdrant.tech/documentation/search/hybrid-queries/  
- https://docs.pinecone.io/guides/search/hybrid-search  
- https://www.pinecone.io/learn/hybrid-search-intro/
