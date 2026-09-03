# 04 — Lexical precision failures (why pure cosine fails)

> Week 7 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

Dense embeddings optimize **semantic neighborhoods**. Training (contrastive pairs, MS MARCO, web query-title) rewards putting paraphrases nearby. That objective **blurs** the distinctions that production users type when they already know the key:

- **SKUs / part numbers** (`SKU-7F2A`, `PN-4418-B`) — rare, high-IDF, often split or character-noised by WordPiece/BPE.  
- **Proper names** (customer org, product family, internal service `payments-gw`) — collisions with common words (`Apple` fruit vs company — Pinecone rerank docs even demo this class).  
- **Error codes** (`ECONNRESET`, `ERR_OS_4092`, HTTP `429` vs the prose “too many requests”).  
- **Version pins** (`8.18` vs `9.0`, `OpenSearch 2.19`) — numeric tokens are famously weak in general text embedders.  
- **Config keys / legal citations** (`max_scan_tuples`, `26 U.S.C. § 501`).

Lexical methods excel **exactly** there: inverted indexes retrieve the posting list for the rare term. Dense methods excel on “how do I reset MFA?” when the doc says “turn two-factor authentication off.” Failure is **asymmetric**: semantic search returns **fluent wrong neighbors** (same product area, wrong identifier). Users experience this as hallucination even when the LLM faithfully read the retrieved chunk.

Sentence-Transformers retrieve & re-rank: lexical search finds **literal** matches and misses synonyms; semantic search recognizes synonyms/acronyms/spelling variation. They present this as motivation for **two-stage** systems — and it equally motivates **hybrid first-stage**, because a semantic-only first stage **never lists** the SKU doc for the CE to save.

SBERT semantic-search docs: keyword engines “can only find documents based on lexical matches”; semantic search also handles synonyms, abbreviations, misspellings. The dual is rarely printed: semantic search **cannot be trusted** as the sole method when the query *is* a lexical match.

Huyen (platform): term-based retrieval is the cheap, strong baseline; hybrid is production. Sequential pattern: fetch all docs containing `transformer` (device vs architecture vs movie), **then** vector-rank among them — a recognition that the **token** is the recall key. Pitfalls post: try **term-based** before agonizing over a vectordb.

Weaviate hybrid blog: sparse + dense roles; hybrid exists because each modality’s blind spot is the other’s strength.

Elastic/OpenSearch hybrid docs: keyword for exact/phrase; vector for meaning; hybrid so the result list has both. Elastic RRF worked examples include documents that **win from BM25 despite missing vectors**.

Tokenization is part of the failure: if `SKU-7F2A` becomes `sku`, `-`, `7`, `##f2`, `##a`, the embedding is a smear of frequent subwords; BM25 on a `keyword` field or identifier analyzer still has a unique posting.

Eval implication: a golden set of only FAQ paraphrases **cannot detect** this class. You need an explicit **lexical-precision slice**.

---

## Alternatives & Tradeoffs

Mitigations ranked by invasiveness:

| # | Mitigation | Helps | Risk |
|---|------------|-------|------|
| 1 | Hybrid BM25 + dense + RRF | Most identifier queries | Analyzer must keep the token |
| 2 | Metadata / keyword **filters** (`product_id`, `version`, `sku`) | When the query or UI provides structure | Users don’t always fill facets |
| 3 | Query classification → lexical-only path for “code-like” queries | Low latency; no dense dilution | Classifier errors |
| 4 | Learned sparse (ELSER/SPLADE) | Synonym expansion *and* term weights | Still not a `keyword` field for SKUs |
| 5 | Character / n-gram indexes | Typos, partial SKUs | Noise, index size |
| 6 | Cross-encoder reranker | Sees raw tokens of **candidates** | Cannot help if stage-1 dropped the doc |
| 7 | Instruct-tuned embeds / bigger models | May reduce *some* lexical misses | Do not assume they retire BM25 |
| 8 | Put identifiers in **chunk text** (Week 6 metadata) | Embeddings at least see the string | Still smoothed; still want BM25 |

Do **not** “fix” this only by raising `top_k` on cosine: the SKU doc may sit at rank 400 in embedding space, behind every semantically adjacent paragraph.

---

## Necessity

Skipping this analysis causes demos that look great on conceptual FAQs and **collapse on ticket deflection / developer docs** — the queries customers actually paste from logs and invoices.

If you skip a lexical-precision eval slice, hybrid A/Bs look flat (FAQ-dominated nDCG) and finance kills BM25 as “complexity.”

If chunks **strip** the SKU into metadata-only and you embed body text without it, **both** legs can fail: BM25 has nothing to match unless you index metadata fields; dense never saw the token. Week 6 + Week 7 are coupled.

Candidate logs without `query_class` make it impossible to report **recall@k by slice**.

---

## Industry Practice

**Common:** Discover the failure in production after launch; add regex boosts as one-offs.

**Strong:** Build an eval slice of lexical-precision queries (IDs, errors, versions, names) **alongside** semantic paraphrases; **gate releases on both slices**. Instrument which **leg** retrieved the gold (BM25-only vs dense-only vs both). Elasticsearch AI Engineer / “Vector Isn’t Enough” lab narrative uses adversarial exact-match queries (error codes, version numbers) to teach hybrid + RRF.

Huyen: start with term-based; don’t overcomplicate vectordb early — for many identifier-heavy corpora, BM25 **is** the product until FAQ volume justifies dense.

**FDE bar:** show a before/after: query `ECONNRESET` cosine-top-10 vs BM25-top-10 vs RRF; explain analyzer (`keyword` vs standard) on a whiteboard.

---

## Concrete Scenario

AI Engineer World’s Fair-style lab listing — break pure vector with error codes and version numbers, then fuse BM25 via Elasticsearch RRF:

https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a  

SBERT lexical vs semantic contrast:

https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html  

Weaviate hybrid motivation:

https://weaviate.io/blog/hybrid-search-explained  

Huyen:

https://huyenchip.com/2024/07/25/genai-platform.html  
https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  

Elastic hybrid / RRF (keyword + vector, docs that rank from BM25 without vectors):

https://www.elastic.co/docs/solutions/search/hybrid-search  
https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  

Pinecone hybrid intro (keyword matches, synonyms, **rare terms** as the point of sparse+dense):

https://docs.pinecone.io/guides/search/hybrid-search  
https://www.pinecone.io/learn/hybrid-search-intro/  

Syllabus: add ≥10 queries of `{sku, error_code, version, person_or_org_name}` to the golden set; require recall@40 ≥ target **on that slice** before calling Week 7 done. Log `query_class`.

---

## Open Questions

- Can instruct-tuned / huge embeds close the lexical gap enough to **drop** BM25 on some domains?  
- Character-level or n-gram augmentation **inside** dense models vs sidecar BM25?  
- How to detect lexical-precision queries reliably online (regex, entropy, IDF of rarest token, tiny classifier)?  
- Multilingual: BM25 analyzer per language vs multilingual dense vs both?  
- Code search: structure-aware lexical (symbols) vs embedding of identifiers?

---

## Sources

- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html  
- https://weaviate.io/blog/hybrid-search-explained  
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion  
- https://www.elastic.co/docs/solutions/search/hybrid-search  
- https://docs.pinecone.io/guides/search/hybrid-search  
- https://www.pinecone.io/learn/hybrid-search-intro/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a  
- https://www.pinecone.io/learn/series/rag/rerankers/
