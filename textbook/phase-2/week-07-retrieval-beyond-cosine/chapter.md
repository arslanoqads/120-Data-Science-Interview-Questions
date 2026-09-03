# Chapter 7 — Retrieval beyond cosine

> **Phase 2 — RAG Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-2/week-07-retrieval-beyond-cosine/`  
> **Syllabus Build:** Ship **hybrid retrieval** for the FastAPI RAG chatbot—dense ANN (bi-encoder embeddings) **and** BM25 (or equivalent sparse) over the same `chunk_id`s, fused with **RRF** (`k=60` unless evals say otherwise)—and **instrument candidate logging** on every query. Do not stop at cosine-only `top_k`.

---

## Chapter framing

Week 6 decided *what* is stored. Week 7 decides *which stored units are even eligible* for generation and, next week, for reranking. Cosine or inner-product over a single dense embedding is one retriever, not a retrieval *system*. Production IR treats candidate generation as **multi-channel**: cheap high-recall first stages that must put the right chunk into a shortlist of tens to low hundreds.

Chip Huyen’s public platform post frames retrieval as a menu, not a religion: **term-based** (keyword / BM25 / inverted index—fast, cheap, strong baseline), **embedding-based** (more expensive, improvable with better models and indexes), and **hybrid** as the production combination. She describes two composition patterns: **sequential** (cheap retriever then more precise ranking—classical retrieve-then-rerank) and **ensemble** (multiple retrievers in parallel, then combine rankings). Week 7 owns the ensemble + first-stage half; Week 8 owns the expensive pairwise rerank.

Sentence-Transformers’ retrieve & re-rank guide is the shared vocabulary: stage-1 can be **lexical** (Elasticsearch-class BM25) **or** a **bi-encoder**; stage-2 is a **cross-encoder** that scores `(query, document)` jointly. Lexical search misses synonyms; semantic search can miss exactness—that contrast *is* the Week 7 problem, not a footnote.

The five ideas below are one system: **bi-encoders** make ANN retrieval possible; **hybrid** runs dense and BM25 in parallel; **RRF** merges ranked lists when scores are incommensurable; **lexical-precision failures** (SKUs, names, error codes, versions) force an eval slice that FAQs alone cannot see; **store selection** follows filters, hybrid primitives, and ops—not HNSW microbenchmarks. Candidate logging binds them: if you only log the final `top_k` sent to the LLM, you cannot tell whether gold never entered either leg, fusion dropped it, truncation cut it, or generation ignored a present chunk (Week 9).

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) retrieving product runbooks with the same `chunk_id`s Week 6 produced—not cosine-only `similarity_search(k=5)`.

**Default path (synthesis):** index each chunk twice (dense vector + inverted/sparse lexical field, same `chunk_id`) → retrieve independently (e.g. 50–100 per leg) → fuse with RRF (`k=60`) → log both lists and fusion params → keep metadata filters (tenant, version, product) as **hard** constraints → escalate fusion (`alpha`, relative-score, learned sparse) only after labeled slices exist. Cross-encoder rerank is **Week 8**—this week owns recall of the candidate set.

---

### Bi-encoder vs cross-encoder

* **Fundamentals:**  
  A **bi-encoder** (Sentence Transformer dual-encoder, “embedding model”) maps query and document **independently** into a shared vector space. Similarity is cosine or dot product. Documents are embedded **once at ingest** and stored; at query time you embed the query and run exact or approximate nearest neighbor (ANN) search (HNSW, IVF, DiskANN, and similar). Corpus size does not multiply Transformer passes at query time—that independence is the point.

  A **cross-encoder** concatenates the `(query, document)` pair (typically `[CLS] query [SEP] document [SEP]`) and runs **full self-attention across both sequences**. The head outputs a scalar relevance score (often mapped to `[0,1]`). It does **not** produce an independently indexable document embedding: every document token’s representation depends on the query tokens, so you cannot precompute “the document vector.”

  Sentence-Transformers documents the split explicitly. Bi-encoders serve **information retrieval, semantic search, clustering**—anything that needs a vector you can index or compare in bulk. Cross-encoders achieve **higher pairwise quality** (SBERT lineage / paper 1908.10084) but “do not produce embeddings we could e.g. index or efficiently compare using cosine similarity.” Their clustering example: comparing 10,000 sentences with a cross-encoder would require ~50 million pair inferences (~65 hours); a bi-encoder embeds each sentence once (~5 seconds) then clusters in vector space.

  **Retrieve & Re-Rank** (official SBERT application guide): first retrieve a large list (e.g. **~100** hits) with lexical search **or** a bi-encoder; then a CrossEncoder scores each `(query, hit)`. Scoring thousands or millions of pairs would be too slow—the retriever exists to bound that work. Pinecone’s rerankers essay restates the information-theory intuition: a bi-encoder must **compress** a document into one vector *without seeing the query*, so query-salient meanings are averaged away; a reranker reads the raw pair at query time.

  **ColBERT / late interaction** sits between the two: token-level MaxSim-style interactions with **precomputable** document token vectors—higher quality than a single vector, cheaper than full cross-attention over the corpus. Treat it as an alternative first-stage or mid-stage, not as a reason to skip hybrid lexical signals. Huyen’s **sequential** pattern is this architecture in ops language: cheap retriever fetches candidates; a more precise, more expensive mechanism orders them. In RAG, rank still matters (lost-in-the-middle), but inclusion in the window often dominates search-style nDCG.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Bi-encoder + ANN only | Millisecond corpus search; precomputable index | Irrelevant near-neighbors; lexical blur; weak fine ranking | Stage-1 alone is incomplete for production RAG |
  | Cross-encoder over full corpus | Best pairwise relevance in theory | Impractical latency/cost at corpus scale | Never as sole retriever |
  | Retrieve ~100 then cross-encode (SBERT) | Quality where it matters; bounded CE work | Stage-1 must recall gold; CE latency on `k` | Industry default; CE wiring is Week 8 |
  | Late interaction (ColBERT-class) | Between bi and full cross; still ANN-able | Token-vector storage; implementation complexity | Stage-1 or mid-stage alternative |
  | Tiny local bi-encoder (`all-MiniLM`) | Cheap ingest/query | Weaker multilingual/domain | Prototypes; measure against domain |
  | API embed (`text-embedding-3-*`, Cohere, Voyage) | Quality/ops outsourced | Cost; less tokenizer↔BM25 analyzer control | Common production stage-1 |
  | Domain-tuned bi-encoder (MS MARCO / tickets) | Better in-domain recall | Training/eval burden | After baseline hybrid proves gaps |

  Asymmetric search (SBERT semantic-search docs): questions vs passages may need `encode_query` / `encode_document` (E5-style prefixes). Using one pooling path for both is a silent quality loss—still a bi-encoder issue. Stage-1 `k` is a cost control: too small → gold never reaches a future CE; too large → CE latency SLO burn. Common pattern: retrieve 80–100 (hybrid, logged), CE the top 20–50 in Week 8. If CE `k` is 8, you are not running retrieve-and-rerank—you are running “slightly better cosine.”

* **Failure Modes:**  
  - Using only cross-encoders on a large corpus times out and cannot serve multi-tenant RAG SLOs.  
  - Using only bi-encoders leaves obvious irrelevant near-neighbors in the `top_k` stuffed into the prompt.  
  - Teams “add a reranker” on `k=5` and conclude rerankers don’t work—the gold was never a candidate (Pinecone: retriever must get the answer into top-k).  
  - Cosine-only stage-1: a perfect cross-encoder cannot recover SKU/error-code misses (see lexical-precision failures).  
  - Asymmetric query/document encoders wired with a single encode path—silent recall loss.  
  - Overwriting stage-1 candidate logs when Week 8 reranks—loses the ability to blame stage-1 vs CE.

* **Average vs. Strong Engineer:**  
  **Average:** `all-MiniLM` or a vendor embedding API + cosine `top_k=4`. No awareness that the embedding model is a bi-encoder; no plan for a 50–100 candidate API.  
  **Strong:** Domain-appropriate bi-encoder (or API embed) → ANN top-50–100, often **hybrid** → cross-encoder / Cohere Rerank / BGE-reranker in Week 8. Sets `k` from **recall@k of stage-1 on a golden set**, not from context-window folklore. Logs stage-1 hits **before** rerank: `bi_encoder_model`, `ann_k`, `ann_metric`, `candidate_ids_stage1`. FDE bar: draw independent towers vs joint Transformer; quote SBERT’s clustering 65h vs 5s; know MS MARCO-trained bi- and cross-encoder siblings agree on the relevance *task* but do not share a vector space.

* **Worked Example:**  
  Deployment Copilot exposes a retriever API this week: `search(query) -> candidates` with per-leg scores. For a FAQ query “how do I reset MFA?”, the bi-encoder ANN returns ~80 near neighbors (paraphrases of two-factor / MFA runbooks). Those hits may include irrelevant neighbors in the same product area. The API returns the full stage-1 list with ranks and scores—**not** only the five chunks that will eventually enter the prompt. Week 8 will call `CrossEncoder.predict` (or a vendor rerank) against that same candidate log schema; this week you do not ship CE as the only retriever, but you build the candidate set as if CE will consume ~50–100 IDs.

  Rough latency sketch from research: bi-encoder query embed ~5–30 ms (local MiniLM) to ~50–200 ms (remote API); ANN/hybrid fetch of 100 IDs typically <20–80 ms if indexed; cross-encoder is one Transformer forward per pair (batched)—tens of ms on GPU for MiniLM-L6 on 100 pairs, hundreds of ms–seconds on CPU, plus network for vendor APIs.

* **Apply It:**  
  1. Confirm the flagship embedder is used as a **bi-encoder**: docs embedded at ingest; query embedded at request time; ANN (or exact NN) for stage-1.  
  2. Expose a candidate API that returns **~50–100** hits (hybrid once other concepts land), not prompt-sized `k=5`.  
  3. Persist `bi_encoder_model`, `ann_k`, `ann_metric` (cosine vs ip), and `candidate_ids_stage1` per query.  
  4. Leave CrossEncoder / vendor rerank wiring for Week 8 against the **same** log schema (`rerank.ids[]` / `rerank.scores[]` appended, not overwritten).  
  5. If using asymmetric models (E5-style), call `encode_query` / `encode_document` (or equivalent prefixes)—do not reuse one path for both.  
  6. Size stage-1 `k` from golden-set **recall@k**, not from “how many chunks fit in the prompt.”

---

### Hybrid search (dense + BM25)

* **Fundamentals:**  
  **Hybrid search** runs a **dense** (semantic / embedding) retriever and a **sparse/lexical** retriever in parallel, then **fuses** the ranked lists into one. Dense captures paraphrase, synonymy, and “the user did not use our heading vocabulary.” Lexical (BM25/BM25F, or learned sparse such as SPLADE / Elastic **ELSER**) captures **exact tokens**: SKUs, error codes, proper names, version strings, config keys.

  Sentence-Transformers’ retrieve & re-rank page contrasts the two first stages you might use *before* a cross-encoder: lexical search looks for literal matches and “will not recognize synonyms, acronyms or spelling variations”; semantic search encodes the query into vector space and retrieves nearby document embeddings. Hybrid is the refusal to pick only one of those first stages.

  Chip Huyen (public platform post): a production retrieval system typically combines several approaches; combining term-based and embedding-based retrieval is **hybrid search**. She distinguishes **sequential** (cheap term filter then kNN/rerank among survivors) from **ensemble** (multiple retrievers rank in parallel, then combine). Week 7’s default is **ensemble**; sequential is valid when BM25 is an excellent high-recall gate—but gold that BM25 never surfaces never recovers.

  Engine primitives (name yours in reviews):

  | System | Hybrid primitive (research) |
  |--------|----------------------------|
  | Weaviate | Vector + BM25; `alpha` (default **0.75**—0 = keyword, 1 = vector); `fusionType` = `relativeScoreFusion` (default since **v1.24**) or `rankedFusion` (RRF-style) |
  | Elasticsearch | Full-text + vector in one request; **recommend RRF**; `rrf` wrapping `standard` + `knn` (optional ELSER/sparse); also `linear` when you want weighted scores |
  | OpenSearch | Hybrid query + **search pipeline**: normalization-processor (score-based) **or** score-ranker-processor RRF (from 2.19) |
  | Qdrant | Named vectors (dense + sparse); Query API `prefetch` then `rrf` or **DBSF** |
  | Pinecone | Single index: dense `values` + `sparse_values`; metric **`dotproduct`**; client-side `alpha` scaling (`hybrid_score_norm`) because `index.query` has no `alpha` kwarg |
  | pgvector | Vectors in Postgres; BM25 via `tsvector`/`tsquery` (or sidecar); **fuse in the application** |

  Learned sparse (ELSER, SPLADE) is still “lexical-shaped” (weighted terms in a huge vocabulary) but can match expanded synonyms better than raw BM25. Elastic can treat BM25 + ELSER + dense as a three-child RRF tree. Analyzer choices **are** the lexical leg: stemming identifiers into mush, splitting `SKU-7F2A`, lowercasing vs keyword fields. Hybrid quality is often an **ingest** bug (Week 6 metadata + this week’s analyzer), not a fusion bug. Same `chunk_id` must appear in both indexes—never fuse “document 12 from BM25” with a differently chunked dense hit.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Dense cosine only | Demo speed; one index; synonymy | Identifier queries; rare tokens; version pins | Throwaway demos only |
  | BM25 only | Exact tokens; cheap ops; explainability | Paraphrase / “how do I…” FAQs | Huyen’s suggested **first** experiment; identifier-heavy corpora |
  | Dense + BM25 + RRF | Robust default; little tuning | Ignores score margins; two indexes | **Syllabus path** |
  | Dense + BM25 + weighted `alpha` / relativeScoreFusion | Uses score magnitude; tunable | Needs labels; sensitive to list length/outliers | After labeled slices exist |
  | Dense + learned sparse | Often stronger lexical+semantic | Model ops, inference cost, version pinning | Escalate from classic BM25 with evidence |
  | Sequential term-then-dense | Cheap candidate cut | Catastrophic if gold has no lexical overlap | When BM25 is a trusted gate |
  | Client EnsembleRetriever vs server hybrid | Portability vs one round-trip | Latency/consistency tradeoffs | pgvector → client RRF; ES/Qdrant → server |

* **Failure Modes:**  
  - Pure cosine systematically misses queries where the right answer hinges on an **exact rare token** embeddings smooth away.  
  - Skipping fusion discipline: ad-hoc `sum(0.5*minmax(bm25)+0.5*cosine)` makes A/B tests measure your scaler, not hybrid.  
  - Sequential BM25-then-dense: gold without lexical overlap never recovers.  
  - Analyzer destroys identifiers (`ECONNRESET` stemmed/split) → BM25 leg is theater.  
  - Different chunking between dense and lexical indexes → fusion joins nonsense.  
  - Over-investing in a dedicated vector DB before BM25 exists (Huyen: don’t start too complex / don’t agonize over vectordb when term-based might already work).

* **Average vs. Strong Engineer:**  
  **Average:** Vectordb cosine only in prototypes; “we’ll add BM25 later.”  
  **Strong:** Hybrid as **default** for technical corpora; intentional BM25 field analyzers (identifiers as `keyword` or minimal analysis); tune fusion **after** measuring failure classes (semantic vs lexical slices); logs both legs. FDE bar: name the engine’s actual hybrid primitive (ES `rrf`, OS hybrid + pipeline, Weaviate `alpha`+fusionType, Qdrant prefetch+fusion, Pinecone sparse+dense `dotproduct`, pgvector DIY). Elastic: `rank_window_size` must be large enough that each child actually contributes documents into RRF.

* **Worked Example:**  
  Same product runbooks as Week 6. Index each chunk’s embedding **and** a BM25 field with an analyzer that keeps identifiers (do not stem `ECONNRESET` into mush). On query: dense top-80 + BM25 top-80 over the same `chunk_id`s, then fuse (next concept) to ~40. A semantic query (“reset MFA”) leans on dense; `ERR_OS_4092` and `widget SKU-7F2A` lean on BM25; both legs contribute diversity so you are not stuck with eighty near-duplicate semantic neighbors. Metadata filters (`tenant`, `product`, `version`) are **hard** predicates applied to both legs—not “hope cosine notices.”

* **Apply It:**  
  1. Index every chunk twice with the **same** `chunk_id`: dense vector + BM25/`tsvector`/sparse field.  
  2. Retrieve independently (syllabus sketch: 50–100 per leg; concrete scenario often uses top-80).  
  3. Configure analyzers so SKUs, error codes, and version strings survive as matchable tokens (`keyword` or minimal analysis where needed).  
  4. Apply tenant/product/version filters as hard constraints on both legs.  
  5. Prefer parallel dense + BM25 → RRF before sequential term-then-dense or learned `alpha`.  
  6. Log both ranked ID lists and raw scores before fusion (see build checklist).

---

### Reciprocal Rank Fusion (RRF)

* **Fundamentals:**  
  **Reciprocal Rank Fusion** merges multiple ranked lists **without calibrating score scales**. For each document \(d\):

  \[
  \mathrm{RRF}(d) = \sum_{r \in \text{rankers}} \frac{1}{k + \mathrm{rank}_r(d)}
  \]

  Ranks are **1-based**. Documents missing from a list contribute **0** from that list. The constant \(k\) (often `rank_constant`) is commonly **60**, the value Cormack, Clarke, and Buettcher used and recommended in **SIGIR 2009** (*“Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods”*). They showed unsupervised RRF combining TREC runs beat individual systems and Condorcet Fuse.

  **Why ranks, not scores:** BM25 scores are typically unbounded positives whose magnitude depends on query length, field boosts, and IDF. Cosine lives in \([-1,1]\) (often ~0.2–0.8 in practice). Inner product / unnormalized dense scores are another scale; ELSER/SPLADE yet another. **Naïve sums and uncalibrated weighted averages are invalid.** RRF throws scores away and keeps order. Elastic’s RRF docs: RRF requires **no tuning**, and the different relevance indicators **do not have to be related** to each other to achieve high-quality results.

  **k’s job:** larger \(k\) flattens contribution differences between rank 1 and rank 20 (more uniform); smaller \(k\) makes top ranks dominate. OpenSearch: valid `rank_constant` in \([1, 10000]\), default **60**. Elastic product docs also default `rank_constant` to **60** (examples sometimes use `1` only to make arithmetic readable).

  **Window:** you only fuse documents that appeared in each list. Elastic `rank_window_size` is how many results **each child retriever** contributes into the fusion pool. If the window is tiny, a document that is #15 on BM25 and #2 on kNN may never meet. Set the window **≥** the per-leg depth you care about; search `size` is the final cutoff after fusion.

  Vendor spellings of the same idea: Elasticsearch `retriever.rrf` (≥2 children; optional weights); OpenSearch `score-ranker-processor` + hybrid query (RRF from 2.19; weights sum to 1.0 if provided); Weaviate `rankedFusion` (RRF-style; **not** default since v1.24—`relativeScoreFusion` is); Qdrant Query API `"query": { "rrf": {} }` after `prefetch`; app-side / pgvector—implement the sum yourself.

  **Relative / min-max score fusion** (Weaviate `relativeScoreFusion`, OpenSearch min_max + arithmetic_mean) keeps **margins** (“this BM25 hit crushed the rest”) but is sensitive to outliers and list length. Weaviate docs: with small `limit`, relative fusion is unstable because min/max are taken over a tiny set—they **oversearch** (internal limit 100) then trim. **DBSF** (Qdrant) normalizes using score distribution rather than only min/max or ranks. Huyen’s **ensemble** pattern is exactly “combine these different rankings”—RRF is the default combinator when you lack labels.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | RRF (`k=60`) | Zero-config; robust across modalities; industry default | Ignores confidence margins; weak #1 ties strong #1 | **Syllabus default** |
  | Relative / min-max score fusion | Uses score magnitude | Outliers; short lists; Weaviate oversearch caveat | When margins matter and lists are deep enough |
  | Weighted linear (`α·dense + (1-α)·sparse`) | Interpretable knob (Pinecone/Weaviate `alpha`) | Needs labels; **must rescale** (Pinecone sparse vs dense ranges) | After labeled failure-class data |
  | Elastic `linear` retriever | First-class weighted scores + normalizers | You own calibration | When you intentionally want scores |
  | DBSF (Qdrant) | Distribution-aware | Harder to explain; extra params | When within-retriever scores are believable |
  | Learned fusion / LTR | Best in theory with data | Judgments; overfit risk | Mature relevance teams |
  | Weighted RRF | Still rank-based; tilts toward a child | Not a license to mix raw BM25 with cosine | Elastic/Qdrant when one leg is systematically better |
  | RRF then cross-encoder | Recall union + CE precision | Week 8 cost; CE cannot see dropped IDs | Next week’s precision stage |

* **Failure Modes:**  
  - “Hybrid” as `0.3 * bm25 + 0.7 * cosine`: BM25’s 12.4 drowns cosine’s 0.81; teams conclude “BM25 made search worse.”  
  - Fusion window = `top_k=5`: you implemented **OR of two tiny lists**, not hybrid.  
  - Jumping to learned `alpha` with ~12 labeled queries overfits the FAQ slice and misses identifiers (or the reverse).  
  - Candidate logs omit **pre-fusion ranks** → cannot debug RRF.  
  - Near-duplicate chunks: RRF promotes docs that appear on both lists—duplicates can dominate.  
  - `[NEEDS MORE RESEARCH]` for an official syllabus rule on deduplicating near-duplicate chunks before vs after RRF beyond noting the failure mode.

* **Average vs. Strong Engineer:**  
  **Average:** vendor default hybrid with no idea whether it is RRF or relative score fusion; `k` left at default; window = final `top_k=5`.  
  **Strong:** Start **RRF `k=60`**; set `rank_window_size` / prefetch `limit` to **50–100** per leg; A/B against relativeScoreFusion **on labeled slices**; introduce learned `alpha` or LTR only with tens+ of labeled queries per failure class. FDE bar: compute a 3-document toy by hand (ranks 1/2/3 on each list, `k=60` vs `k=1`) to show why `k=1` over-rewards a single #1; cite Cormack 2009 when interviewers ask “why 60.”

* **Worked Example:**  
  Two legs return overlapping IDs. Document A is rank 1 on BM25 and absent from dense → contributes \(1/(60+1)\) from BM25 only. Document B is rank 2 on dense and rank 5 on BM25 → sum of both reciprocals. With `k=60`, the gap between rank 1 and rank 5 is modest; with `k=1`, a single #1 dominates. Elasticsearch’s RRF reference shows a hit **without a vector field** still winning from the BM25 leg—exactly the identifier rescue Deployment Copilot needs. Syllabus path: dense top-80 + BM25 top-80 → RRF fuse to 40 with `k=60`; log `fusion.method`, `fusion.k`, `fusion.window`, per-leg ranks, and fused ranks. If the store is pgvector, implement the sum in-process; if ES/Qdrant/Weaviate, use the native primitive but still log pre-fusion lists.

* **Apply It:**  
  1. Implement RRF (app-side or engine) with **`k=60`** unless a labeled eval says otherwise.  
  2. Set each leg’s contribution window to **≥** per-leg depth (50–100), not to the final prompt `k`.  
  3. Never add raw BM25 and cosine without a documented normalizer; prefer RRF until labels exist.  
  4. Log `fusion.method`, `fusion.k`, `fusion.window`, `dense.ranks[]`, `lexical.ranks[]`, `fused.ids[]`.  
  5. Hand-check a tiny three-document example with `k=60` vs `k=1` before shipping.  
  6. Defer weighted `alpha` / relativeScoreFusion / LTR until semantic **and** lexical-precision slices exist.

---

### Lexical precision failures (why pure cosine fails)

* **Fundamentals:**  
  Dense embeddings optimize **semantic neighborhoods**. Training (contrastive pairs, MS MARCO, web query-title) rewards putting paraphrases nearby. That objective **blurs** distinctions production users type when they already know the key:

  - **SKUs / part numbers** (`SKU-7F2A`, `PN-4418-B`) — rare, high-IDF, often split or character-noised by WordPiece/BPE.  
  - **Proper names** (customer org, product family, internal service `payments-gw`) — collisions with common words (`Apple` fruit vs company).  
  - **Error codes** (`ECONNRESET`, `ERR_OS_4092`, HTTP `429` vs the prose “too many requests”).  
  - **Version pins** (`8.18` vs `9.0`, `OpenSearch 2.19`) — numeric tokens are famously weak in general text embedders.  
  - **Config keys / legal citations** (`max_scan_tuples`, `26 U.S.C. § 501`).

  Lexical methods excel **exactly** there: inverted indexes retrieve the posting list for the rare term. Dense methods excel on “how do I reset MFA?” when the doc says “turn two-factor authentication off.” Failure is **asymmetric**: semantic search returns **fluent wrong neighbors** (same product area, wrong identifier). Users experience this as hallucination even when the LLM faithfully read the retrieved chunk.

  Sentence-Transformers: lexical search finds **literal** matches and misses synonyms; semantic search recognizes synonyms/acronyms/spelling variation. The dual is rarely printed: semantic search **cannot be trusted** as the sole method when the query *is* a lexical match. A semantic-only first stage **never lists** the SKU doc for a future cross-encoder to save.

  Huyen (platform): term-based retrieval is the cheap, strong baseline; hybrid is production. Sequential pattern: fetch all docs containing a token, **then** vector-rank among them—recognition that the **token** is the recall key. Pitfalls post: try **term-based** before agonizing over a vectordb. Elastic/OpenSearch hybrid docs and Elastic RRF examples include documents that **win from BM25 despite missing vectors**. Tokenization is part of the failure: if `SKU-7F2A` becomes `sku`, `-`, `7`, `##f2`, `##a`, the embedding is a smear of frequent subwords; BM25 on a `keyword` field still has a unique posting.

  Eval implication: a golden set of only FAQ paraphrases **cannot detect** this class. You need an explicit **lexical-precision slice**.

