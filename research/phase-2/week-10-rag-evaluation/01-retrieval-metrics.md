# 01 — Retrieval metrics (P@k, R@k, MRR, NDCG)

> Week 10 concept research (deep). Legal sources only.

---

## Fundamentals

Treat the retriever as a classical IR system. For each query *q*, the pipeline returns an **ordered** list *D₁ … Dₖ*. Labels (**qrels**) are binary or graded relevance of documents/chunks to *q* (or to a gold answer’s supporting passages). Hamel Husain (evals FAQ, “How should I approach evaluating my RAG system?”): the retrieval component is a **search problem**; evaluate it with traditional IR metrics — Recall@k, Precision@k, MRR — **before** LLM judges on generation. Jason Liu’s **Tier 1** is the same cut.

NVIDIA NeMo’s RAG evaluation flow scores retrieval with **pytrec_eval** (`retriever_recall_k`, `retriever_ndcg_cut_k`, `retriever_P_k`, `retriever_map_cut_k`) and generation separately with **ragas**. Retriever metrics are only computed when a retriever pipeline is actually specified. Azure Foundry **Document Retrieval** is the labelled-qrels process evaluator: composite **Fidelity, NDCG, XDCG, Max Relevance, Holes**.

### Operational definitions (RAG packing)

Always name **which list** you scored: stage-1 `fetch_k`, fused list, reranked list, or **packed prompt k**. Comparing Recall@40 (Week 7 pool) to Recall@5 (packed) without saying so is a reporting bug.

