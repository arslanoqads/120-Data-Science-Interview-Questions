# 00 — Week overview & syllabus mapping

> Week 7 — Retrieval beyond cosine  
> Research notes (raw).

---

## Fundamentals

Week 7 is the **candidate-generation** week of Phase 2 RAG. Week 6 decided *what* is stored. This week decides *which stored units are even eligible* for generation (and, next week, for reranking). Cosine / inner-product over a single dense embedding is one retriever, not a retrieval *system*. Production IR treats retrieval as **multi-channel**: a cheap high-recall first stage (or two parallel first stages) that must put the right chunk in a shortlist of tens to low hundreds.

Chip Huyen’s public platform post frames retrieval as a menu, not a religion: **term-based** (keyword / BM25 / inverted index — fast, cheap, strong baseline; also works on text metadata of images/video), **embedding-based** (more expensive, improvable with better models and indexes), and **hybrid** as the production combination. She also describes two composition patterns: **sequential** (cheap retriever then more precise ranking — classical retrieve-then-rerank) and **ensemble** (multiple retrievers in parallel, then combine rankings). Week 7 owns the ensemble + first-stage half; Week 8 owns the expensive pairwise rerank.

Sentence-Transformers’ retrieve & re-rank guide is the shared vocabulary: stage-1 can be **lexical** (Elasticsearch-class BM25) **or** a **bi-encoder**; stage-2 is a **cross-encoder** that scores `(query, document)` jointly. The guide is explicit that lexical search misses synonyms while semantic search can miss exactness — that contrast *is* the Week 7 problem, not a footnote.

The syllabus spine:

1. **Bi-encoder vs cross-encoder** — independent embeddings + ANN vs pair scoring; why you cannot cross-encode the corpus.  
2. **Hybrid search** — dense + BM25 (or learned sparse) in parallel.  
3. **RRF** — merge ranked lists without pretending BM25 and cosine share a scale.  
4. **Lexical-precision failures** — SKUs, names, error codes, version pins as a first-class eval slice.  
5. **Store selection** — pgvector vs dedicated vector DBs vs hybrid-native engines (Elasticsearch/OpenSearch, Weaviate, Qdrant, Pinecone).

**Instrument candidate logging** is not optional polish. If you only log the final `top_k` sent to the LLM, you cannot distinguish: (a) gold never retrieved on either leg, (b) gold retrieved on BM25 but dropped by fusion, (c) gold fused in but truncated before generate, (d) generate ignored a present gold chunk (Week 9). Logs need per-leg ranks, scores, fusion params, filters, and timings.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Dense cosine only | Demo speed; one index; synonymy | Identifier queries; rare tokens; version pins |
| BM25 only | Exact tokens; cheap ops; explainability | Paraphrase / “how do I…” FAQs |
| Hybrid + RRF (syllabus default) | Robust default; no score calibration | Ignores confidence margins; needs two indexes |
| Hybrid + weighted `alpha` / relative-score fusion | Uses score magnitude; tunable | Needs labels; sensitive to list length/outliers |
| Dense + learned sparse (SPLADE / ELSER) | Often stronger lexical+semantic in one family | Model ops, inference cost, version pinning |
| Sequential BM25-then-dense (Huyen sequential) | Cheap candidate cut | Gold that BM25 never surfaces never recovers |
| Jump to vectordb bake-off (Huyen pitfall) | Feels like architecture work | Abstracts the retrieval *mechanism* you need to debug |

For the flagship RAG chatbot, Week 7 should prefer **parallel dense + BM25 → RRF → logged candidate set**, with metadata filters as hard predicates. Do not start by swapping Pinecone for Qdrant to “fix relevance.” Huyen’s pitfalls post: agonize over which vector database to use when term-based retrieval (no vectordb) might already work.

---

## Necessity

Concrete failure modes if Week 7 is skipped:

- FAQ demos look great; ticket deflection on `ECONNRESET`, `SKU-1842`, `OpenSearch 2.19` collapses.  
- Cross-encoder / Cohere Rerank in Week 8 cannot resurrect a chunk that never entered the 100-hit pool.  
- Averaging BM25 and cosine without fusion discipline randomly promotes one modality.  
- No candidate logs → every production miss is blamed on “the LLM hallucinated.”  
- Store choice happens on HNSW microbenchmarks instead of hybrid + filter + ops constraints.  
- Over-investing in a dedicated vector DB before BM25 exists (Huyen: don’t start too complex).

Elasticsearch’s hybrid framing and OpenSearch’s hybrid docs both exist because **score incommensurability** and **keyword vs meaning** are engine-level problems, not library preferences.

---

## Industry Practice

