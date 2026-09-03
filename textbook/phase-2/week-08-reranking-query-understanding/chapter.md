# Chapter 8 — Reranking and query understanding

> **Phase 2 — RAG Systems**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-2/week-08-reranking-query-understanding/`  
> **Syllabus Build:** On the Week 7 hybrid candidate API, ship **two-stage retrieval**: stage-1 hybrid + RRF (or equivalent) returning **50–100** candidates (`fetch_k`); stage-2 cross-encoder rerank (Cohere **or** self-hosted BGE) keeping **top 5–10** for generation; add **exactly one** query transform (HyDE *or* multi-query expansion *or* decomposition) on a **routed** slice; **measure delta** against the Week 7 baseline (stage-1 recall@k, nDCG/MRR after rerank, answer accuracy / groundedness after packing 5–10, plus p95 latency of retrieve vs rerank vs generate).

---

## Prerequisites Recap

Before this week you should already have from Week 7:

- **Hybrid retrieval** — dense ANN (bi-encoder embeddings) **and** BM25 (or equivalent sparse) over the same `chunk_id`s, not cosine-only `top_k`.  
- **RRF fusion** (`k=60` unless evals say otherwise) merging both legs into a candidate set of tens to low hundreds.  
- **Candidate logging** on every query (`retrieval_id`, per-leg ids/ranks/scores, fusion params, fused list) so stage-1 misses stay attributable.  
- A store path that supports the hybrid you shipped — **pgvector + app-side fusion**, or a dedicated / hybrid-native engine — with filters and dual-leg logs intact.

You do **not** need cross-encoder rerank, lost-in-the-middle packing discipline, or routed query transforms yet. That is what this week teaches.

---

## What this week builds

Week 7 built a high-recall candidate set (hybrid + RRF, logged). Week 8 is the **precision and query-side** week: which of those candidates occupy the prompt, in what order, and whether the query string itself should be rewritten before retrieval.

The syllabus spine is one production pattern, not three competing architectures:

1. **Retrieve 50–100** with the cheap stage-1 you already have (bi-encoder ANN, BM25, or hybrid).  
2. **Rerank** those candidates with a cross-encoder (Cohere Rerank or BGE-reranker).  
3. **Pack top 5–10** into the generator, with intentional ordering because of lost-in-the-middle.  
4. Add **one** query transform (HyDE, multi-query expansion, or decomposition) on a routed slice.  
5. **Measure the delta** vs the no-rerank / no-transform baseline — quality *and* latency.

Sentence-Transformers’ Retrieve & Re-Rank guide is the shared vocabulary: retrieve a large list (e.g. **100** hits) with lexical search or a bi-encoder; those hits may include irrelevant neighbors; a **CrossEncoder** scores each `(query, candidate)` jointly; the user (or the LLM) sees the reordered shortlist. Scoring thousands or millions of pairs would be slow, so the retriever exists to bound the reranker’s work.

Pinecone’s restatement for RAG: maximize retrieval recall by fetching plenty of documents, then maximize *LLM* recall by minimizing how many make it into context. Search engineers used two-stage systems long before RAG because **rerankers are slow and retrievers are fast**. Chip Huyen’s public platform post names the **sequential** pattern: cheap retriever, then a more precise, more expensive ranking step. Her 2023 open-challenges post cites Lost in the Middle: **how much context a model can take ≠ how efficiently it uses that context**. Week 7 owned the **ensemble** first stage; this week owns the sequential second hop.

The four ideas below are one system:

- **Two-stage retrieval** — stage-1 hybrid pool (50–100) → cross-encoder → packed top 5–10.  
- **Cross-encoder rerankers** — Cohere Rerank (managed) or BGE-reranker (self-host); pick one path, measure.  
- **Lost in the middle** — fewer, better-ordered docs beat stuffing a long window.  
- **Query transformation** — exactly one routed transform (HyDE, multi-query, or decomposition), measured on its slice.

Query transforms sit *before* stage-1. They buy **recall** when user wording and document wording live far apart, or when one embedding cannot cover multi-hop intent. They do **not** replace reranking. The teaching rule is **one transform, measured** — not a stack of HyDE + 5 paraphrases + sub-questions on every chat turn.

Do not skip this week for “long-context models can eat top-20 cosine hits.” Liu et al. show more retrieved docs eventually stop helping; Pinecone restates the same as maximize retriever recall then minimize what the LLM sees. Do not overwrite Week 7 candidate logs when rerank lands — Week 9 needs both stages to separate miss-at-retrieve from miss-at-rerank from ignore-at-generate.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: **Deployment Copilot**) on product runbooks with Week 7’s hybrid candidate API and logs.

**Default path (synthesis):** keep Week 7 candidate logs; **append** `rerank.ids[]`, `rerank.scores[]`, `rerank.model`, `top_n` → tune `fetch_k` on **stage-1 recall@k** until gold is usually in the 50–100 pool; only then tune the reranker → pack **few** docs; put the highest-rerank hit first (optionally first+last via `LongContextReorder`) → enable one query transform only where eval slices show vocabulary mismatch or multi-hop failure → compare Cohere vs BGE on **your** corpus (BEIR/MTEB are directional).

---

### Two-stage retrieval (broad recall → reranker → top-k)

* **Fundamentals:**  
  **Two-stage retrieval** is the production IR pattern that RAG inherited:

  **Stage 1 (retriever):** cheap, high-recall search over the full corpus. Implementations: bi-encoder + ANN, BM25 / inverted index, learned sparse, or **hybrid + RRF** (Week 7). Returns a candidate pool of tens to low hundreds — syllabus default **50–100**. The job is **not** to order perfectly. The job is to put the true answer **in the set**.

  **Stage 2 (reranker):** expensive, high-precision model — usually a **cross-encoder** — scores each `(query, candidate)` pair with full attention and keeps **top-k** (syllabus **5–10**, literature often 5–20) for the LLM. The reranker never sees documents stage-1 dropped.

  Pinecone (“Rerankers and Two-Stage Retrieval”): scoring the whole corpus with a reranker is too slow. Retrievers are fast; rerankers are accurate. The RAG-specific twist: you are not only optimizing search nDCG for a SERP — you are optimizing **what occupies a finite, position-sensitive context window**. Their walkthrough recipe: retrieve more (`top_k=25` in one example), rerank to a handful (`top_n=3`). Hosted-rerank docs generalize: first query the index for a given number of results, then send query + results to a reranking model.

  Sentence-Transformers “Retrieve & Re-Rank”: retrieve e.g. **100** possible hits with Elasticsearch **or** a `SentenceTransformer` bi-encoder; then a `CrossEncoder` scores relevancy of all candidates. Explicit constraint: “Scoring thousands or millions of (query, document)-pairs would be rather slow. Hence, we use the retriever to create a set of e.g. 100 possible candidates.”

  Chip Huyen (public GenAI platform post) describes the same idea as **sequential** composition: a cheap retriever fetches candidates; a more precise, more expensive mechanism orders them. She contrasts that with **ensemble** (parallel retrievers then combine — Week 7). Week 8 owns the sequential second hop after ensemble fusion.

  **Why two stages instead of “just retrieve 5 well”:** a bi-encoder must compress each document into one vector *without seeing this query* (Pinecone’s compression argument). Neighbors in embedding space include topical near-misses. The cross-encoder reads the raw pair at query time. You cannot afford that over millions of chunks, so you **bound** the pairwise work.

  **Three-stage** (retrieve per modality → RRF → cross-encoder → LLM) is the enterprise default when Week 7 hybrid exists: RRF is still stage-1 fusion, not a reranker. Do not confuse rank-fusion with cross-encoding.

  **Late interaction (ColBERT)** is a different cost curve: token-level MaxSim with precomputable document token vectors. LlamaIndex ships `ColbertRerank` as a postprocessor. Treat it as an alternative mid-stage, not a reason to skip lexical hybrid or to cross-encode the corpus.

  **Invariant:** stage-1 depth (`fetch_k`) must be high enough that gold is **in the candidate set**. Rerankers cannot recover what stage-1 never retrieved.

* **The Alternatives:**  

  | Design | What you gain | What it costs | When it fits |
  |--------|---------------|---------------|--------------|
  | Single-stage top-k dense | Demo latency | Weak precision; no pairwise interaction | Throwaway demos only |
  | Hybrid stage-1 + no rerank | Better recall mix | Ranking still coarse; more docs → lost-in-middle | Incomplete for production precision |
  | **Two-stage retrieve→rerank** | Best quality/$ for many RAG apps | +latency; needs `fetch_k` tuning | **Syllabus default** |
  | Three-stage (retrieve→RRF→rerank→LLM) | Strong enterprise default | More logs to maintain | When Week 7 hybrid already exists |
  | End-to-end late interaction (ColBERT) | Quality between bi and full cross | Index size; ops complexity | Mid-stage alternative |
  | Sequential BM25-then-dense (no CE) | Cheap candidate cut | Gold with no lexical overlap dies | When BM25 is a trusted gate |
  | Raise `k` into a long-context model | Feels like “using the window” | Liu et al. open-domain saturation | Not a substitute for packing |
  | LLM listwise rerank of 50 | Models set effects | Highest latency/$ | Escalation after pointwise CE |

  Knobs that are actually the design:

  | Knob | If too small | If too large |
  |------|----------------|--------------|
  | `fetch_k` / `similarity_top_k` | Gold never reaches CE; “reranker doesn’t work” | CE/API latency and $; Cohere recommends against >1000 docs/request |
  | Packed `top_n` | Missing supporting evidence / multi-hop | Middle mud; token cost; U-curve |
  | Rerank input text | Truncation (`max_tokens_per_doc`, BGE `max_length=512`) drops the needle | Sending whole PDFs wastes the *reranker’s* context |
  | Batch size (self-host) | GPU underused; p95 worse | OOM |

  LangChain’s cross-encoder integration copy: retrieve top-20 via embeddings, rerank down to top-5 is “one of the highest-impact quality improvements for a RAG pipeline.” Their Cohere notebook uses `search_kwargs={"k": 20}` then `CohereRerank`. LlamaIndex Cohere example: `similarity_top_k=10` then `top_n=2`, contrasted with retrieving top-2 directly (irrelevant context → hallucination). Syllabus depths (50–100 → 5–10) are the same pattern scaled to a hybrid first stage.

* **Failure Modes:**  
  - **Rerank-on-k=5:** CE permutes five near-misses; gold sat at rank 40 of ANN. Looks like “Cohere is bad.”  
  - **Rerank-the-corpus:** timeout, GPU melt, or Cohere `documents * max_chunks_per_doc > 10,000` error.  
  - **Overwrite stage-1 logs:** Week 9 cannot tell miss-at-retrieve from miss-at-rerank.  
  - **Rerank after aggressive metadata filters emptied the pool:** CE has nothing to work with; empty or off-topic `top_n`.  
  - **Pack 50 reranked docs:** you paid for precision then reintroduced lost-in-the-middle.  
  - Without stage-2, noisy neighbors consume context-window slots; without a broad stage-1, the reranker never sees the right doc.

* **Average vs. Strong Engineer:**  
  **Average:** embed → top-5 → LLM (no rerank). Or call Cohere with defaults on top-20 once, never tune `fetch_k`.  
  **Strong:** hybrid retrieve 50–100 → rerank to 5–10 → generate; log both stages; tune `fetch_k` on **recall@k** before touching the generator prompt; cap documents per rerank request; set `top_n` to the generator’s evidence budget; monitor p95 of rerank **separately** from ANN. Frameworks: LangChain `ContextualCompressionRetriever`; LlamaIndex `node_postprocessors`. Pinecone Inference: hosted models including `bge-reranker-v2-m3`; integrated `search` with `rerank` parameter or standalone `rerank`. FDE bar: draw retrieve-100 / rerank-10; explain why RRF is not a cross-encoder; refuse to evaluate a reranker until stage-1 recall@100 is measured; quote Cohere “recommend against sending more than 1,000 documents in a single request.”

* **Worked Example:**  
  Deployment Copilot exposes `GET /retrieve?fetch_k=80` (Week 7 hybrid + RRF) and `POST /retrieve_rerank` that consumes those IDs, calls a cross-encoder, and returns `top_n=8`. Same golden set as Week 7; report **gold-in-pool@80** vs **gold-in-packed@8**. SBERT’s official pipeline encodes Wikipedia paragraphs with a bi-encoder, retrieves a large hit list, then a `CrossEncoder` scores `(query, paragraph)` pairs. LlamaIndex’s Cohere notebook pattern: retrieve top 10, filter with `CohereRerank(top_n=2)` vs retrieve top 2 only — the latter hallucinates when those two are irrelevant. LangChain Cohere: FAISS retriever `k=20` + `CohereRerank` inside `ContextualCompressionRetriever`, then a QA chain over compressed docs. Do not start by swapping Cohere for BGE to “fix relevance” if gold never entered `fetch_k`.

* **Apply It:**  
  1. Keep Week 7 candidate logs; **append** `rerank.ids[]`, `rerank.scores[]`, `rerank.model`, `top_n` — do not overwrite stage-1.  
  2. Set stage-1 `fetch_k` to **50–100**; tune on **recall@k** until gold is usually in the pool before touching the reranker.  
  3. Wire stage-2 to keep **top 5–10** for generation (`top_n` = generator evidence budget).  
  4. Cap documents per rerank request (Cohere: recommend against >1,000; respect chunk caps).  
  5. Expose a separate retrieve-then-rerank path (or postprocessor) with p95 of rerank measured separately from ANN.  
  6. Gate the week on gold-in-pool@`fetch_k` vs gold-in-packed@`top_n` on the same golden set.

---

### Cross-encoder rerankers (Cohere Rerank, BGE-reranker)

* **Fundamentals:**  
  A **cross-encoder reranker** concatenates query and document and runs **full self-attention** over the pair, emitting a scalar relevance score. Unlike a bi-encoder, it does **not** produce an indexable document embedding (Week 7). That is why it is stage-2: one forward pass (or API call) **per candidate**.

  **Cohere Rerank (managed).** Product: sort texts by semantic relevance to a query; typically applied to an existing search system’s hits. Models from Cohere docs (as of the research pass): `rerank-v4.0-pro` (multilingual; docs + semi-structured JSON; SOTA / complex use-cases); `rerank-v4.0-fast` (same family; lower latency / higher throughput); `rerank-v3.5` (docs + JSON; EN + non-EN; same languages as `embed-multilingual-v3.0`; **4096** token context); `rerank-english-v3.0` / `rerank-multilingual-v3.0` (4096 context).

  **API (`POST https://api.cohere.com/v2/rerank`):** required `model`, `query`, `documents` (list of strings). Optional `top_n` (else return all). Optional `max_tokens_per_doc` (**default 4096**); long documents truncated. Recommend **against >1,000 documents** per request. Structured data: format as **YAML strings** for best performance. Query+document tokens share the per-document context; overflow is **chunked** into multiple inferences. Constraints: query up to **2048** tokens (truncated); `documents * max_chunks_per_doc` must not exceed **10,000**; default `max_chunks_per_doc` is 1. Response: ordered results with relevance scores (product copy: scores in `[0,1]` with reordered indices — treat as **rank keys**, not calibrated probabilities across domains). Prefer v2 + current model IDs in new work; LangChain examples still show `rerank-english-v3.0` — **pin and re-benchmark** when upgrading to v3.5/v4. Zero ML ops; network RTT + vendor $; enterprise/VPC deploy options exist. Product claim (echoed by Pinecone inference blog): fewer better docs can **cut generator tokens** enough to pay for rerank — treat as a hypothesis to measure on your prompt sizes.

  **BGE-reranker (self-hosted open weights).** BAAI FlagEmbedding family. `BAAI/bge-reranker-v2-m3`: multilingual **lightweight** cross-encoder initialized from **bge-m3** lineage; Hugging Face card: ~**0.6B** params; “easy to deploy, fast inference.” Sister models: `bge-reranker-base` / `large` (xlm-roberta; Chinese+English); `bge-reranker-v2-gemma` (Gemma-2B, LLM-style reranker); `bge-reranker-v2-minicpm-layerwise` (choose output layer for speed). Card guidance: multilingual → v2-m3 or v2-gemma; efficiency → v2-m3 or low layer of MiniCPM.

  **Inference:** `FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)` then `compute_score(['query','passage'])` — raw logits (example **-5.65**); `normalize=True` applies **sigmoid** to `[0,1]`. Batch: list of pairs. Transformers: `AutoModelForSequenceClassification` + tokenizer; `max_length=512` in the official snippet — **truncation is a quality bug** if your chunks are longer. Sentence-Transformers `CrossEncoder` wraps the same idea for MS MARCO MiniLM baselines. LangChain: `HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")` + `CrossEncoderReranker(top_n=3)` + `ContextualCompressionRetriever` (size table: MiniLM-L6 **22M** English baseline vs BGE v2-m3 **568M** multilingual default). LlamaIndex: `SentenceTransformerRerank(model=..., top_n=...)` (docs example MiniLM-L-2; default TinyBERT for speed) or Cohere postprocessor for the API. Pinecone hosted: `bge-reranker-v2-m3` for high-performance multilingual, messy data, short queries → 1–2 paragraph passages. Evaluation protocol on the model card: rerank **top 100** from a dense retriever on BEIR / CMTEB / MIRACL — same two-stage depths as this week.

  **Latency/quality law:** every candidate is a forward pass or HTTP call. Quality usually rises with model size and with `fetch_k` (until stage-1 recall saturates). Truncation limits matter more than people think: Cohere chunks long docs; BGE-m3 CE snippet truncates at 512 unless you change it.

  Pointwise CE vs **listwise** (LlamaIndex `LLMRerank`, `RankGPTRerank`, RankLLM): listwise can model “this set together”; cost is a generation call over many passages. Keep as an alternative, not the syllabus default.

