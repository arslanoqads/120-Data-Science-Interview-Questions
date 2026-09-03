# Week 7 — Retrieval Beyond Cosine

> RAW SOURCE MATERIAL for AI Engineer / FDE curriculum. Legal sources only. Chip Huyen via public blog only.

---

## Concept 1: Bi-encoder vs cross-encoder architectures

### Fundamentals
A **bi-encoder** (Sentence Transformer dual-encoder) embeds query and document **independently** into vectors; similarity is cosine / dot product—enabling ANN search over millions of precomputed doc vectors. A **cross-encoder** feeds the **(query, document) pair** jointly through a Transformer and outputs a relevance score; it does **not** produce independently indexable embeddings, but full cross-attention makes it much more accurate on small candidate sets.

Sentence-Transformers docs: bi-encoders for retrieval/clustering at scale; cross-encoders for high-accuracy comparison / re-ranking of ~10² candidates.

### Alternatives & Tradeoffs
| | Bi-encoder | Cross-encoder |
|--|------------|---------------|
| Latency at corpus scale | Milliseconds via HNSW/IVF | Impractical over full corpus |
| Quality | Good recall, weaker fine ranking | Best pairwise relevance |
| Indexing | Precompute doc embeddings | No doc-only index |
| Typical role | Stage-1 retriever | Stage-2 reranker |

ColBERT / late interaction sits between them (token-level interactions with precomputable doc representations)—another alternative when you need more quality than bi-encoders without full cross-encoder cost.

### Necessity
Using only cross-encoders on a large corpus times out. Using only bi-encoders leaves obvious irrelevant near-neighbors in the top-k (synonymy helps, but fine-grained relevance suffers). Production IR almost always combines both (Week 8).

### Industry Practice
**Common:** `all-MiniLM` / vendor embedding API + cosine top-k.  
**Strong:** Domain-tuned bi-encoder (or API embed) → top-50–100 → cross-encoder / Cohere Rerank / BGE-reranker. Sentence-Transformers ships MS MARCO-trained bi- and cross-encoders explicitly for this pattern.

### Concrete Scenario
Official Retrieve & Re-Rank guide: retrieve ~100 hits with bi-encoder or Elasticsearch, then CrossEncoder scores each (query, hit) pair; presents top passages:  
https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  

Architecture explanation (bi vs cross diagrams):  
https://github.com/huggingface/sentence-transformers/blob/main/examples/cross_encoder/applications/README.md

### Open Questions
- When do strong modern embeds (e.g., large API models) reduce the marginal value of cross-encoders?
- Should stage-1 be dense, sparse, or hybrid before the cross-encoder?
- Distilled / listwise rerankers vs pointwise cross-encoders?

### Sources
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
- https://github.com/huggingface/sentence-transformers/blob/main/examples/cross_encoder/applications/README.md
- https://osanseviero.github.io/hackerllama/blog/posts/sentence_embeddings2/
- https://www.pinecone.io/learn/series/rag/rerankers/

---

## Concept 2: Hybrid search (dense vector + BM25 / lexical)

### Fundamentals
**Hybrid search** runs dense (semantic) retrieval and sparse/lexical retrieval (BM25/BM25F, or learned sparse like SPLADE/ELSER) in parallel, then **fuses** ranked lists. Dense captures paraphrase/synonymy; BM25 captures exact tokens (SKUs, error codes, names, version strings).

Chip Huyen (public platform post): term-based retrieval is fast/cheap and a strong baseline; embedding retrieval is more expensive but improvable; combining them is hybrid search.

Weaviate: hybrid = vector + BM25, scores combined via fusion (`relativeScoreFusion` or `rankedFusion`).

### Alternatives & Tradeoffs
| Stack | Notes |
|-------|-------|
| Dense only | Fails on lexical-precision queries |
| BM25 only | Fails on semantic paraphrase |
| Dense + BM25 + RRF | Robust default, little tuning |
| Dense + BM25 + weighted alpha | Tunable if you have labels |
| Dense + learned sparse (SPLADE/ELSER) | Often stronger than classic BM25; more ops |
| Hybrid + metadata filters | Production multi-tenant pattern |

### Necessity
Pure cosine RAG systematically misses queries where the right answer hinges on an exact rare token that embeddings smooth away. Support/docs/code search without lexical signal is a known production failure mode (Elasticsearch AI Engineer lab framing: break vector with version numbers and error codes, rescue with BM25).

### Industry Practice
**Common:** Vectordb cosine only in prototypes.  
**Strong:** Hybrid as default for technical corpora; tune fusion after measuring failure classes; keep BM25 field analyzers (stemming, identifiers) intentional. Huyen’s pitfalls post warns against agonizing over vectordb choice when term-based retrieval might already work.

### Concrete Scenario
Weaviate conceptual docs + “Hybrid Search Explained” blog: parallel BM25 + vector, fusion methods, `alpha` weighting:  
https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
https://weaviate.io/blog/hybrid-search-explained  