| Metric | Definition (operational) | Sensitive to | Typical RAG use |
| --- | --- | --- | --- |
| **Precision@k** | (# relevant in top *k*) / *k* | Noise in the packed window | “Are we feeding junk to the LLM?” |
| **Recall@k** | (# relevant in top *k*) / (# relevant in qrels for *q*) | Misses outside *k* | “Can generation possibly succeed?” — primary recall-failure detector |
| **MRR** | mean over queries of 1/rank of *first* relevant hit (0 if none) | Single-hit lookup | FAQ / factoid RAG where one chunk suffices |
| **NDCG@k** | DCG normalized by ideal DCG | Graded relevance + rank | Tuning hybrid weights and rerankers |

**Formulas (binary relevance unless noted):**

- \(\mathrm{P@k} = \frac{|\{d \in \mathrm{top\text{-}k} : \mathrm{rel}(d)=1\}|}{k}\)
- \(\mathrm{R@k} = \frac{|\{d \in \mathrm{top\text{-}k} : \mathrm{rel}(d)=1\}|}{|\{d : \mathrm{rel}(d)=1\}|}\)
- \(\mathrm{RR} = 1/\min\{i : \mathrm{rel}(D_i)=1\}\) (0 if none); \(\mathrm{MRR} = \mathrm{mean}_q \mathrm{RR}(q)\)
- \(\mathrm{DCG@k} = \sum_{i=1}^{k} \frac{2^{\mathrm{rel}_i}-1}{\log_2(i+1)}\); \(\mathrm{NDCG@k} = \mathrm{DCG@k}/\mathrm{IDCG@k}\)

NeMo documents `retriever_recall_k` as “fraction of relevant documents retrieved in the top k”; `retriever_ndcg_cut_k` as NDCG at cutoff k (range 0–1); `retriever_P_k` as precision at k. Cutoffs in their retriever-metrics catalog include k ∈ {5, 10, 20, 100} for several named metrics — **your** production *k* may not be in that set; still compute it.

### RAGAS Context Precision (rank-aware cousin)

From docs.ragas.io: Context Precision assesses whether **relevant chunks are placed at the top**. It is the mean of Precision@k **only at ranks where the chunk is relevant** (\(v_k \in \{0,1\}\)):

\[
\mathrm{Context\ Precision@K} = \frac{\sum_{k=1}^{K} (\mathrm{Precision@k} \times v_k)}{\text{number of relevant items in the top } K}
\]

\[
\mathrm{Precision@k} = \frac{\mathrm{TP@k}}{\mathrm{TP@k}+\mathrm{FP@k}}
\]

Worked shape from their docs: relevant then irrelevant → score ≈ 1.0; **irrelevant first**, relevant second → score ≈ 0.5. Same set, different order — NDCG/Context Precision move; set-Recall@2 does not.

**Variants:**

- **ContextPrecision** — LLM judges chunk usefulness vs a **reference** answer.  
- **ContextUtilization** — same rank-aware score vs the **generated response** (no reference).  
- **NonLLMContextPrecisionWithReference** — RapidFuzz / Levenshtein vs `reference_contexts`.  
- **IDBasedContextPrecision** = |retrieved IDs ∩ reference IDs| / |retrieved IDs| (example: retrieved `{doc_1..4}`, gold `{doc_1, doc_4, doc_5, doc_6}` → **0.5**).

**Context Recall** (separate metric, needs a reference): fraction of **reference-answer claims** attributable to retrieved contexts (LLM), or ID-based |gold IDs ∩ retrieved| / |gold IDs|. ID example in docs: retrieved 3 IDs, gold 4, one overlap → **0.25**. This is the claim-level cousin of Recall@k when you lack chunk qrels but have a gold answer.

### Azure Document Retrieval composite

Requires `retrieval_ground_truth` (human `query_relevance_label` per `document_id`) and `retrieved_documents` (system `relevance_score`). Docs recommend it when retrieval is the bottleneck and you have labels — including **parameter sweeps** (algorithm, top_k, chunk size).

| Metric | Azure description |
| --- | --- |
| **Fidelity** | Good documents returned / known good in the dataset (search fidelity) |
| **NDCG** | Ranking vs ideal order of relevant items |
| **XDCG** | Quality of top-k **regardless of scoring of other index documents** |
| **Max Relevance** | Maximum relevance in the top-k chunks (`top1_relevance`, `top3_max_relevance` in sample output) |
| **Holes** / **holes_ratio** | Documents **missing** query relevance judgments — label sanity, not IR quality |

Sample output in Microsoft Learn: `ndcg@3` score **0.646** (pass), `fidelity` **0.019** (fail). That split is the teaching point: NDCG can look “ok” while fidelity says you are not covering known-good docs.

**Retrieval** (LLM-judge, no qrels): 1–5 relevance of concatenated context to the query; pass/fail vs threshold (default 3). Use when labels do not exist; do not replace NDCG once qrels exist (Hamel).

---

## Alternatives & Tradeoffs

| Choice | Tradeoff |
| --- | --- |
| Binary vs graded labels | Graded NDCG needs rubrics (Azure 0–4 / 1–5 scales); binary understates “partially useful” chunks |
| Doc-level vs chunk-level qrels | Chunk labels match the prompt unit; doc labels are cheaper but coarse (a relevant doc can still pack the wrong chunk) |
| Fixed *k* vs *k* sweeps | Production *k* must be reported; sweeps show the recall–noise frontier (Week 8 LITM) |
| Exact ID match vs LLM-judged relevance | IDs are cheap and reproducible; LLM relevance scales when qrels missing (needs calibration) |
| MRR vs Recall@k | MRR ignores extra supporting chunks needed for multi-hop / FP7 completeness |
| Set metrics vs rank-aware | Recall@k can be 1.0 with gold at rank *k*; NDCG/Context Precision still punish that for a small packed window |
| Micro vs macro average | Micro weights busy queries; macro treats each query equally — **say which** |
| Azure Fidelity vs Recall@k | Same spirit (coverage of known good); fidelity is defined on Azure’s labelled set + top n |

**Proxy trap:** optimizing embedding cosine on a synthetic query set can raise P@k on that set while harming real-user recall (distribution shift). Hamel reverse-generation (facts → questions from **your** corpus) is a bootstrap, not a substitute for production queries.

**k trap:** raising *k* monotonically improves Recall@k and usually hurts P@k / context precision. Week 8 rerank exists so you can keep a **small packed k** with high NDCG.

---

## Necessity

End-to-end answer accuracy **confounds** retrieval and generation. Without retrieval metrics you cannot tell Week 9 **recall failure** (gold never eligible) from **ranking/assembly** (gold below packed k / consolidator drop) from **grounding** (gold packed, unused).

**Recall@k is the gate:** if Recall@k_prod = 0, groundedness of the answer is **irrelevant** to debugging retrieval. Averaging faithfulness across those rows blames the generator (Hamel “absence blindness”).

Without NDCG/MRR/Context Precision you will not see Week 8 rerank **working**: gold already in fetch_k, order improved. Recall@fetch_k stays flat; that is success for ranking, not a “no-op eval.”

Azure **Holes** catch a silent bug: you think you have NDCG but half the retrieved IDs have no labels — the metric is not comparable across weeks.

---

## Industry Practice

- Maintain **qrels** (TREC-style) or per-query gold `chunk_id` lists in the golden set (Week 10 file 03).  
- Report at **the same k used in production packing** and at **fetch_k** (and optionally ± neighbors). NeMo: user sets k from 1 to configured `top_k`.  
- Ablate BM25 / dense / hybrid / +rerank with **NDCG@k + Recall@k** on the **same** query set (Week 7–8 story).  
- LangSmith RAG tutorial: **retrieval_relevance** LLM-as-judge when labelled docs are unavailable — binary relevant/not vs concatenated FACTS. Starting point only.  
- Prefer **ID-based** RAGAS precision/recall in CI (deterministic, fast); keep LLM Context Precision for error analysis.  
- Parameter sweep (Azure): generate retrieval results for vector vs semantic, top_k, chunk sizes; pick the setting that maximizes Document Retrieval metrics **then** re-check E2E (file 04).  
- Log `holes` / unlabeled retrieved IDs; do not gate on NDCG when holes_ratio is high.

**Common:** one “retrieval quality” LLM score, k unspecified.  
**Strong:** pytrec / sklearn / RAGAS ID metrics at two k’s; lexical vs semantic slices (Week 7).  
**FDE:** explain Fidelity vs Recall; XDCG vs NDCG; why MRR is the wrong primary metric for multi-hop; quote NeMo’s split of pytrec vs ragas.

---

## Concrete Scenario

**Query:** `ERR_OS_4092` after OpenSearch upgrade (Week 7 lexical slice). Gold chunks: `runbook#os-4092`, `compat-matrix#2.19`.

| System | Ranked IDs (packed k=5) | P@5 | R@5 | RR | Notes |
| --- | --- | --- | --- | --- | --- |
| Cosine-only | 5 semantically “search error” FAQs, neither gold | 0 | 0 | 0 | Recall failure; do not tune prompt |
| Hybrid RRF | gold at ranks 7 and 12, packed 1–5 miss | 0 | 0 at k=5; R@40=1.0 | 1/7 | Ranking/assembly; Week 8 rerank |
| + CE rerank | gold at 1 and 3 | 0.4 | 1.0 | 1.0 | NDCG jumps; generation now eligible |

Azure-shaped labels: gold docs `query_relevance_label` 4–5, near-miss 2. After rerank, `ndcg@3` rises; if you never labelled the near-misses, **holes** stay high and NDCG is noisy.

LangSmith: https://docs.langchain.com/langsmith/evaluate-rag-tutorial — dataset → run → `retrieval_relevance` alongside groundedness.

Azure Document Retrieval metrics: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  

NeMo: https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html — `retriever_recall_5` / `retriever_ndcg_cut_5` type `pytrec_eval`.

---

## Open Questions

- How to define chunk relevance for questions requiring synthesis across *n* chunks (credit partial sets vs all gold IDs)?  
- Should ACL-filtered docs count as relevant-but-inaccessible in the recall **denominator** (they are “known good” for the tenant that cannot see them)?  
- Best labelling UX for graded chunk relevance at startup scale (<100 queries) — 0/1 vs Azure 0–4?  
- MAP vs NDCG vs MRR as the **single** ranking KPI for hybrid α / RRF k=60 — industry default is NDCG@k + Recall@k, not one number.  
- When retrieved_context is **concatenated** (Azure `context` string), how to recover per-chunk ranks for Context Precision? (Keep structured `ids[]` in traces.)

---

## Sources

- RAGAS Context Precision: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/  
- RAGAS Context Recall: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/  
- Azure RAG evaluators (Document Retrieval): https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators  
- NVIDIA NeMo RAG flow (pytrec_eval): https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/rag.html  
- NVIDIA retriever metrics: https://docs.nvidia.com/nemo/microservices/26.3.1/evaluator/metrics/retriever.html  
- NVIDIA RAGAS-family RAG metrics: https://docs.nvidia.com/nemo/microservices/26.3.0/evaluator/metrics/rag.html  
- LangSmith RAG eval tutorial: https://docs.langchain.com/langsmith/evaluate-rag-tutorial  
- Hamel RAG FAQ: https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html  
- Jason Liu six evals (Tier 1 IR): https://jxnl.co/writing/2025/05/19/there-are-only-6-rag-evals/  
- Barnett et al. (eval implications of FP2 K-cutoff): https://arxiv.org/abs/2401.05856  