* **The Alternatives:**  

  | Mitigation | What you gain | What it costs | When it fits |
  |------------|---------------|---------------|--------------|
  | Hybrid BM25 + dense + RRF | Most identifier queries | Analyzer must keep the token | **First-line syllabus fix** |
  | Metadata / keyword filters (`product_id`, `version`, `sku`) | Structured exactness | Users don’t always fill facets | When UI/query provides structure |
  | Query classification → lexical-only for “code-like” queries | Low latency; no dense dilution | Classifier errors | Optional routing after always-hybrid baseline |
  | Learned sparse (ELSER/SPLADE) | Synonym expansion *and* term weights | Still not a pure `keyword` field for SKUs | Lexical-leg upgrade |
  | Character / n-gram indexes | Typos, partial SKUs | Noise; index size | Partial-match SKU search |
  | Cross-encoder reranker | Sees raw tokens of **candidates** | Cannot help if stage-1 dropped the doc | Week 8 precision—not a stage-1 substitute |
  | Bigger / instruct-tuned embeds | May reduce *some* lexical misses | Do not assume they retire BM25 | Measure; keep BM25 until proven |
  | Put identifiers in **chunk text** (Week 6) | Embeddings at least see the string | Still smoothed; still want BM25 | Coupled with hybrid indexing of metadata fields |

  Do **not** “fix” this only by raising `top_k` on cosine: the SKU doc may sit at rank 400 in embedding space, behind every semantically adjacent paragraph.

