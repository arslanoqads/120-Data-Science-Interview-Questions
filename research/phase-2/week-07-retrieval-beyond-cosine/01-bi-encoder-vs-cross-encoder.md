# 01 — Bi-encoder vs cross-encoder architectures

> Week 7 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

A **bi-encoder** (Sentence Transformer dual-encoder, “embedding model”) maps query and document **independently** into a shared vector space. Similarity is cosine or dot product. Documents are embedded **once at ingest** and stored; at query time you embed the query and run exact or approximate nearest neighbor (ANN) search (HNSW, IVF, DiskANN, etc.). That independence is the entire point: corpus size does not multiply Transformer passes at query time.

A **cross-encoder** concatenates the `(query, document)` pair (typically `[CLS] query [SEP] document [SEP]`) and runs **full self-attention across both sequences**. The head outputs a scalar relevance score (often mapped to `[0,1]`). It does **not** produce an independently indexable embedding for the document. You cannot precompute “the document vector” because the representation of every document token depends on the query tokens.

Sentence-Transformers documents this split explicitly. Bi-encoders are for **information retrieval, semantic search, clustering** — anything that needs a vector you can index or compare in bulk. Cross-encoders achieve **higher pairwise quality** (their paper 1908.10084 / SBERT lineage) but “do not produce embeddings we could e.g. index or efficiently compare using cosine similarity.” Clustering 10,000 sentences with a cross-encoder would require ~50 million pair inferences (~65 hours in their example); a bi-encoder embeds each sentence once (~5 seconds) then clusters in vector space.

**Retrieve & Re-Rank** (official SBERT application guide): given a query, first retrieve a large list (e.g. **100** hits) with either **lexical search** (Elasticsearch) or a **SentenceTransformer bi-encoder**; those hits may include irrelevant neighbors; then a **CrossEncoder** scores each `(query, hit)` and the user sees the reordered list. Scoring “thousands or millions of (query, document)-pairs would be rather slow,” so the retriever exists to bound the cross-encoder’s work.

Pinecone’s rerankers essay restates the information-theory intuition: a bi-encoder must **compress** a document into one vector *without seeing the query*, so meanings that would only be salient given this query are averaged away. A reranker reads the raw pair at query time — less compression, more compute.

**ColBERT / late interaction** (and SBERT’s newer multi-vector encoders) sit between the two: token-level MaxSim-style interactions with **precomputable** document token vectors. Higher quality than a single vector, cheaper than full cross-attention over the corpus. Treat it as an alternative first-stage or mid-stage, not as a reason to skip hybrid lexical signals.

Huyen’s public platform post’s **sequential** pattern is this architecture in ops language: cheap retriever fetches candidates; a more precise, more expensive mechanism (kNN among filtered docs, or a reranker) orders them. In RAG, rank still matters (lost-in-the-middle), but inclusion in the window often dominates search-style nDCG.

---

## Alternatives & Tradeoffs

| | Bi-encoder | Cross-encoder | Late interaction (ColBERT-class) |
|--|------------|---------------|----------------------------------|
| Latency at corpus scale | Milliseconds via ANN | Impractical over full corpus | Mid: more storage (token vectors), still ANN-able |
| Quality | Good recall, weaker fine ranking | Best pairwise relevance | Between bi and full cross |
| Indexing | Precompute doc embeddings | No doc-only index | Precompute token embeddings |
| Typical role | Stage-1 retriever | Stage-2 reranker (Week 8) | Stage-1 or substitute rerank |
| Failure mode | Irrelevant near-neighbors; lexical blur | Timeout / cost if `k` too large | Index size; implementation complexity |

Additional knobs:

| Choice | Tradeoff |
|--------|----------|
| Tiny bi-encoder (`all-MiniLM`) | Cheap ingest/query; weaker multilingual/domain |
| API embed (`text-embedding-3-*`, Cohere, Voyage) | Quality/ops outsourced; cost; less control of tokenizer vs BM25 analyzer alignment |
| Domain-tuned bi-encoder (MS MARCO, your tickets) | Better in-domain recall; training/eval burden |
| Pointwise CE vs listwise LLM rerank | CE is batchable and cheap vs GPT; listwise can model set effects (Week 8) |
| Stage-1 `k` | Too small → gold never reaches CE; too large → CE latency SLO burn |

Asymmetric search (SBERT semantic-search docs): questions vs passages may need `encode_query` / `encode_document` (E5-style prefixes). Using one pooling path for both is a silent quality loss, still a bi-encoder issue.

---

## Necessity

Using **only** cross-encoders on a large corpus times out and cannot serve multi-tenant RAG SLOs. Using **only** bi-encoders leaves obvious irrelevant near-neighbors in the `top_k` stuffed into the prompt: synonymy helps “reset MFA,” but fine-grained relevance (“is this the *cancellation* policy or the *refund* policy?”) suffers. Production IR almost always **combines** them; this week you must still **build stage-1 as if Week 8 will consume ~50–100 candidates**.