Qdrant + LangChain hybrid (`RetrievalMode.HYBRID`, dense + sparse BM25 embeddings):  
https://qdrant.tech/documentation/frameworks/langchain/  
https://docs.langchain.com/oss/python/integrations/vectorstores/qdrant

### Open Questions
- Classic BM25 vs learned sparse as the lexical leg?
- Server-side fusion (Qdrant/Weaviate/ES) vs client-side EnsembleRetriever?
- Per-query routing (skip dense for identifier-like queries)?

### Sources
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search
- https://weaviate.io/blog/hybrid-search-explained
- https://qdrant.tech/documentation/frameworks/langchain/
- https://docs.langchain.com/oss/python/integrations/vectorstores/qdrant

---

## Concept 3: Reciprocal Rank Fusion (RRF)

### Fundamentals
**RRF** merges multiple ranked lists without calibrating score scales. For each document \(d\):

\[
\mathrm{RRF}(d) = \sum_{r \in \text{rankers}} \frac{1}{k + \mathrm{rank}_r(d)}
\]

with rank constant \(k\) commonly **60**. Documents appearing near the top of multiple lists rise; score magnitudes (incompatible across BM25 vs cosine) are ignored.

Elasticsearch: `rrf` retriever wraps child retrievers (e.g., BM25 `standard` + `knn`); no tuning required for score commensurability. Weaviate’s `rankedFusion` is RRF-style; `relativeScoreFusion` (default since v1.24) instead min-max normalizes scores then sums—preserving margin information.

### Alternatives & Tradeoffs
| Fusion | Pros | Cons |
|--------|------|------|
| **RRF** | Zero-config; robust across modalities | Ignores confidence margins |
| Relative / min-max score fusion | Uses score magnitude | Sensitive to outliers / list length |
| Weighted linear (`α·dense + (1-α)·sparse`) | Interpretable knob | Needs labels to set α; rescale carefully |
| DBSF (Qdrant) | Distribution-aware normalization | More moving parts |

### Necessity
Naïve averaging of BM25 and cosine scores is invalid—different units/distributions. Without fusion discipline, hybrid “helps” randomly. RRF is the safe merge when you lack a validation set.

### Industry Practice
**Common:** Vendor default hybrid (often RRF or relative score fusion).  
**Strong:** Start RRF (`k=60`); A/B against relativeScoreFusion; only introduce learned α with ≥ tens of labeled queries; set `rank_window_size` high enough that each leg contributes (Elasticsearch docs).

### Concrete Scenario
Elasticsearch RRF reference—combine BM25 + kNN (or ELSER) via `rrf` retriever, `rank_constant`, `rank_window_size`:  
https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  

Weaviate fusion types explained:  
https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
https://weaviate.io/blog/hybrid-search-explained

### Open Questions
- Optimal \(k\) as a function of candidate depth?
- Should reranker scores replace RRF as the final fuse when both legs return candidates?
- Multi-channel RRF (dense + sparse + reciprocal links / graph)?

### Sources
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search
- https://weaviate.io/blog/hybrid-search-explained
- https://sbert.net/examples/sparse_encoder/applications/retrieve_rerank/README.html (hybrid + RRF evaluation mention)

---

## Concept 4: Why pure semantic similarity fails on lexical-precision queries

### Fundamentals
Dense embeddings optimize semantic neighborhoods. They **blur** rare identifiers, version pins (`8.18` vs `9.0`), error codes, SKUs, legal citations, and exact config keys—queries where the correct doc is the one that literally contains the token. Lexical methods excel exactly there; dense methods excel on “how do I reset MFA?” paraphrases. Failure is asymmetric: semantic search returns fluent wrong neighbors.

Sentence-Transformers explicitly contrasts lexical search (literal matches; misses synonyms) with semantic search (synonyms; can miss exactness)—motivating hybrid + rerank pipelines.

### Alternatives & Tradeoffs
Mitigations ranked by invasiveness:
1. Hybrid BM25 + dense (usually enough)
2. Metadata / keyword filters (`product_id`, `version`)
3. Query classification → lexical-only path for “code-like” queries
4. Learned sparse embeddings
5. Reranker that sees raw tokens (cross-encoder)

### Necessity
Skipping this analysis causes demos that look great on conceptual FAQs and collapse on ticket deflection / developer docs—the queries customers actually type.

### Industry Practice
**Common:** Discover the failure in production after launch.  
**Strong:** Build an eval slice of lexical-precision queries (IDs, errors, versions) alongside semantic paraphrases; gate releases on both slices. Elasticsearch AI Engineer lab narrative (“Vector Isn’t Enough”) uses adversarial exact-match queries to teach this.

### Concrete Scenario
AI Engineer World’s Fair-style lab description—break pure vector with error codes and version numbers, then fuse BM25 via Elasticsearch RRF:  
https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a  