* **The Alternatives:**  

  | Option | Latency / ops | Quality / fit | When it fits |
  |--------|---------------|---------------|--------------|
  | No rerank | Fastest | Baseline; near-misses in the prompt | Never the production end state |
  | Small CE (`cross-encoder/ms-marco-MiniLM-L-6-v2`, TinyBERT) | Low GPU/CPU; framework defaults | Good English MS MARCO baseline; dated vs 2024–26 models | Latency-tight English baselines |
  | **BGE-reranker-v2-m3** | Self-host GPU (CPU OK for small batches); free weights | Strong multilingual OSS; 512-token trap | VPC / cost control; **syllabus self-host path** |
  | BGE v2-gemma / MiniCPM-layerwise | Heavier GPU; layerwise speed knob | Higher quality / EN-ZH | After v2-m3 saturates |
  | **Cohere Rerank** (`rerank-v3.5` / v4 pro vs fast) | Network RTT; zero ML ops; doc/query token limits | Strong managed; YAML for structured; residency via private deploy | **Syllabus managed path** |
  | Pinecone hosted CE (`bge-reranker-v2-m3`, `pinecone-rerank-v0`) | Same VPC as the index | Ops consolidation; still a CE | When the index and CE share a vendor |
  | Jina / Voyage / mixedbread / Qwen3-Reranker | Mix of API vs weights; **check licenses** (some CC-BY-NC) | Leaderboard chasing | Measure on your corpus |
  | LLM listwise / RankGPT | Highest latency/$ | Flexible; overkill for many stacks | Escalation after pointwise CE |
  | ColBERT postprocessor | Mid: token vectors | Fine-grained MaxSim; not full cross | Mid-stage alternative |

  Cohere v4 **pro vs fast** is the vendor’s explicit quality/latency fork. Self-host vs API is residency, $ at QPS, and who owns p99. Cost accounting: rerank $ + extra ms vs **generator** tokens.