* **Failure Modes:**  
  - FAQ demos look great; ticket deflection on `ECONNRESET`, `SKU-1842`, `OpenSearch 2.19` collapses.  
  - FAQ-dominated nDCG makes hybrid A/Bs look flat; finance kills BM25 as “complexity.”  
  - Chunks strip the SKU into metadata-only and embed body text without it → **both** legs can fail unless metadata fields are indexed for BM25 and/or included in embed text.  
  - Candidate logs without `query_class` → cannot report **recall@k by slice**.  
  - Raising cosine `top_k` never surfaces the identifier doc; CE never sees it.  
  - Regex boosts added as one-offs after launch instead of a first-class eval slice.

* **Average vs. Strong Engineer:**  
  **Average:** Discovers the failure in production; adds regex boosts; golden set is FAQ paraphrases only.  
  **Strong:** Builds an eval slice of lexical-precision queries (IDs, errors, versions, names) **alongside** semantic paraphrases; **gates releases on both slices**; instruments which **leg** retrieved the gold (BM25-only vs dense-only vs both). Elasticsearch “Vector Isn’t Enough” lab narrative uses adversarial exact-match queries to teach hybrid + RRF. FDE bar: show before/after for `ECONNRESET`—cosine-top-10 vs BM25-top-10 vs RRF; explain `keyword` vs standard analyzer on a whiteboard. Huyen: for many identifier-heavy corpora, BM25 **is** the product until FAQ volume justifies dense.

