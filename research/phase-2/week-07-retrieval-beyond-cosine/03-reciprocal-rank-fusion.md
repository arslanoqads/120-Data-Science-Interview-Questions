# 03 — Reciprocal Rank Fusion (RRF)

> Week 7 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

**Reciprocal Rank Fusion** merges multiple ranked lists **without calibrating score scales**. For each document \(d\):

\[
\mathrm{RRF}(d) = \sum_{r \in \text{rankers}} \frac{1}{k + \mathrm{rank}_r(d)}
\]

Ranks are **1-based**. Documents missing from a list contribute **0** from that list. The constant \(k\) (often called `rank_constant`) is commonly **60**, the value Cormack, Clarke, and Buettcher used and recommended in **SIGIR 2009**: *“Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods”* (ACM 10.1145/1571941.1572114; Google Research pubs mirror). They showed unsupervised RRF combining TREC runs beat individual systems and Condorcet Fuse, and built a LETOR meta-learner from it.

**Why ranks, not scores:** BM25 scores are typically unbounded positives whose magnitude depends on query length, field boosts, and IDF. Cosine similarity lives in \([-1,1]\) (often ~0.2–0.8 in practice). Inner product / unnormalized dense scores are another scale. ELSER/SPLADE yet another. **Naïve sums and uncalibrated weighted averages are invalid.** RRF throws scores away and keeps order. Elastic’s RRF docs: “RRF requires **no tuning**, and the different relevance indicators **do not have to be related** to each other to achieve high-quality results.”

**k’s job:** larger \(k\) flattens contribution differences between rank 1 and rank 20 (more uniform); smaller \(k\) makes top ranks dominate. OpenSearch: valid `rank_constant` in \([1, 10000]\), default **60**; larger → more uniform, smaller → more weight on top-ranked items. Elastic `rank_constant` default is **60** in product docs (examples sometimes use `1` only to make arithmetic readable).

**Window:** you only fuse the documents that appeared in each list. Elastic `rank_window_size` is how many results **each child retriever** contributes into the fusion pool. If the window is tiny, a document that is #15 on BM25 and #2 on kNN may never meet. Set the window **≥** the per-leg depth you care about; `size` of the search is the final cutoff after fusion.

**Vendor spellings of the same idea:**

| System | Mechanism | Notes |
|--------|-----------|--------|
| Elasticsearch | `retriever.rrf` with ≥2 children | Optional **weights** on children (weighted hybrid example). Also `linear` retriever if you want scores. |
| OpenSearch | `score-ranker-processor` + `hybrid` query | RRF from 2.19; weights must **sum to 1.0** if provided. Alternative: normalization-processor. |
| Weaviate | `rankedFusion` | RRF-style; **not** default since v1.24 (`relativeScoreFusion` is). |
| Qdrant | Query API `"query": { "rrf": {} }` after `prefetch` | Optional `k` and `weights`; alternative **DBSF**. |
| App-side / pgvector | Implement the sum yourself | Required when the store has no hybrid primitive. |

**Relative / min-max score fusion** (Weaviate `relativeScoreFusion`, OpenSearch min_max + arithmetic_mean): keep **margins** (“this BM25 hit crushed the rest”). Sensitive to **outliers** and **list length**. Weaviate docs: with small `limit`, relative fusion is unstable because min/max are taken over a tiny set — they **oversearch** (internal limit 100) then trim. That is an implementation warning for anyone rolling their own min-max.

**DBSF (Qdrant):** normalize using score **distribution** (mean/variance-style) rather than only min/max or ranks. More moving parts; useful when you believe scores are comparable *within* a retriever but want robustness across retrievers.

Huyen’s **ensemble** pattern is exactly “combine these different rankings together to generate a final ranking” — RRF is the default combinator when you lack labels.

---

## Alternatives & Tradeoffs

| Fusion | Pros | Cons |
|--------|------|------|
| **RRF** (`k=60`) | Zero-config; robust across modalities; industry default | Ignores confidence margins; a weak #1 ties a strong #1 |
| Relative / min-max score fusion | Uses score magnitude | Outliers; short lists; Weaviate oversearch caveat |
| Weighted linear (`α·dense + (1-α)·sparse`) | Interpretable knob (Pinecone/Weaviate `alpha`) | Needs labels; **must rescale** (Pinecone sparse vs dense ranges) |
| Elastic `linear` retriever | First-class weighted scores + normalizers | You own calibration |
| DBSF | Distribution-aware | Harder to explain; extra params |
| Learned fusion / LTR | Best in theory with data | Needs judgments; overfit risk |
| Reciprocal rank then **cross-encoder** | RRF for recall union; CE for precision | Week 8 cost; CE still cannot see dropped IDs |