* **Failure Modes:**  
  - **Thresholding raw BGE logits** as if they were probabilities.  
  - **Comparing Cohere scores to BGE scores** on one scale.  
  - **Sending 1000-token chunks to a 512-max CE** — needle truncated.  
  - **CPU MiniLM in a tight p95** without batching (`predict` once, not a Python loop).  
  - **Data residency:** sending tickets to Cohere Cloud when policy requires VPC — use BGE or Cohere private.  
  - **Silent model default:** LlamaIndex TinyBERT default is a speed choice, not a quality choice.  
  - Skipping `top_n` so you still stuff all returned docs (Cohere returns all if `top_n` unspecified).

* **Average vs. Strong Engineer:**  
  **Average:** skip rerank, or Cohere on top-20 with library defaults, `top_n` unspecified.  
  **Strong:** benchmark Cohere vs BGE **on your corpus** (BEIR/MTEB directional only); cap documents per request; batch; set `top_n` to generator budget; monitor p95 separately from embed search; for VPC, self-host BGE or private Cohere. LangChain: mandatory `model=` on `CohereRerank`. LlamaIndex: `similarity_top_k` ≫ `top_n`. Pin model IDs in config; log them on every `retrieval_id`. FDE bar: recite `/v2/rerank` fields (`model`, `query`, `documents`, `top_n`, `max_tokens_per_doc`); FlagReranker vs Transformers 512 truncation; explain why 1000-doc Cohere requests are a footgun; pick MiniLM vs BGE vs Cohere from a **measured** quality/latency Pareto, not a tweet. Treat vendor YouTube score claims as **unverified** until you rerun.