* **Worked Example:**  
  Deployment Copilot’s golden set includes: “reset MFA” (semantic), `ERR_OS_4092` (error code), `widget SKU-7F2A` (SKU), `v8.18 vs v9.0` (version). Gate the week on **recall@40 on both slices**, not only nDCG on FAQs. Syllabus guidance: add ≥10 queries of `{sku, error_code, version, person_or_org_name}`; require recall@40 ≥ target **on that slice** before calling Week 7 done. Log `query_class` as `semantic` | `identifier` | `mixed`. For `ECONNRESET`, cosine neighbors may be generic connection-troubleshooting prose; BM25 returns the runbook whose body (or keyword field) contains the exact token; RRF keeps that ID in the fused candidate set for Week 8.

* **Apply It:**  
  1. Add a **lexical-precision** golden slice (≥10 queries covering SKU, error code, version, name) beside semantic paraphrases.  
  2. Gate Week 7 on recall@40 (or your fused cutoff) **on both slices**.  
  3. Ensure Week 6 chunks keep identifiers in indexable text and/or BM25 metadata fields.  
  4. Classify queries (`query_class`) in candidate logs for slice metrics.  
  5. Prefer hybrid + RRF over raising cosine `top_k` or hoping Week 8 CE will invent missing candidates.  
  6. When debugging a miss, check which **leg** saw gold before blaming the LLM.

