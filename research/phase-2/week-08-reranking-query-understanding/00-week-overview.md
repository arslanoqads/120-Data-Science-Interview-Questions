# 00 — Week overview & syllabus mapping

> Week 8 — Reranking & query understanding  
> Research notes (raw).

---

## Fundamentals

Week 8 is the **precision and query-side** week of Phase 2 RAG. Week 7 built a high-recall candidate set (hybrid + RRF, logged). This week decides **which of those candidates occupy the prompt**, in **what order**, and whether the **query string** itself should be rewritten before retrieval.

The syllabus spine is a single production pattern, not three competing architectures:

1. **Retrieve 50–100** with the cheap stage-1 you already have (bi-encoder ANN, BM25, or hybrid).  
2. **Rerank** those candidates with a cross-encoder (Cohere Rerank or BGE-reranker).  
3. **Pack top 5–10** into the generator, with intentional ordering because of lost-in-the-middle.  
4. Add **one** query transform (HyDE, multi-query expansion, or decomposition) on a routed slice.  
5. **Measure the delta** vs the no-rerank / no-transform baseline — quality *and* latency.

Sentence-Transformers’ Retrieve & Re-Rank guide is the shared vocabulary: retrieve a large list (e.g. **100** hits) with lexical search or a bi-encoder; those hits may include irrelevant neighbors; a **CrossEncoder** scores each `(query, candidate)` jointly; the user (or the LLM) sees the reordered shortlist. Scoring thousands or millions of pairs would be slow, so the retriever exists to bound the reranker’s work.

Pinecone’s rerankers chapter is the RAG restatement: maximize retrieval recall by fetching plenty of documents, then maximize *LLM* recall by minimizing how many make it into context. Search engineers used two-stage systems long before RAG because **rerankers are slow and retrievers are fast**.

Chip Huyen’s public platform post already named the **sequential** pattern: cheap retriever, then a more precise, more expensive ranking step. Her 2023 open-challenges post cites Lost in the Middle when discussing RAG: **how much context a model can take ≠ how efficiently it uses that context**.

Query transforms sit *before* stage-1. They buy **recall** when user wording and document wording live far apart, or when one embedding cannot cover multi-hop intent. They do **not** replace reranking. HyDE (Gao et al., arXiv:2212.10496) is the flagship paper: generate a hypothetical answer document, embed *that*, retrieve real docs. Decomposition and multi-query expansion are the other two syllabus tools. The teaching rule is **one transform, measured** — not a stack of HyDE + 5 paraphrases + sub-questions on every chat turn.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Cosine `top_k=5` → generate (Week 7 “common”) | Demo latency | Precision; lost-in-middle mud if you later raise `k` |
| Hybrid 50–100 → generate without rerank | Recall of gold in the window | Near-miss neighbors consume slots; U-curve risk |
| **Hybrid 50–100 → CE rerank → 5–10** (syllabus default) | Precision under a latency budget | Extra 50–200+ ms; GPU or API cost |
| Three-stage (retrieve → RRF → CE → LLM) | Strong enterprise default | More moving parts; need logs at each hop |
| ColBERT / late interaction instead of CE | Different cost curve; token-level MaxSim | Index size; ops; still not lexical hybrid |
| Long-context dump of top-50 | Feels like “using the window” | Liu et al.: extra docs stop helping; middle ignored |
| Query transform on every request | Recall on hard queries | LLM latency × N; error cascades; eval confound |
| **One routed transform + measure delta** | Targeted recall; clean A/B | Need a query router / slice taxonomy |

For the flagship RAG chatbot, prefer **Week 7 candidates (50–100) → rerank to 5–10 → generate**, then enable **one** transform where labeled slices fail. Do not start by swapping Cohere for BGE to “fix relevance” if gold never entered `fetch_k`.

---

## Necessity

Concrete failure modes if Week 8 is skipped:

- Stage-1 hybrid still returns near-misses; the generator quotes them confidently.  
- Teams “try a reranker” on `k=5` and conclude rerankers do nothing — gold was never a candidate (Pinecone: the retriever must get the answer into the candidate set).  
- Naïve `k=20` stuffing invites **lost-in-the-middle**: Liu et al. show a U-shaped accuracy curve; GPT-3.5-Turbo on their multi-document QA was **worse than closed-book** when the gold passage sat in the middle.  
- Open-domain case study in the same paper: going from 20 to 50 Wikipedia docs only marginally improved NQ (~1–1.5%) while retriever recall was still rising — models failed to *use* extra docs.  
- Query/document vocabulary mismatch (customer speak vs engineer docs) collapses stage-1 recall; no reranker recovers a miss.  
- Stacking HyDE + multi-query + decomposition without measurement makes every production miss un-debuggable and burns TTFT.

Without position-aware eval you may increase `k` and watch quality drop while celebrating “more context.”

---

## Industry Practice