* **Worked Example:**  
  Feature-flag `RERANK_PROVIDER=cohere|bge` on Deployment Copilot with the same `fetch_k`/`top_n`. Path A: Cohere `rerank-v3.5` (or pinned v4) via `/v2/rerank` with `top_n=8` and `max_tokens_per_doc` matched to chunk size. Path B: `FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)` scoring the same 80 candidates in one batch; do not treat raw logits as calibrated probabilities unless `normalize=True`. LangChain wiring: `base_retriever` with large `k` + `ContextualCompressionRetriever` wrapping `CohereRerank` or `CrossEncoderReranker`. LlamaIndex: `similarity_top_k=50–100` + `node_postprocessors=[CohereRerank(top_n=5)]` or `SentenceTransformerRerank`. Golden-set nDCG@10 + p95. Do not mix providers in one A/B without logging `model`.

* **Apply It:**  
  1. Pick **one** provider path for the first ship (Cohere API **or** BGE self-host); feature-flag the other for later A/B.  
  2. Pin `rerank.model` / `rerank.provider` in config and log them on every `retrieval_id`.  
  3. Set `top_n` explicitly to the packed budget (5–10); never rely on “return all.”  
  4. For BGE/Transformers, raise or validate `max_length` against chunk size — do not silently truncate needles at 512.  
  5. For Cohere, respect ≤1000 docs/request, query 2048 truncation, and the 10k chunk product cap; prefer YAML for structured fields.  
  6. Benchmark quality (nDCG/MRR of packed set) and p95 on **your** corpus before declaring a winner.