---

### Vector database selection (pgvector vs dedicated vs hybrid-native)

* **Fundamentals:**  
  Three practical **buckets**—not a leaderboard of HNSW QPS:

  1. **pgvector (Postgres extension)** — vectors **beside** relational data; ACID, PITR, JOINs, RLS, one operational plane if you already run Postgres. Official README: exact and approximate NN; types `vector`, `halfvec`, `bit`, `sparsevec`; distances `<->` L2, `<#>` negative inner product, `<=>` cosine, `<+>` L1, plus Hamming/Jaccard for binary. Indexes: **HNSW** (better speed-recall, slower build, more memory; can build empty) and **IVFFlat** (faster build, less memory, needs data for k-means `lists`). Operator class must match the query operator (`vector_cosine_ops` with `<=>`, not `<->`). Cosine **similarity** is `1 - (embedding <=> query)`. Hybrid BM25 is **not** native: use `tsvector`/`tsquery` (or a sidecar) and **fuse in the application** (RRF). Filtered ANN historically **post-filters** HNSW candidates → **fewer than LIMIT** rows; **0.8.0** added **iterative index scans** (`hnsw.iterative_scan` = `strict_order` | `relaxed_order`, `hnsw.max_scan_tuples` default 20000) so the scan expands until enough rows match `WHERE` or a cap. Supabase/Neon docs reiterate the short-result filtered-search footgun.

  2. **Dedicated vector DBs** (Qdrant, Weaviate, Milvus, Pinecone, …) — ANN + **payload filters** as a first-class product; often **native sparse/hybrid**; scale and filtered-search performance beyond a general-purpose DB’s comfort zone. You buy (or operate) a second system and a **sync pipeline** from OLTP/object storage.

  3. **Hybrid-native search engines** (Elasticsearch, OpenSearch) — decades of **BM25/BM25F**, analyzers, synonyms, aggregations, plus kNN/semantic + **RRF retrievers / hybrid queries**. Attractive if the team already operates ES for logs/search. Vector features are **version-sensitive**; cluster ops are real.

  Huyen (pitfalls): **agonize over what vector database to use** when a simple **term-based** solution that **doesn’t require a vectordb** works—“start too complex.” Platform post: retrieval quality comes from **combining mechanisms**, not from the brand of ANN. Selection is **filters, hybrid, scale, consistency, team ops**. Sync tax applies whenever you dual-write embeddings vs OLTP: exactly-once chunk IDs; rebuilds when the embed model changes. pgvector avoids a second database but not embed rebuilds. Multi-tenancy: Postgres RLS + `tenant_id` btree vs payload filters on HNSW—**filter selectivity** (post-filter vs pre-filter) often dominates raw QPS tables.