- **Common (demo AI):** embed query → `similarity_search(k=4–8)` → stuff context. No rerank. No query rewrite. `k` chosen from context-window folklore.  
- **Strong:** Hybrid retrieve 50–100 → Cohere or BGE rerank to 5–10; log both stages; tune `fetch_k` on recall@k before touching the generator prompt; optionally `LongContextReorder` (LlamaIndex) so strong docs sit at edges; one query transform behind a router (factual / multi-hop / vocab-gap). LangChain pattern: `base_retriever` with large `k` + `ContextualCompressionRetriever` wrapping `CohereRerank` or `CrossEncoderReranker`. LlamaIndex: `similarity_top_k=50–100` + `node_postprocessors=[CohereRerank(top_n=5)]` or `SentenceTransformerRerank`.  
- **FDE bar:** can quote SBERT’s ~100 then CrossEncoder; Cohere `/v2/rerank` params (`model`, `query`, `documents`, `top_n`, `max_tokens_per_doc`); BGE `FlagReranker` vs Transformers `AutoModelForSequenceClassification`; Liu et al. U-curve + open-domain saturation; HyDE’s “hallucinations OK, embedding bottleneck filters”; measure **delta** of rerank and of the single transform on the same golden set.

Cohere product framing (docs + Pinecone inference blog): passing fewer, better docs often **reduces** generator tokens/cost despite rerank spend.

---

## Concrete Scenario

Same product runbooks as Weeks 6–7. On each query:

1. (Optional, routed) Apply **one** transform: e.g. HyDE hypothetical doc embed *or* 3 paraphrases fused with RRF — never both until each has a measured lift.  
2. Hybrid retrieve `fetch_k=80` (dense 80 + BM25 80 → RRF). Log as Week 7.  
3. Rerank the fused 80 with Cohere `rerank-v3.5` or `BAAI/bge-reranker-v2-m3`; `top_n=8`.  
4. Pack 8 chunks, highest score first; optionally reverse-interleave for edges.  
5. Generate. Log `rerank.latency_ms`, scores, and whether gold rank improved.

**Gate the week on deltas**, not vibes:

| Metric | Baseline (Week 7 fused top-8) | Treatment |
|--------|-------------------------------|-----------|
| Stage-1 recall@80 | Must already be high | Rerank cannot fix this |
| nDCG@8 / MRR of packed set | Cosine/RRF order | After CE |
| Answer accuracy / citation hit | Packed 8 unreranked | Packed 8 reranked |
| p95 retrieve / rerank / generate | — | Rerank budget e.g. +100–200 ms |
| Transform slice (vocab-gap, multi-hop) | Raw query | +one transform |

Public bar: SBERT retrieve-rerank README; Cohere Rerank API reference; Hugging Face `BAAI/bge-reranker-v2-m3`; Liu et al. arXiv:2307.03172; Gao et al. arXiv:2212.10496.

URL: https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
Companions: https://docs.cohere.com/reference/rerank · https://huggingface.co/BAAI/bge-reranker-v2-m3 · https://arxiv.org/abs/2307.03172 · https://arxiv.org/abs/2212.10496

---

## Open Questions

- Have post-2024 long-context models flattened the U-curve enough to change `k=5–10` defaults, or only the *shape* of the curve?  
- Optimal `fetch_k` vs rerank model size under a fixed p95?  
- Listwise / RankGPT / LLM-as-reranker vs classic pointwise cross-encoder — when is the extra latency worth it?  
- Can agentic “retrieve more if confidence low” replace static two-stage depths?  
- HyDE vs fine-tuned query rewriter vs Query2doc (concat pseudo-doc to the query for BM25)?  
- Score calibration: can Cohere `[0,1]` or BGE sigmoid thresholds be absolute across domains?

---

## Measure-the-delta protocol (syllabus instrument)

Do not ship rerank or a transform without a paired comparison on the **same** golden queries.

**Rerank A/B (primary):**

| Field | Why |
|-------|-----|
| `retrieval_id` | Join to Week 7 candidate log — **do not overwrite** stage-1 |
| `fetch_k`, `top_n` | Reproducible depths |
| `rerank.model`, `rerank.provider` | Cohere vs BGE vs MiniLM |
| `gold_rank_pre`, `gold_rank_post` | Did CE promote gold? |
| `packed_ids[]` | What the LLM actually saw |
| `latencies_ms.{stage1,rerank,generate}` | SLO attribution |
| `answer_correct` / judge score | End-to-end, not only nDCG |

**Transform A/B (secondary, one technique):**

Hold rerank fixed. Compare raw-query vs transformed-query on the slice the transform is meant to help (short FAQ vs long policy prose → HyDE; multi-constraint → decomposition; synonymy → multi-query). Report recall@80 **and** extra LLM ms. If recall does not move, delete the transform.

---

## Boundaries with adjacent weeks

| Week | This week does | This week does not |
|------|----------------|-------------------|
| 6 | Consume chunk text as rerank input | Re-chunk to “fix” ranking without evidence |
| 7 | Consume hybrid 50–100 + logs | Re-derive RRF / store choice |
| 8 | Rerank, pack 5–10, one query transform, measure delta | Full failure taxonomy (Week 9) or metric cookbook (Week 10) |
| 9 | Provide packed-set + position logs for “ignored gold” vs “never retrieved” | Write the taxonomy |
| 10 | Provide nDCG/recall/latency numbers for the two-stage stack | Own the eval harness design |

---

## Sources

- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://www.pinecone.io/learn/series/rag/rerankers/  
- https://docs.pinecone.io/guides/search/rerank-results  
- https://docs.cohere.com/reference/rerank  
- https://docs.cohere.com/docs/rerank  
- https://huggingface.co/BAAI/bge-reranker-v2-m3  
- https://arxiv.org/abs/2307.03172  
- https://arxiv.org/abs/2212.10496  
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://docs.langchain.com/oss/python/integrations/retrievers/cohere-reranker  
- https://docs.langchain.com/oss/python/integrations/document_transformers/cross_encoder_reranker  
- https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/  