---

### Lost in the middle (why reranking mitigates)

* **Fundamentals:**  
  **Paper:** Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang. *Lost in the Middle: How Language Models Use Long Contexts.* arXiv:**2307.03172**. Published in **TACL** 2024 (ACL Anthology 2024.tacl-1.9). Affiliations: Stanford, UC Berkeley, Samaya AI.

  **Claim:** having a long context window is not the same as **using** information in that window. When the authors vary **where** the relevant information sits, performance is often **U-shaped**: best when the needle is at the **beginning** (primacy) or **end** (recency), worst in the **middle** — including for models advertised as long-context.

  **Task 1 — Multi-document QA (RAG analogue):** a question + **k** Wikipedia passages; **exactly one** contains the answer; **k−1** are distractors. Instantiated from NaturalQuestions-Open (2,655 queries whose long answer is a paragraph). Gold from NQ annotations; distractors = Contriever-MSMARCO top chunks that do **not** contain the annotated answers. They permute **position** of the gold document and **k** independently. Result: U-shaped accuracy vs gold position. Extreme finding: when gold is in the **middle**, **GPT-3.5-Turbo** multi-document QA can fall **below closed-book** (paper: closed-book **56.1%**). Extended-context models are **not necessarily** better at using context than their shorter-context counterparts.

  Architecture probes: encoder-decoder models are more position-robust **within training length**, then show a U-curve when sequences exceed training length. **Query-aware contextualization** (query before *and* after the documents) nearly perfects the synthetic KV task but **minimally** changes multi-document QA trends. Base LMs without instruction tuning still show the U-curve.

  **Task 2 — Synthetic key-value retrieval:** JSON key-value pairs; return the value for a key. Isolates “can you even copy from the middle?” Some models are perfect; others still U-shaped on middle keys.

  **Open-domain case study (§5):** unlike the controlled task (exactly one gold doc always present), retriever-reader on NQ-Open + Wikipedia: **none or many** of the top-k may contain the answer. **Performance saturates long before retriever recall saturates.** Using **50 documents instead of 20** only marginally improves (~**1.5%** GPT-3.5-Turbo, ~**1%** Claude-1.3) while the retriever is still recovering more gold. Extra retrieved docs are not extra used docs.

  **Protocol they want future long-context claims to meet:** show performance is **minimally affected by position** (small best-case vs worst-case gap), not merely that the window is 100K tokens.

  **Why reranking mitigates (without rewriting attention):** reranking does **not** flatten Transformer positional bias. It changes the **input construction**:

  1. **Fewer docs** — leave the long-k regime where the paper shows degradation and open-domain saturation. Pinecone: maximize retriever recall, then minimize what the LLM sees; they cite Liu et al. explicitly.  
  2. **Better docs in the slots that remain** — less chance the answer lives in a distractor the model actually attends to.  
  3. **Optional edge placement** — put the highest-rerank passage first (primacy) and/or last (recency). LlamaIndex **`LongContextReorder`**: docs cite the same study and reorder retrieved nodes when a large top-k is still required.

  Chip Huyen (*Open challenges in LLM research*, 2023, public blog): RAG is two phases; **context length ≠ efficient context use**; Lost in the Middle is the example under “prompt construction.” Her later platform post: rank still matters because of lost-in-the-middle, but **inclusion** in the window often dominates search-style nDCG — which is why stage-1 recall and stage-2 packing are both this week’s job.