* **The Alternatives:**  

  | Option | Choose when | Watch outs |
  |--------|-------------|------------|
  | **pgvector** | Existing Postgres; moderate scale (often cited informally as low–mid millions if hardware/index fit); need joins/transactions/RLS | DIY hybrid; filtered ANN needs iterative scans; HNSW RAM; vacuum/index build windows |
  | **Qdrant** | Filtered vector performance; self-host control; native sparse/hybrid Query API | Ops (or cloud cost); second store to sync |
  | **Weaviate** | Built-in hybrid BM25+vector; GraphQL/modules | Ops/schema; fusion default changed v1.24 |
  | **Pinecone** | Zero-ops managed; speed to prod; hybrid sparse+dense | Lock-in; cost at volume; `dotproduct`+client `alpha`; less Lucene-style analyzer control |
  | **Elasticsearch** | Already ES; RRF + BM25 + kNN + ELSER in one engine | Cluster ops; license/distro; vector feature matrix by version |
  | **OpenSearch** | ES-like, Apache 2.0 lineage; hybrid query + pipelines | Plugin/version matrix; hybrid pagination caveats in docs |
  | **Milvus / Zilliz** | Very large scale | Distributed ops |
  | **FAISS/Chroma in-process** | Notebooks, tests | Not multi-tenant production by itself |
  | **pgvectorscale / DiskANN** | Close dedicated-engine gap on Postgres | Evolving—measure on **your** filtered queries |

