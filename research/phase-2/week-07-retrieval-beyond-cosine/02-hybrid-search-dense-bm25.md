# 02 — Hybrid search (dense vector + BM25 / lexical)

> Week 7 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

**Hybrid search** runs a **dense** (semantic / embedding) retriever and a **sparse/lexical** retriever in parallel, then **fuses** the ranked lists into one. Dense captures paraphrase, synonymy, and “the user did not use our heading vocabulary.” Lexical (BM25/BM25F, or learned sparse such as SPLADE / Elastic **ELSER**) captures **exact tokens**: SKUs, error codes, proper names, version strings, config keys.

Sentence-Transformers’ retrieve & re-rank page contrasts the two first stages you might use *before* a cross-encoder: **lexical search** looks for literal matches and “will not recognize synonyms, acronyms or spelling variations”; **semantic search** encodes the query into vector space and retrieves nearby document embeddings. Hybrid is the refusal to pick only one of those first stages.

Chip Huyen (public platform post): **term-based retrieval** can be keyword search or BM25 / Elasticsearch inverted indexes; it is usually used for text but also for images/video **via text metadata**. **Embedding-based** retrieval is more expensive but improvable. “A production retrieval system typically combines several approaches. Combining term-based retrieval and embedding-based retrieval is called **hybrid search**.” She distinguishes **sequential** (cheap term filter then kNN/rerank among survivors) from **ensemble** (multiple retrievers rank in parallel, then combine). Week 7’s default is **ensemble**; sequential is a valid alternative when BM25 is an excellent high-recall gate.

**Weaviate:** hybrid = vector + BM25; scores combined via fusion. Parameters: `alpha` (default **0.75** in their API docs — 0 = pure keyword, 1 = pure vector, 0.5 = even); `fusionType` = `relativeScoreFusion` (default since **v1.24**) or `rankedFusion` (RRF-style, default ≤ v1.23). Conceptual docs explain why they prefer relative score fusion: it **retains score margins**, whereas ranked fusion only keeps order.

**Elasticsearch:** hybrid is full-text + vector in **one request**. Official hybrid-search solution doc: **recommend RRF** to merge full-text and vector rankings. Retriever tree: `rrf` wrapping `standard` (BM25 `match`/`multi_match`) and `knn`, optionally ELSER/sparse. Also `linear` retriever when you *do* want weighted scores with a normalizer.

**OpenSearch:** hybrid query + **search pipeline**. Two philosophies: **normalization-processor** (min_max / L2 / z-score then arithmetic/geometric/harmonic mean — score-based, preserves margins, weights as decimal percentages) vs **score-ranker-processor** (RRF, rank-based, available from 2.19). Docs say choose score-based when margins should survive; choose RRF when you do not want to measure how each clause scores.

**Qdrant:** named vectors (dense + sparse) on one point; Query API `prefetch` each representation then fuse with `rrf` or **DBSF** (distribution-based score fusion). Sparse may be BM25-like (`Qdrant/bm25` document models in their course) or learned sparse.

**Pinecone:** **single index** storing dense `values` + `sparse_values`; metric must be **`dotproduct`** for combined dense/sparse on one index. Sparse and dense are **not** on the same numeric range; docs warn that without weighting, sparse can dominate. Weighting is typically **client-side** `alpha` scaling of the query vectors (`hybrid_score_norm`: dense × α, sparse × (1−α)) because `index.query` does not take an `alpha` kwarg. Separate-index hybrid is supported but they recommend one index for ops simplicity. Schema/FTS path (BM25 string fields + vectors) is a newer document-oriented alternative.

Learned sparse (ELSER, SPLADE): still “lexical-shaped” (weighted terms in a huge vocabulary) but can match **expanded** terms (synonyms) better than raw BM25. Elastic treats BM25 + ELSER + dense as a three-child RRF tree.

---

## Alternatives & Tradeoffs

| Stack | Notes |
|-------|-------|
| Dense only | Fails on lexical-precision queries (concept 04) |
| BM25 only | Fails on semantic paraphrase; still Huyen’s suggested **first** experiment |
| Dense + BM25 + RRF | Robust default; little tuning; syllabus path |
| Dense + BM25 + weighted alpha / relativeScoreFusion | Tunable if you have labels; Weaviate default path |
| Dense + learned sparse | Often stronger than classic BM25; model/version ops |
| Hybrid + metadata filters | Production multi-tenant pattern; filters are not fusion |
| Sequential term-then-dense | Cheap; catastrophic if gold has no lexical overlap |
| Client EnsembleRetriever vs server hybrid | Portability vs latency/consistency of one round trip |