* **The Alternatives:**  

  | Mitigation | Idea | Limit | When it fits |
  |------------|------|-------|--------------|
  | **Rerank → fewer docs (5–10)** | Primary production fix; syllabus default | Cannot help if gold never retrieved | **Default path** |
  | Best-first packing | Exploit primacy | Recency unused; still a U if k is huge | After CE, always put #1 first |
  | Best-first + best-last / `LongContextReorder` | Exploit both lobes of the U | Middle still weak if you keep many docs | When packing more than ~5–8 |
  | Query-aware contextualization | Query before and after docs | Paper: helps KV copy more than multi-doc QA | Optional prompt tweak |
  | Smaller chunks + citations | Less hay per needle | Chunking is Week 6; citations ≠ attention | Coupled with packing |
  | Long-context models alone | Marketing | Paper: extended context ≠ robust middle use | Not a substitute for rerank |
  | Encoder-decoder generators | More robust in-train-length | Rare as the RAG *generator* in current stacks | Rare escalation |
  | Raise k until recall saturates | Feels scientific | Open-domain: reader saturates first | Measure then reject |

  Rerank **then** reorder is complementary: CE chooses *who* enters; reorder chooses *where* they sit.

* **Failure Modes:**  
  - Naïvely stuffing top-20 cosine (or even top-20 RRF) hits invites middle-context failures that look like “the model is dumb” or “hallucination.” Liu et al. show the failure can be **worse than giving no documents**.  
  - **“We have 128K context so k=40 is free.”** Token $ is not free; middle use is not free.  
  - **Gold at rank 1 of CE but packed as document #6 of 12** — you paid for ranking then buried it.  
  - **Evaluating only average accuracy** without slicing by gold position — U-curve hidden in the mean.  
  - **Blaming the LLM** when Week 7 logs show gold was never retrieved — different bug (Week 9 taxonomy).  
  - Without **position-aware eval**, you may increase `k` and watch quality drop while celebrating “more context.”

* **Average vs. Strong Engineer:**  
  **Average:** `k=5` folklore without position testing; or `k=20` because the model card says 128K.  
  **Strong:** measure answer accuracy vs **gold-doc position** on a controlled permutation set (even a 50-query mini protocol); keep prompt packs short; put highest-rerank doc first (or first+last); treat “more context” as a hypothesis to **falsify**. Pinecone rerankers chapter + refine-with-rerank page cite Liu et al. as motivation. LlamaIndex ships `LongContextReorder` as a named postprocessor for this paper. Huyen: invest in retrieval/chunking/querying, not only window size. FDE bar: reproduce the paper’s two experimental knobs (position, k) in language; quote the closed-book-vs-middle GPT-3.5 number as a warning, not as a 2026 SOTA; distinguish *controlled* one-gold-doc vs *open-domain* saturation; log `packed_position` of gold on every eval query. Whether post-2024 long-context models have flattened the U-curve enough to change `k=5–10` defaults remains an open question in the research notes — do not invent a new default without measuring.

* **Worked Example:**  
  Curriculum lab on Deployment Copilot: take 30 NQ-style (or runbook) questions where gold chunk is known. For each, build a 10-doc prompt with gold at indices 0, 4, and 9. Measure exact-match (or your judge). Then rerank the same 10 and pack top 5 (gold should move to index 0 if CE works). Optionally apply `LongContextReorder` if you must keep a larger pack. The delta **is** this week’s point: fewer, better-ordered docs beat stuffing. Log `packed_ids[]` and `packed_position` of gold so Week 9 can separate “ignored gold” from “never retrieved.”

* **Apply It:**  
  1. Cap generator context at **5–10** packed chunks after rerank — do not ship “top-50 into 128K” as the default.  
  2. Pack highest-rerank score **first**; optionally first+last via `LongContextReorder` when packs stay large.  
  3. Add a mini position-permutation eval (gold at start / middle / end) and report accuracy by position.  
  4. Log `packed_ids[]` and gold’s `packed_position` on every eval query.  
  5. Treat “raise k because the window is big” as a hypothesis to falsify against answer quality, not token folklore.  
  6. Do not blame the generator for middle failures when stage-1 never retrieved gold — check Week 7 logs first.

---

### Query transformation (HyDE, decomposition, expansion)

