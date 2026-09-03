# 03 — Corpus drift and reindexing strategy

> Week 9 concept research (deep). Legal sources only.

---

## Fundamentals

**Corpus drift** = indexed knowledge diverges from **operational truth**. It is not one bug. It is several clocks running at different rates:

| Clock | What moves | How it shows up |
|-------|------------|-----------------|
| Document clock | Adds / updates / deletes in the CMS or object store | FP1/FP2-shaped misses; contradictory versions in C (FP4) |
| Pipeline clock | Chunker, overlap, embedding model, metadata extractors | Recall collapse after “we upgraded embeddings”; **citation ID churn** |
| Policy clock | ACL, retention, residency, tenant partitions | Gold exists globally, invisible to this user (false FP1) |
| Fact clock | Prices, policies, on-call rotas expire | Faithful answers to **superseded** chunks (A\|C high, world-correctness low) |

Barnett §3.1: **changing the embedding strategy requires re-indexing all chunks**; chunk size and embedding choice are coupled. Lesson table: implement a **RAG pipeline for configuration** — calibrate chunk size, embedding, chunking, retrieval, consolidation, context size, and prompts together (Cognitive Reviewer, AI Tutor, BioASQ). Second lesson: **testing performance characteristics are only possible at runtime**; labelled Q/A often arrive after indexing.

**Citation drift** is the user-visible form: historical `chunk_id` / offsets no longer point at the bytes the model quoted. Rechunking or re-embedding without an **immutable evidence store** invalidates the sources panel even when answers remain plausible.

**Reindexing strategy** is the ops plan for when and how to rebuild dense (and sparse) indices:

| Strategy | Description | When |
|----------|-------------|------|
| **Full rebuild** | Re-chunk + re-embed entire corpus | Embedding-model change; chunker change; corruption |
| **Incremental upsert** | Content-hash change detection; upsert/delete affected docs | Normal CMS edits |
| **Blue/green index** | Build new index; flip alias after eval gate | Any risky pipeline_version |
| **Dual-write / shadow** | Serve old; score new offline on golden set | Embedding A/B |
| **Temporal / versioned retrieval** | `valid_from` / `valid_to`; keep superseded chunks for audit | Policies, prices, legal |
| **as_of filter** | Query-time metadata, not “hope embeddings encode recency” | Time-travel Q&A |

Databricks long-context RAG study (Leng et al., blog + arXiv:2411.03538) is relevant here even though it is not a drift paper: **retrieval depth and context packing interact with the generator**. A reindex that changes chunk size or overlap changes how many chunks you pack for a token budget — you must **re-sweep k** and LITM position, not only recall@k.

Hamel on “RAG is dead”: retrieval is not dead; **naive single-vector** may be. Drift control still applies to hybrid, ColBERT, and agentic search — the **evidence store** and **index alias** remain the source of truth.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
| --- | --- | --- |
| Full reindex nightly | Simple consistency | Cost; downtime; citation ID churn if IDs are positional |
| Hash-based incremental only | Cheap freshness | Misses embedding-model upgrades; won’t catch silent chunker bugs if hash is on **source file** not **chunk text** |
| Incremental + full on `pipeline_version` bump | Balanced | Two code paths; must thread version through logs |
| Immutable evidence store + `supersedes` links | Citation integrity; audit | Storage; default retrieval must **filter superseded** |
| Always serve latest blob, citations are URLs | Simple UX | False trust after edits (concept 02) |
| Skip eval gate on index flip | Fast SLA | Recall@k regressions ship (Barnett: continuous calibration) |

**Freshness SLA vs eval gate:** shipping a new chunker without re-running retrieval metrics on a **pinned** golden set routinely regresses recall@k. Conversely, freezing the index while the CMS moves produces silent FP1.

Golden-set drift is the sibling problem: if the **corpus is the moving target**, last month’s qrels point at deleted chunks. Refresh labels on a cadence; keep a **frozen eval snapshot** of corpus+index for regression (separate from production freshness).

---

## Necessity

Without drift control, **groundedness metrics stay high** while **answer correctness vs the world** collapses — the system is faithful to yesterday’s policy PDF. Enterprise RAG ownership includes **corpus freshness**; otherwise citations lend authority to outdated pricing, medical doses, or course weeks (Barnett AI Tutor: “topics in week 6” is a time-indexed question).

Service-specific failures:

- **Embedding upgrade, partial reembed:** mixed vector spaces; cosine is meaningless; looks like a sudden recall crater.  
- **Delete in CMS, tombstone missing in vector DB:** retriever cites a ghost; generation may still quote snapshot or hallucinate around a stub.  
- **Right-to-be-forgotten vs audit:** legally drop source but keep cited snapshots — product/legal design, not an embedding trick.  
- **ACL change without re-filter:** tenant B sees tenant A chunks (not a quality metric; still a Week 9 log field).  
- **Blue/green flip without alias atomicity:** mixed k from two chunkers in one request.  
- **Canary only on E2E accuracy:** misses retrieval holes Azure would call `holes` (unlabeled) or fidelity drop.

---

## Industry Practice

**Common:** cron “reindex all” Sunday night; IDs = filename + integer; no `pipeline_version`; citations are live URLs.

**Strong:**

- Pin `pipeline_version` + `embedding_model` + `chunker_config` on every stored chunk (Week 6 metadata).  
- Content-addressed IDs; on text change, **new ID** + `supersedes` link; retrieval filter `superseded=false` by default.  
- Gate production alias flips on: recall@k / NDCG (same k as prod), sample faithfulness on snapshots, spot-check **high-traffic queries**.  
- Online signals: rising “I don’t know,” thumbs-down, contradiction rate in retrieved sets, Azure Document Retrieval **fidelity** drop.  
- Time-sensitive corpora: metadata `as_of` / `valid_to` filters.  
- Dual-index eval: old vs new alias on the **same** golden queries (Week 8 delta protocol reused).  
- Log `index_alias` on every `retrieval_id` so Week 9 taxonomy can split “model change” from “index change.”

**FDE bar:** explain why embedding change ⇒ **full** reembed (Barnett); draw blue/green; refuse to debug “quality drop Monday” without `pipeline_version` and content hashes; distinguish **faithful-stale** from **hallucination**.

---

## Concrete Scenario

Injection **cell H** from the overview: update a policy PDF in object storage; **do not** reindex. Query that was correct last week now returns the old hash. Labels: canonical **recall** (stale content = missing *current* content), Barnett **FP1-like**, Jason C|Q measured against **new** truth. Groundedness vs **packed old C** may still be 1.0 — that is the teaching point.

Databricks DocsQA in the long-context study uses **real user questions** against **public Databricks documentation** — a corpus that itself drifts as docs ship. Their experimental chunking (512 tokens, stride 256, `text-embedding-3-large`, FAISS IndexFlatL2) is a **pinned pipeline**; changing any knob is a new index.

Practitioner writeup on citations backfiring when chunks keep changing (immutable evidence / content-addressed IDs): https://medium.com/@npavfan2facts/rag-citations-backfire-when-chunks-keep-changing-850f4336d882

URL: https://arxiv.org/abs/2401.05856 (embedding change ⇒ full reindex)  
Companions: https://www.databricks.com/blog/long-context-rag-performance-llms · https://arxiv.org/abs/2411.03538 · https://aiarch.dev/patterns/grounded-rag · Week 6 `ingested_at` / `doc_version` notes

---

## Open Questions

- Automated **canaries** for embedding-space drift without labelled queries (random triplet stability? reconstruction?)?  
- How often to refresh golden sets when the corpus is the moving target?  
- Legal retention of cited snapshots after source deletion (audit vs right-to-be-forgotten)?  
- Does agentic “search the live web” remove index drift or just **move** drift into tool-result freshness?  
- Sparse+dense dual indices: incremental BM25 vs full dense rebuild — split cadences?

---

## Sources

- Barnett et al. (chunk/embed coupling; reindex all chunks; runtime validation): https://arxiv.org/abs/2401.05856 · https://arxiv.org/html/2401.05856v1  
- Databricks Long Context RAG Performance: https://www.databricks.com/blog/long-context-rag-performance-llms  
- Leng et al. arXiv:2411.03538: https://arxiv.org/abs/2411.03538  
- Grounded RAG / index ownership: https://aiarch.dev/patterns/grounded-rag  
- Citation drift writeup: https://medium.com/@npavfan2facts/rag-citations-backfire-when-chunks-keep-changing-850f4336d882  
- Hamel “Is RAG dead?” (retrieval still required; naive vectors ≠ RAG): https://hamel.dev/blog/posts/evals-faq/index.html  
- Azure Document Retrieval (parameter sweep including chunk sizes): https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- YouTube: Hamel & Shreya Lenny’s Podcast (failure modes emerge from reviewing outputs; you cannot freeze a corpus-blind rubric): https://www.youtube.com/watch?v=BsWxPI9UM4c  