**Weighted RRF:** Elastic and Qdrant allow per-retriever weights. Qdrant: weight 3 vs 1 means rank-3 on the heavy list ≈ rank-1 on the light list; non-overlapping sets return ~3 from the heavy list per 1 from the light. This is still rank-based — not a license to mix raw BM25 with cosine.

---

## Necessity

Without fusion discipline, “hybrid” is a coin flip. Teams report “BM25 made search worse” when they added `0.3 * bm25 + 0.7 * cosine` and BM25’s 12.4 drowned cosine’s 0.81.

Without a large enough fusion window, you implemented **OR of two tiny lists**, not hybrid. Candidate logging must store **pre-fusion ranks** or you cannot debug RRF.

If you skip RRF and jump to learned `alpha` with 12 labeled queries, you will overfit the FAQ slice and miss identifier queries (or the reverse).

---

## Industry Practice

**Common:** vendor default hybrid (often RRF or relative score fusion) with no idea which; `k` left at default; window = `top_k=5`.

**Strong:** Start **RRF `k=60`**; set `rank_window_size` / prefetch `limit` to **50–100** per leg; A/B against relativeScoreFusion **on labeled slices**; only introduce learned `alpha` or LTR with tens+ of labeled queries per failure class. Elastic docs: children execute independently, then RRF combines — aggregations have special notes (read if you facet).

**FDE bar:** compute a 3-document toy example by hand (rank 1/2/3 on each list, `k=60` vs `k=1`) to show why `k=1` over-rewards a single #1. Cite Cormack 2009 when interviewers ask “why 60.”

OpenSearch blog (introducing RRF for hybrid): merge neural, k-NN, and Boolean without score normalization.

---

## Concrete Scenario

Elasticsearch RRF reference — combine BM25 + kNN (or ELSER) via `rrf` retriever, `rank_constant`, `rank_window_size`; worked example shows a hit **without a vector field** still winning from the BM25 leg:

https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  

Also: https://www.elastic.co/guide/en/elasticsearch/reference/8.19/rrf.html  
https://www.elastic.co/docs/reference/elasticsearch/rest-apis/retrievers/rrf-retriever  

OpenSearch RRF:

https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/  
https://docs.opensearch.org/latest/search-plugins/search-pipelines/score-ranker-processor/  
https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/  

Weaviate fusion types:

https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
https://weaviate.io/blog/hybrid-search-fusion-algorithms  

Qdrant:

https://qdrant.tech/documentation/search/hybrid-queries/  

Original paper:

https://doi.org/10.1145/1571941.1572114  
https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/  

Syllabus: implement RRF in the app if the store is pgvector; **log** `k`, window, per-leg ranks, fused score. Redis’s public RRF explainer is a readable secondary on “why not add the scores.”

---

## Open Questions

- Optimal \(k\) as a function of candidate depth and number of rankers?  
- Should a **cross-encoder** replace RRF as the *final* fuse whenever both legs return candidates (CE as fusion, not just reorder of fused list)?  
- Multi-channel RRF (dense + sparse + click/graph/recency)?  
- Dedup of near-duplicate chunks: RRF promotes docs that appear on both lists — duplicates can dominate.  
- Weighted RRF vs query-dependent routing?

---

## Sources

- https://doi.org/10.1145/1571941.1572114  
- https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/  
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/retrievers/rrf-retriever  
- https://www.elastic.co/guide/en/elasticsearch/reference/8.19/rrf.html  
- https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/  
- https://docs.opensearch.org/latest/search-plugins/search-pipelines/score-ranker-processor/  
- https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/  
- https://docs.weaviate.io/weaviate/concepts/search/hybrid-search  
- https://weaviate.io/blog/hybrid-search-explained  
- https://weaviate.io/blog/hybrid-search-fusion-algorithms  
- https://qdrant.tech/documentation/search/hybrid-queries/  
- https://redis.io/blog/reciprocal-rank-fusion/  
- https://huyenchip.com/2024/07/25/genai-platform.html