If stage-1 is cosine-only, a perfect cross-encoder cannot recover SKU/error-code misses (concept 04). If you skip understanding the architecture, teams “add a reranker” on `k=5` and conclude rerankers don’t work — the gold was never a candidate (Pinecone: retriever must get the answer into top-k).

---

## Industry Practice

**Common:** `all-MiniLM` or a vendor embedding API + cosine `top_k=4`. No cross-encoder. No awareness that the embedding is a bi-encoder.

**Strong:** Domain-appropriate bi-encoder (or API embed) → ANN top-50–100, often **hybrid** (concept 02) → cross-encoder / Cohere Rerank / BGE-reranker / Jina reranker. Sentence-Transformers ships **MS MARCO-trained** bi- and cross-encoders explicitly for this pattern. Pinecone Inference `rerank` (e.g. `bge-reranker-v2-m3`) documents the same two-stage constraint: do not run the reranker over more than a few hundred docs.

**FDE bar:** draw the two diagrams (independent towers vs joint Transformer); quote SBERT’s clustering 65h vs 5s example; set `k` from **recall@k of stage-1 on a golden set**, not from context-window folklore; log stage-1 hits **before** rerank (syllabus: instrument candidate logging).

Osanseviero (hackerllama) public post: bi-encoders for search/scale; cross-encoders for comparing a few dozen pairs; retrieve-then-rerank when you need both.

---

## Concrete Scenario

Official Retrieve & Re-Rank guide: retrieve ~100 hits with a bi-encoder **or** Elasticsearch, then `CrossEncoder` scores each `(query, hit)` pair; Wikipedia-paragraph demo notebooks on Simple English Wikipedia.

https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  

Architecture explanation (bi vs cross diagrams; “Cross-Encoders do not produce a sentence embedding”):

https://github.com/huggingface/sentence-transformers/blob/main/examples/cross_encoder/applications/README.md  

Pinecone two-stage writeup (compression vs joint attention; time penalty):

https://www.pinecone.io/learn/series/rag/rerankers/

Syllabus mapping: implement the **retriever API** this week (`search(query) -> candidates with scores from each leg`). Wire CrossEncoder.predict / vendor rerank in Week 8 against the **same** candidate log schema.

---

## Open Questions

- When do strong modern embeds (large API models, instruction-tuned) reduce the **marginal** value of a cross-encoder on FAQ-like corpora? (Still usually keep hybrid for identifiers.)  
- Should stage-1 be dense, sparse, or hybrid **before** the cross-encoder? (Usually hybrid.)  
- Distilled / listwise rerankers vs pointwise cross-encoders under a 50ms budget?  
- Late interaction as stage-1: does it shrink the need for BM25, or still fail on SKUs if tokenization splits them?  
- Matryoshka / binary embeddings: speed vs the already-lossy bi-encoder compression?

---

## Latency budget (why `k` is an SLO)

Rough production sketch (single GPU or a rerank API):

- Bi-encoder query embed: ~5–30 ms (local MiniLM) to ~50–200 ms (remote API).  
- ANN / hybrid fetch of 100 IDs: typically <20–80 ms if indexed.  
- Cross-encoder: **one Transformer forward per pair** (batched). MiniLM-L6 CE on 100 pairs might be tens of ms on GPU and **hundreds of ms–seconds** on CPU. Vendor rerank APIs bill per doc and add network.

Therefore: **stage-1 `k` is a cost control.** SBERT’s “~100” is a quality starting point, not a requirement to CE-score 100 in a 200 ms p95 budget. Common pattern: retrieve 80–100 (hybrid, logged), CE the top 20–50. If CE `k` is 8, you are not running retrieve-and-rerank; you are running “slightly better cosine.”

MS MARCO-trained checkpoints in the Sentence-Transformers org (`cross-encoder/ms-marco-MiniLM-L-6-v2` and bi-encoder siblings) exist specifically so the two stages **agree on the relevance task** (passage ranking), not because MiniLM is SOTA in 2026. Swap embeds independently of the CE; they do not share a vector space (Pinecone/neural-base: independent models).

---

## Logging fields specific to this concept

On each query persist: `bi_encoder_model`, `ann_k`, `ann_metric` (cosine vs ip), `candidate_ids_stage1`. When Week 8 lands: `cross_encoder_model`, `ce_k`, `ce_scores[]`. A CE that reorders but never promotes a BM25-only identifier hit is a **stage-1 bug**, not a CE bug.

---

## Sources

- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html  
- https://github.com/huggingface/sentence-transformers/blob/main/examples/cross_encoder/applications/README.md  
- https://sbert.net/docs/quickstart.html  
- https://huggingface.co/papers/1908.10084  
- https://osanseviero.github.io/hackerllama/blog/posts/sentence_embeddings2/  
- https://www.pinecone.io/learn/series/rag/rerankers/  
- https://huyenchip.com/2024/07/25/genai-platform.html