* **Fundamentals:**  
  Rerankers order **candidates that exist**. If the user’s wording lives far from document wording — or the question is multi-hop — **stage-1 recall collapses** and Week 8 precision never runs. **Query transformation** is the query-side fix: change what you embed / BM25 **before** retrieval. The syllabus rule is **one transform, then measure delta** — not HyDE + multi-query + sub-questions on every turn.

  **HyDE — Hypothetical Document Embeddings.** Paper: Luyu Gao, Xueguang Ma, Jimmy Lin, Jamie Callan. *Precise Zero-Shot Dense Retrieval without Relevance Labels.* arXiv:**2212.10496** (ACL 2023 long). CMU LTI + Waterloo. Code: https://github.com/texttron/hyde. **No models were trained** for the pre-print: InstructGPT + Contriever used off the shelf.

  **Procedure:** (1) An instruction-following LLM is told to **write a document that answers the question** — a *hypothetical* document. It captures relevance **patterns** but is unreal and may contain **false details**. (2) An unsupervised **contrastive encoder** embeds that hypothetical doc. The dense bottleneck is a **lossy compressor** intended to drop hallucinated specifics and keep topical neighborhood. (3) Retrieval is **document–document** similarity against the corpus. Query–document similarity is **not** explicitly scored.

  **Why it exists:** fully zero-shot dense retrieval without relevance labels is hard; MS-MARCO transfer cannot be assumed. HyDE “pivots” through a generated example of relevance. Empirical headline: HyDE significantly outperforms Contriever-only unsupervised dense retrieval and is comparable to fine-tuned retrievers across web search, QA, fact verification, and non-English. **Hallucinations are acceptable** in the hypothesis; grounding is the nearest **real** corpus vectors. If the LLM’s hypothesis is in the wrong neighborhood (alien domain, empty knowledge), Contriever retrieves the wrong street.

  Framework wiring: LangChain JS `HydeRetriever` — LLM generates hypothetical answer, embed that, search; default prompts from the paper. Python historically `HypotheticalDocumentEmbedder` / HyDE chain under `langchain_classic` (paths move; verify at implement time). LlamaIndex: `HyDEQueryTransform` as a pre-retrieval transform (confirm current import path).

  **Query expansion / multi-query.** Generate **paraphrases** or related terms (LLM or classic IR expansion); retrieve for each; **fuse** (union + dedupe, or **RRF** — Week 7). LangChain **`MultiQueryRetriever.from_llm`**: typically ~3 variants; `include_original` if you still want the user string. Wins on vocabulary mismatch and latent ambiguity. Cost: **K ×** ANN/BM25 plus one LLM hop.

  Related **Query2doc** (Wang, Yang, Wei; arXiv:**2303.07678**): few-shot LLM writes a **pseudo-document**, then **concatenates it to the query** for BM25 and/or dense — unlike HyDE’s “embed the hypothesis alone.” They argue HyDE’s assumption (pseudo-doc ≈ gold semantics) can fail; expansion-by-concatenation still helps sparse retrievers. If you already have BM25 from Week 7, Query2doc-style expansion is a lexical-friendly cousin of HyDE.

  **Query decomposition.** Split a **multi-hop / multi-constraint** question into sub-queries; retrieve (and often generate) per sub-query; synthesize. LlamaIndex **`SubQuestionQueryEngine`**: break a complex query into sub-questions per relevant data source/tool, gather intermediate answers, synthesize (example: compare Uber vs Lyft revenue growth 2020–2021). LangChain patterns: multi-query is not the same as decomposition — paraphrases vs **atomic sub-questions**. Error cascades: a bad split retrieves the wrong evidence forever.

  **Step-back (adjacent, not a required third technique):** Zheng et al. step-back prompting: rewrite to a **more abstract** question, retrieve on the abstraction, answer the specific question with both. Useful when the user query is hyperspecific and docs state a **policy**. Extra LLM call; can over-generalize. Treat as an alternative router branch, not stacked with HyDE by default.

  These are **query-side** recall tools. After any of them, still run **hybrid + rerank** on the transformed retrieves. Cache expansions for repeated FAQs.

* **The Alternatives:**  

  | Technique | Helps when | Costs / risks | When it fits |
  |-----------|------------|---------------|--------------|
  | **No transformation** | Latency-critical; in-domain wording | Misses vocab-gap and multi-hop | Identifier / SKU / error-code queries |
  | **Multi-query expansion** | Synonyms, broad or ambiguous intent | K retrievals; fusion; LLM rewrite quality | Ambiguous wording, one intent |
  | **HyDE** | Short questions vs long answer-like docs; zero-shot dense gap | LLM latency; bad hyps in alien/private domains; dense-only unless you also BM25 the hyp | Short FAQ vs long prose docs |
  | **Query2doc concat** | Want BM25 term injection from an LLM | Prompt leakage of fabricated facts into lexical match | Lexical-friendly cousin when BM25 exists |
  | **Decomposition** | Multi-hop / multi-constraint / multi-index | Orchestration; error cascades; linear cost in sub-qs | Compare A vs B / multi-hop |
  | **Step-back** | Need abstract policy before instance | Extra call; may miss instance-specific facts | Router branch for policy docs |
  | **Stack all of them** | Looks advanced | Unmeasurable; TTFT disaster | Syllabus **forbids** as default |

  **Syllabus constraint:** enable **one** transform on a **router**. Measure delta on the slice it targets. If recall@80 does not move, remove it.

  Router sketch:

  | Query class | Transform |
  |-------------|-----------|
  | Identifier / SKU / error code | **None** (Week 7 BM25); HyDE can hurt |
  | Short semantic FAQ vs long prose docs | HyDE |
  | Ambiguous wording, one intent | Multi-query (K=3) + RRF |
  | Multi-hop / compare A vs B | Decomposition |
  | Conversational follow-up | Standalone rewrite (history compression) — different bug |

  Do **not** HyDE an error code. The hypothetical doc will not contain `ECONNRESET`.

* **Failure Modes:**  
  - **HyDE in a private corpus the LLM has never seen** — fluent wrong neighborhood.  
  - **Always-on HyDE** adding 300–800 ms to every “reset password” query.  
  - **Decomposition producing 8 sub-questions** for a single-fact lookup.  
  - **Evaluating E2E only** so you cannot tell transform recall vs rerank precision.  
  - **Embedding the hypothesis with a different model than the index.**  
  - **Feeding HyDE output to the generator as if it were a source** — it is not evidence.  
  - Stacking HyDE + multi-query + decomposition without measurement makes every production miss un-debuggable and burns TTFT.