- **Common (demo AI):** `embed(query)` → `vectordb.similarity_search(k=5)` → stuff context. One embedding API. No BM25. No logs beyond LangSmith span names.  
- **Strong:** Dual index; RRF or vendor hybrid; eval slices for **semantic paraphrase** *and* **lexical precision**; candidate logging with `chunk_id` ranks per retriever; filters for tenant/version. Elastic recommends RRF as the hybrid default; OpenSearch offers score-normalization *or* RRF via search pipelines; Weaviate defaults `relativeScoreFusion` since v1.24 but still ships `rankedFusion`; Qdrant Query API prefetches dense+sparse then `rrf`/`dbsf`; Pinecone hybrid is dense+sparse in one `dotproduct` index with client-side `alpha` scaling.  
- **FDE bar:** can explain why Sentence-Transformers says retrieve ~100 then cross-encode (Week 8); why Cormack et al. set `k≈60`; why pgvector hybrid is `tsvector` + vector + *app-side* fusion; why “vector isn’t enough” labs break cosine with error codes and versions.

---

## Concrete Scenario

Syllabus build: same product runbooks as Week 6. Index each chunk’s embedding **and** a BM25 field (analyzer that keeps identifiers: don’t stem `ECONNRESET` into mush). On query:

1. Dense top-80 + BM25 top-80.  
2. RRF fuse to 40.  
3. Log JSON: `{query, dense:[{id,rank,score}], bm25:[...], fused:[...], k:60, filters}`.  
4. Golden set includes: “reset MFA” (semantic), `ERR_OS_4092` (error code), `widget SKU-7F2A` (SKU), `v8.18 vs v9.0` (version). Gate the week on **recall@40 on both slices**, not only nDCG on FAQs.

Public bar: Sentence-Transformers retrieve & re-rank (bi-encoder or Elasticsearch, then CrossEncoder — defer CrossEncoder scoring to Week 8 but **build the candidate API now**). Elastic RRF retriever wrapping `standard` + `knn`. Weaviate hybrid conceptual docs. Huyen platform post on hybrid vs sequential.

URL: https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
Companions: https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion · https://huyenchip.com/2024/07/25/genai-platform.html · https://docs.weaviate.io/weaviate/concepts/search/hybrid-search

---

## Open Questions

- Do modern API embedders (large multilingual, instruction-tuned) shrink the hybrid gap enough to drop BM25 on *some* corpora?  
- Per-query routing (lexical-only when the query looks like an identifier) vs always-hybrid?  
- Should candidate logs live in the app tracer (OpenTelemetry attributes) or a retrieval-specific table for eval joins?  
- Server-side fusion (ES/Qdrant/Weaviate) vs client-side RRF for portability across pgvector?  
- When does sequential (filter-by-BM25 then dense) beat parallel ensemble?

---

## Candidate logging (syllabus instrument)

Minimum record per request (JSON or OTel attributes + a joinable `retrieval_id`):

| Field | Why |
|-------|-----|
| `query_text`, `query_hash` | Replay; PII policy decides redaction |
| `query_class` | `semantic` \| `identifier` \| `mixed` — slice metrics |
| `filters` | tenant, product, version — explain empty results |
| `dense.ids[]`, `dense.ranks[]`, `dense.scores[]` | Did ANN see gold? |
| `lexical.ids[]`, `lexical.ranks[]`, `lexical.scores[]` | Did BM25 see gold? |
| `fusion.method`, `fusion.k`, `fusion.window` | RRF vs alpha vs relative |
| `fused.ids[]`, `fused.ranks[]` | What left this week toward generate/Week 8 |
| `latencies_ms.{embed,ann,bm25,fusion}` | SLO: which leg is slow |
| `store`, `embed_model`, `index_names` | Model-swap debugging |

If Week 8 reranks, **do not overwrite** this record — append `rerank.ids[]` / `rerank.scores[]`. Week 9 failure taxonomy joins on `retrieval_id`.

---

## Boundaries with adjacent weeks

| Week | This week does | This week does not |
|------|----------------|-------------------|
| 6 | Consume stable `chunk_id` + metadata | Re-chunk to “fix retrieval” without evidence |
| 7 | Hybrid + RRF + logs; store choice criteria | Claim cosine-only is done |
| 8 | Expose a candidate list API of size ~50–100 | Ship cross-encoder as the *only* retriever |
| 9 | Provide logs that distinguish miss-at-retrieve vs miss-at-generate | Full failure taxonomy write-up |
| 10 | Provide slice recall numbers | Full metric framework |

---

## Sources

- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  
- https://www.elastic.co/docs/solutions/search/hybrid-search  
- https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/  
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
- https://weaviate.io/blog/hybrid-search-explained  
- https://qdrant.tech/documentation/search/hybrid-queries/  
- https://docs.pinecone.io/guides/search/hybrid-search  
- https://www.pinecone.io/learn/series/rag/rerankers/