Analyzer choices **are** the lexical leg: stemming `ERROR`/`error`, splitting `SKU-7F2A`, lowercasing vs keyword fields. Hybrid quality is often an **ingest** bug (Week 6 metadata + this week’s analyzer), not a fusion bug.

---

## Necessity

Pure cosine RAG systematically misses queries where the right answer hinges on an **exact rare token** that embeddings **smooth away**. Support, docs, and code search without a lexical signal is a known production failure mode. Elastic’s public hybrid material and “vector isn’t enough” lab framing exist to **break** vector search with version numbers and error codes, then rescue with BM25.

Skipping hybrid also skips **candidate diversity**: two lists of 80 with modest overlap beat one list of 80 that all sit in the same semantic neighborhood (near-duplicate chunks).

If you skip fusion discipline and `sum(0.5*minmax(bm25)+0.5*cosine)` with ad-hoc scaling, A/B tests lie: you are testing your scaler, not hybrid.

---

## Industry Practice

**Common:** Vectordb cosine only in prototypes; “we’ll add BM25 later.”

**Strong:** Hybrid as **default** for technical corpora; keep BM25 field analyzers intentional (identifiers as `keyword` or minimal analysis); tune fusion **after** measuring failure classes (semantic vs lexical slices). Huyen’s pitfalls post: do not agonize over vectordb choice when **term-based retrieval that doesn’t require a vectordb** might already work — i.e. prove BM25 value on your queries **before** a three-vendor bake-off.

**FDE bar:** name the engine’s actual hybrid primitive (ES `rrf` retriever, OS hybrid + pipeline, Weaviate `alpha`+fusionType, Qdrant prefetch+fusion, Pinecone sparse+dense dotproduct, pgvector DIY). Log both legs (syllabus). Elastic: `rank_window_size` must be large enough that each child actually contributes documents into RRF.

---

## Concrete Scenario

Weaviate conceptual docs + “Hybrid Search Explained” blog: parallel BM25 + vector; `rankedFusion` vs `relativeScoreFusion`; `alpha`.

https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
https://weaviate.io/blog/hybrid-search-explained  

Elasticsearch hybrid solution page + RRF reference (BM25 `standard` + `knn` in one retriever tree):

https://www.elastic.co/docs/solutions/search/hybrid-search  
https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  

OpenSearch hybrid index (pipeline + hybrid query):

https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/  

Qdrant hybrid Query API:

https://qdrant.tech/documentation/search/hybrid-queries/  

Pinecone hybrid guide + learn intro:

https://docs.pinecone.io/guides/search/hybrid-search  
https://www.pinecone.io/learn/hybrid-search-intro/  

Huyen:

https://huyenchip.com/2024/07/25/genai-platform.html  

Syllabus: same `chunk_id` in both indexes; never fuse “document 12 from BM25” with a different chunking of document 12 from dense.

---

## Open Questions

- Classic BM25 vs learned sparse as the lexical leg on *your* tokenizer/domain?  
- Server-side fusion vs client-side RRF (pgvector, FAISS + rank_bm25)?  
- Per-query routing (skip dense for identifier-like queries; skip BM25 for long natural language)?  
- Should `alpha` be predicted by a tiny classifier rather than global?  
- Three-way hybrid (BM25 + dense + sparse-learned) — diminishing returns vs ops cost?

---

## Sources

- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
- https://docs.weaviate.io/weaviate/search/hybrid  
- https://weaviate.io/blog/hybrid-search-explained  
- https://weaviate.io/blog/hybrid-search-fusion-algorithms  
- https://www.elastic.co/docs/solutions/search/hybrid-search  
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  
- https://www.elastic.co/what-is/hybrid-search  
- https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/  
- https://docs.opensearch.org/latest/query-dsl/compound/hybrid/  
- https://opensearch.org/blog/building-effective-hybrid-search-in-opensearch-techniques-and-best-practices/  
- https://qdrant.tech/documentation/search/hybrid-queries/  
- https://docs.pinecone.io/guides/search/hybrid-search  
- https://www.pinecone.io/learn/hybrid-search-intro/