* **Average vs. Strong Engineer:**  
  **Average:** raw user query → embed. Maybe a hidden “rewrite for search” prompt nobody evals.  
  **Strong:** router by query type; HyDE or multi-query for semantic gaps; decomposition for multi-hop; **still** hybrid + rerank; cache expansions; evaluate incremental latency vs nDCG/recall **on the slice**. LangChain: `HydeRetriever` / classic HyDE chain; `MultiQueryRetriever` (under `langchain_classic` in v1 migrations). LlamaIndex: `HyDEQueryTransform`; `SubQuestionQueryEngine`. FDE bar: explain Gao et al.’s two-step factorization (NLG then doc–doc similarity); contrast Query2doc concat vs HyDE embed; refuse to ship three transforms; show a table of recall@80 and p95 with/without the one transform. Huyen: transforms are part of **querying**, not a new agent framework — don’t start too complex.

* **Worked Example:**  
  Chatbot lab (measure delta): 40 labeled “vocab gap” queries (user language ≠ runbook headings). **A:** raw query, hybrid 80, BGE (or Cohere) rerank 8. **B:** same but **one** transform — e.g. HyDE embedding for the dense leg only; BM25 still uses the raw query (or Query2doc concat — pick **one**, not both). Hold rerank fixed. Report recall@80, nDCG@8, answer EM / groundedness, extra ms. Ship B only if recall lift fits the latency budget. For multi-hop slices, swap HyDE for `SubQuestionQueryEngine`-style decomposition instead — still one technique. Never feed the hypothetical document into the generator as evidence.

* **Apply It:**  
  1. Choose **exactly one** transform for the first ship (HyDE *or* multi-query *or* decomposition).  
  2. Put it behind a **router** / query-class gate — not on every request (especially not on identifier queries).  
  3. Hold rerank fixed; A/B raw vs transformed on the **slice** the transform targets.  
  4. Report recall@`fetch_k` **and** extra LLM ms; delete the transform if recall does not move.  
  5. Keep embedding model for HyDE hypotheses identical to the index encoder; never cite the hypothesis as a source.  
  6. After the transform, still run **hybrid + rerank**; cache expansions for repeated FAQs.

---

## Week 8 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Stage-1 depth:** Week 7 hybrid + RRF returns `fetch_k=50–100`; tune on **recall@k** until gold is usually in the pool.  
2. **Stage-2 rerank:** Cross-encoder (Cohere `/v2/rerank` **or** `BAAI/bge-reranker-v2-m3`) keeps **top 5–10**; pin and log `rerank.model` / provider.  
3. **Logging:** Append `rerank.ids[]`, `rerank.scores[]`, `rerank.model`, `top_n`, `packed_ids[]`, latencies — **do not overwrite** stage-1.  
4. **Packing / LITM:** Highest-rerank first (optional `LongContextReorder`); measure answer quality vs gold position on a mini protocol.  
5. **One query transform:** Router enables HyDE *or* multi-query *or* decomposition on a labeled slice only.  
6. **Measure delta:** Same golden set — stage-1 recall@k, nDCG/MRR of packed set, answer accuracy / groundedness, p95 retrieve / rerank / generate; transform slice recall@80 + extra LLM ms.

**Rerank A/B fields (primary):**

| Field | Why |
|-------|-----|
| `retrieval_id` | Join to Week 7 candidate log |
| `fetch_k`, `top_n` | Reproducible depths |
| `rerank.model`, `rerank.provider` | Cohere vs BGE vs MiniLM |
| `gold_rank_pre`, `gold_rank_post` | Did CE promote gold? |
| `packed_ids[]` | What the LLM actually saw |
| `latencies_ms.{stage1,rerank,generate}` | SLO attribution |
| `answer_correct` / judge score | End-to-end, not only nDCG |

**Transform A/B (secondary, one technique):** hold rerank fixed; compare raw-query vs transformed-query on the slice the transform is meant to help. If recall does not move, delete the transform.

**Boundaries with adjacent weeks:** Week 6 supplies chunk text as rerank input (do not re-chunk to “fix” ranking without evidence). Week 7 supplies hybrid 50–100 + logs (do not re-derive RRF). Week 8 owns rerank, pack 5–10, one query transform, measure delta — not the full failure taxonomy (Week 9) or metric cookbook (Week 10).

When those steps are true, Week 8 is done in the syllabus sense: Deployment Copilot retrieves broadly, ranks precisely, packs few docs with intentional order, optionally rewrites hard queries once, and can show the measured delta.

---

## Looking ahead

Week 9 covers the **RAG failure taxonomy**: when the answer is wrong, which stage broke — **recall** (evidence never eligible / never in `fetch_k`), **ranking / context-assembly** (gold in the pool but not packed, or buried mid-prompt), or **generation-grounding** (usable context, model still invents or under-extracts). The artifact is a **portfolio debugging log** joined on `retrieval_id` from Weeks 7–8 — taxonomy labels appended, not a new retriever. Keep stage-1 and `rerank.*` / `packed_position` fields intact so fault injection can attribute misses. Do not skip this week’s measured packing for “we’ll just look at end-to-end answer accuracy.”