* **Failure Modes:**  
  - ETL to a vectordb you didn’t need, or billion-scale ANN through Postgres until latency SLOs break.  
  - **Fake** hybrid (cosine-only) because the dedicated store was sold as “the RAG database.”  
  - Putting RAG on ES without anyone who understands analyzers → worse BM25 than `rank_bm25` in the app.  
  - Skipping iterative scans on pgvector: tenant filters **silently under-return**—looks like “RAG missed the doc” (Week 9) when the index never visited it.  
  - Store choice on HNSW microbenchmarks instead of hybrid + filter + ops constraints.  
  - Wrong operator class (`<=>` with L2 ops) → silently wrong neighbors.

* **Average vs. Strong Engineer:**  
  **Average:** Chroma/FAISS in notebooks → Pinecone or Weaviate on first deploy → surprise invoice or surprise ops; cosine-only because “we have a vector DB.”  
  **Strong:** Default **pgvector** if Postgres + modest vectors + SQL filters/joins + willingness to RRF in app (or add OpenSearch later for lexical). Move to **Qdrant/Weaviate/Milvus** when filtered recall/latency or native hybrid dominate. Use **Elasticsearch/OpenSearch** when lexical relevance (synonyms, BM25F field boosts, facets) is already a competency or the corpus **is** the search platform. Measure **end-to-end RAG quality and p95**, not only ANN QPS. FDE bar: explain operator classes; why Pinecone hybrid wants `dotproduct`; why Weaviate `alpha=0.75` is not Elastic RRF; why OpenSearch needs a **pipeline** for hybrid combination; why “just pgvector” still needs `tsvector` for Week 7.