Weaviate hybrid motivation (sparse + dense roles):  
https://weaviate.io/blog/hybrid-search-explained

Huyen: start with term-based; don’t overcomplicate vectordb early:  
https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html

### Open Questions
- Can instruct-tuned embeds close the lexical gap enough to drop BM25?
- Character-level or n-gram augmentation inside dense models?
- How to detect lexical-precision queries reliably online?

### Sources
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
- https://weaviate.io/blog/hybrid-search-explained
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a

---

## Concept 5: Vector database selection (pgvector vs dedicated vector DBs vs hybrid-native search engines)

### Fundamentals
Three practical buckets:

1. **pgvector (Postgres extension)** — vectors beside relational data; transactional consistency; SQL filters/joins; sweet spot roughly low–mid millions of vectors if you already run Postgres.
2. **Dedicated vector DBs** (Qdrant, Weaviate, Milvus, Pinecone, …) — ANN + payload filters first-class; often native sparse/hybrid; scale and filtered-search performance beyond comfort zone of general-purpose DB indexes.
3. **Hybrid-native search engines** (Elasticsearch/OpenSearch) — mature BM25 + vectors + RRF retrievers in one engine; attractive if the team already operates ES for search/logs.

Huyen: agonizing over which vectordb to use is a common early pitfall when simpler retrieval may suffice.

### Alternatives & Tradeoffs
| Option | Choose when | Watch outs |
|--------|-------------|------------|
| **pgvector** | Existing Postgres, moderate scale, need joins/transactions | Filtered ANN can degrade; hybrid is DIY (`tsvector` + vector + app-side RRF) |
| **Qdrant** | Filtered vector search performance, self-host control, native sparse/hybrid | You own ops (or pay cloud) |
| **Weaviate** | Want built-in hybrid BM25+vector, modules | Ops/schema learning curve |
| **Pinecone** | Zero-ops managed; speed to prod | Vendor lock-in, cost at volume, less low-level control |
| **Elasticsearch/OpenSearch** | Already ES; need RRF + BM25 + kNN together | Cluster ops; vector features must be version-aware |
| **Milvus** | Very large scale | Heavier distributed ops |

### Necessity
Wrong store creates accidental complexity: sync pipelines between OLTP and a vectordb, or conversely, pushing billion-scale ANN through Postgres until latency SLOs break. Selection is an architecture decision tied to **filters, hybrid, scale, and team ops**—not leaderboard HNSW microbenchmarks alone.

### Industry Practice
**Common:** Chroma/FAISS in notebooks → Pinecone/Weaviate in first deploy.  
**Strong:** Default **pgvector** if Postgres + <~5–10M vectors + simple filters; move to Qdrant/Weaviate/Milvus when filtered recall/latency or hybrid native features dominate; use Elasticsearch when lexical relevance engineering is already a competency. Measure end-to-end RAG quality, not only ANN QPS.

### Concrete Scenario
Elasticsearch RRF shows hybrid-native engine path (BM25 + knn in one query API):  
https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  

Qdrant hybrid via Query API prefetch + RRF (framework docs):  
https://qdrant.tech/documentation/frameworks/langchain/  

Weaviate first-class hybrid:  
https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  

Comparative engineering guidance (pgvector vs Pinecone vs Qdrant tradeoffs—use as secondary synthesis, verify against primary vendor docs):  
https://theaugmenteddev.com/blog/vector-databases-compared-pgvector-qdrant-pinecone

### Open Questions
- When does Postgres + `pgvectorscale` / DiskANN close the gap with dedicated engines?
- Should “vector DB” disappear into the search platform (ES) or the OLTP DB (pgvector)?
- Multi-tenant noisy-neighbor behavior under HNSW + heavy filters?

### Sources
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search
- https://qdrant.tech/documentation/frameworks/langchain/
- https://docs.langchain.com/oss/python/integrations/vectorstores/qdrant
- https://theaugmenteddev.com/blog/vector-databases-compared-pgvector-qdrant-pinecone
- https://learnbackend.com/guides/pgvector-vs-pinecone-vs-qdrant/

---

## Week 7 synthesis notes (for later curriculum writing)

1. Bi-encoder retrieves; cross-encoder (Week 8) precision-ranks.  
2. Hybrid + RRF is the pragmatic production default for technical corpora.  
3. Lexical-precision eval slices are mandatory.  
4. Pick storage from **consistency / filters / hybrid / ops**, not hype—Huyen’s “start simpler” applies.

### Talk / video pointers
- Greg Kamradt / FullStackRetrieval chunking talk feeds ingest quality upstream of retrieval: https://youtu.be/8OJC21T2SL4  
- AI Engineer hybrid search lab framing: https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a  
- Emil Eifrem GraphRAG (AI Engineer) — beyond vector/BM25 when relations matter: https://ai.engineer/talks/graphrag