* **Worked Example:**  
  Deployment Copilot already uses Postgres for app data. Week 7 implements hybrid **in-process RRF** on pgvector + `tsvector` **before** introducing a dedicated engine: store embeddings with a matching HNSW operator class; index runbook text (and identifier fields) as `tsvector`; query both; fuse with `k=60`; enable iterative scans so tenant `WHERE` clauses do not silently shrink results below `LIMIT`. Log `store`, `embed_model`, and `index_names` next to candidate lists. Only if filtered recall/latency or analyzer needs outgrow Postgres do you justify Qdrant/Weaviate/ES—and you still keep dual-leg logging so a store swap is measurable.

* **Apply It:**  
  1. If the chatbot already uses Postgres, implement Week 7 hybrid with **pgvector + `tsvector` + app-side RRF** before a vendor bake-off.  
  2. Match pgvector **operator class** to the distance operator; know cosine similarity = `1 - (embedding <=> query)`.  
  3. Enable **iterative index scans** (or equivalent) for filtered ANN; verify tenant filters return full `LIMIT`.  
  4. If choosing ES/OS/Weaviate/Qdrant/Pinecone, name the **hybrid primitive** and log its parameters.  
  5. Prove BM25 value on your lexical-precision slice before agonizing over vectordb brand (Huyen).  
  6. Persist `store`, `embed_model`, `index_names` on every candidate log for model-swap debugging.

---

## Week 7 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Dual index:** Same `chunk_id` in dense ANN and BM25/`tsvector`/sparse; analyzers keep identifiers.  
2. **Parallel retrieve:** Dense top-50–100 and lexical top-50–100 (concrete scenario often 80/80); hard metadata filters on both.  
3. **Fuse with RRF:** `k=60` unless evals say otherwise; window ≥ per-leg depth; fused cutoff e.g. 40 toward generate/Week 8.  
4. **Instrument candidate logging** on every query (JSON or OTel attributes + joinable `retrieval_id`):

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
   | Stage-1 extras | `bi_encoder_model`, `ann_k`, `ann_metric` |

5. **Eval gate:** Semantic paraphrase slice **and** lexical-precision slice; recall@fused-cutoff (e.g. recall@40) on **both**.  
6. **Store path:** pgvector + app RRF if Postgres already; else use the engine’s hybrid/RRF primitive—still log both legs.  
7. **Week 8 boundary:** Candidate API of size ~50–100; do **not** overwrite Week 7 logs when rerank lands—append `rerank.*`. Cross-encoder is not this week’s sole retriever.

When those steps are true, Week 7 is done in the syllabus sense: Deployment Copilot no longer pretends cosine-only `top_k` is a retrieval system, and every miss is attributable to a leg, fusion, filter, or (later) generate.

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

## Compilation notes

- All concept sections above are grounded in `research/phase-2/week-07-retrieval-beyond-cosine/` (`00`–`05` plus README).  
- One `[NEEDS MORE RESEARCH]` marker appears under RRF failure modes: research notes near-duplicate dominance under RRF as an open concern but does not prescribe a syllabus-standard dedupe policy.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.  
- Chip Huyen material is from public blog posts only (`genai-platform`, `ai-engineering-pitfalls`), matching the research corpus constraint.
