# 02 — Cross-encoder rerankers (Cohere Rerank, BGE-reranker) — latency / quality

> Week 8 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

A **cross-encoder reranker** concatenates query and document and runs **full self-attention** over the pair, emitting a scalar relevance score. Unlike a bi-encoder, it does **not** produce an indexable document embedding (Week 7). That is why it is stage-2: one forward pass (or API call) **per candidate**.

### Cohere Rerank (managed)

Product: sort texts by semantic relevance to a query; typically applied to an existing search system’s hits. Conceptual docs list current models (as of this research pass):

| Model | Notes from Cohere docs |
|-------|------------------------|
| `rerank-v4.0-pro` | Multilingual; docs + semi-structured JSON; SOTA / complex use-cases |
| `rerank-v4.0-fast` | Same family; lower latency / higher throughput |
| `rerank-v3.5` | Docs + JSON; EN + non-EN; same languages as `embed-multilingual-v3.0`; **4096** token context |
| `rerank-english-v3.0` | English; 4096 context |
| `rerank-multilingual-v3.0` | Non-English; 4096 context |

**API (`POST https://api.cohere.com/v2/rerank`):** required `model`, `query`, `documents` (list of strings). Optional `top_n` (else return all). Optional `max_tokens_per_doc` (**default 4096**); long documents truncated. Recommend **against >1,000 documents** per request. Structured data: format as **YAML strings** for best performance. Query+document tokens share the per-document context; overflow is **chunked** into multiple inferences (best-practices guide). Constraints (best practices): query up to **2048** tokens (truncated); `documents * max_chunks_per_doc` must not exceed **10,000**; default `max_chunks_per_doc` is 1. Response: ordered results with relevance scores (product copy: scores in `[0,1]` with reordered indices — treat as **rank keys**, not calibrated probabilities across domains).

v1 dialect additionally supported object documents, `rank_fields`, `return_documents` (still visible in some SDK/gateway docs). Prefer v2 + current model IDs in new work; LangChain examples still show `rerank-english-v3.0` — **pin and re-benchmark** when upgrading to v3.5/v4.

Zero ML ops; network RTT + vendor $; enterprise/VPC deploy options exist (Cohere LangChain private-deploy note). Product claim (echoed by Pinecone inference blog): fewer better docs can **cut generator tokens** enough to pay for rerank.

### BGE-reranker (self-hosted open weights)

BAAI FlagEmbedding family. `BAAI/bge-reranker-v2-m3`: multilingual **lightweight** cross-encoder initialized from **bge-m3** lineage; Hugging Face card: ~**0.6B** params; “easy to deploy, fast inference.” Sister models: `bge-reranker-base` / `large` (xlm-roberta; Chinese+English); `bge-reranker-v2-gemma` (Gemma-2B, LLM-style reranker); `bge-reranker-v2-minicpm-layerwise` (choose output layer for speed). Card guidance: multilingual → v2-m3 or v2-gemma; efficiency → v2-m3 or low layer of MiniCPM.

**Inference:**

- `FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)` then `compute_score(['query','passage'])` — raw logits (example **-5.65**); `normalize=True` applies **sigmoid** to `[0,1]`. Batch: list of pairs.  
- Transformers: `AutoModelForSequenceClassification` + tokenizer; `max_length=512` in the official snippet — **truncation is a quality bug** if your chunks are longer.  
- Sentence-Transformers `CrossEncoder` wraps the same idea for MS MARCO MiniLM baselines.  
- LangChain: `HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")` + `CrossEncoderReranker(top_n=3)` + `ContextualCompressionRetriever`. Their size table: MiniLM-L6 **22M** English baseline vs BGE v2-m3 **568M** multilingual default.  
- LlamaIndex: `SentenceTransformerRerank(model=..., top_n=...)` (docs example MiniLM-L-2; default TinyBERT for speed) or Cohere postprocessor for the API.  
- Pinecone hosted: `bge-reranker-v2-m3` described as high-performance multilingual, messy data, short queries → 1–2 paragraph passages.

Evaluation protocol on the model card: rerank **top 100** from a dense retriever on BEIR / CMTEB / MIRACL — same two-stage depths as this week.

**Latency/quality law:** every candidate is a forward pass or HTTP call. Quality usually rises with model size and with `fetch_k` (until stage-1 recall saturates). Truncation limits matter more than people think: Cohere chunks long docs; BGE-m3 CE snippet truncates at 512 unless you change it.

Pointwise CE vs **listwise** (LlamaIndex `LLMRerank`, `RankGPTRerank`, RankLLM): listwise can model “this set together”; cost is a generation call over many passages. Keep as an alternative, not the syllabus default.

---

## Alternatives & Tradeoffs

| Option | Latency / ops | Quality / fit |
|--------|---------------|---------------|
| No rerank | Fastest | Baseline; near-misses in the prompt |
| Small CE (`cross-encoder/ms-marco-MiniLM-L-6-v2`, TinyBERT) | Low GPU/CPU; LangChain/LlamaIndex defaults | Good English MS MARCO baseline; dated vs 2024–26 models |
| **BGE-reranker-v2-m3** | Self-host GPU (CPU OK for small batches); free weights | Strong multilingual OSS; 512-token trap |
| BGE v2-gemma / MiniCPM-layerwise | Heavier GPU; layerwise speed knob | Higher quality / EN-ZH |
| **Cohere Rerank** (`rerank-v3.5` / v4 pro vs fast) | Network RTT; zero ML ops; doc/query token limits | Strong managed; YAML for structured; residency via private deploy |
| Pinecone hosted CE (`bge-reranker-v2-m3`, `pinecone-rerank-v0`) | Same VPC as the index | Ops consolidation; still a CE |
| Jina / Voyage / mixedbread / Qwen3-Reranker | Mix of API vs weights; **check licenses** (some CC-BY-NC) | Leaderboard chasing |
| LLM listwise / RankGPT | Highest latency/$ | Flexible; overkill for many stacks |
| ColBERT postprocessor | Mid: token vectors | Fine-grained MaxSim; not full cross |

Cohere v4 **pro vs fast** is the vendor’s explicit quality/latency fork. Self-host vs API is residency, $ at QPS, and who owns p99.

**Cost accounting:** rerank $ + extra ms vs **generator** tokens. Pinecone claimed large input-token reductions when reranking vs stuffing; treat as a hypothesis to measure on your prompt sizes, not a guarantee.

---

## Necessity

If stage-1 hybrid still returns near-misses, the generator will quote them confidently. Reranking is the cheapest **precision** lever after hybrid search for many teams. Skipping it leaves quality on the table when the latency budget allows ~50–200 ms extra (small CE) or one RTT (Cohere).

Failure modes:

- **Thresholding raw BGE logits** as if they were probabilities.  
- **Comparing Cohere scores to BGE scores** on one scale.  
- **Sending 1000-token chunks to a 512-max CE** — needle truncated.  
- **CPU MiniLM in a tight p95** without batching (`predict` once, not a Python loop).  
- **Data residency:** sending tickets to Cohere Cloud when policy requires VPC — use BGE or Cohere private.  
- **Silent model default:** LlamaIndex TinyBERT default is a speed choice, not a quality choice.

---

## Industry Practice

**Common:** skip rerank, or Cohere on top-20 with library defaults, `top_n` unspecified (returns all — you still stuff 20).

**Strong:** benchmark Cohere vs BGE **on your corpus** (BEIR/MTEB directional only); cap documents per request; batch; set `top_n` to generator budget; monitor p95 separately from embed search; for VPC, self-host BGE or private Cohere. LangChain: mandatory `model=` on `CohereRerank`. LlamaIndex: `similarity_top_k` ≫ `top_n`. Pin model IDs in config; log them on every `retrieval_id`.

**FDE bar:** recite `/v2/rerank` fields; FlagReranker vs Transformers 512 truncation; explain why 1000-doc Cohere requests are a footgun; pick MiniLM vs BGE vs Cohere from a **measured** quality/latency Pareto, not a tweet.

---

## Concrete Scenario

**Cohere API reference** (`model`, `query`, `documents`, `top_n`, `max_tokens_per_doc`); example query “capital of the United States” over five distractor-ish paragraphs, `top_n=3`.

https://docs.cohere.com/reference/rerank  
https://docs.cohere.com/docs/rerank  
https://docs.cohere.com/docs/reranking-best-practices  
Product: https://cohere.com/rerank  

**BGE model card** (FlagReranker + Transformers; sigmoid normalize; eval reranks top 100):

https://huggingface.co/BAAI/bge-reranker-v2-m3  
FlagEmbedding: https://github.com/FlagOpen/FlagEmbedding  

**LangChain CE + BGE v2-m3** (retrieve k=20, `CrossEncoderReranker` top_n=3):

https://docs.langchain.com/oss/python/integrations/document_transformers/cross_encoder_reranker  

**LangChain Cohere** (k=20, `CohereRerank`):

https://docs.langchain.com/oss/python/integrations/retrievers/cohere-reranker  
Cohere’s LC guide: https://docs.cohere.com/docs/rerank-on-langchain  

**LlamaIndex postprocessors** (`CohereRerank`, `SentenceTransformerRerank`, `LLMRerank`, ColBERT, RankGPT):

https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/  

**Pinecone hosted rerank** (including `bge-reranker-v2-m3` passage note):

https://docs.pinecone.io/guides/search/rerank-results  

Chatbot implementation: feature-flag `RERANK_PROVIDER=cohere|bge`; same `fetch_k`/`top_n`; golden-set nDCG@10 + p95. Do not mix providers in one A/B without logging `model`.

YouTube (legal public talks): cross-encoder + Cohere walkthrough https://www.youtube.com/watch?v=ZFbaA9eM0uo ; Cohere Rerank on BM25 without training https://www.youtube.com/watch?v=UsQa-G2-Os0 ; survey of CE vs Cohere vs Qwen3 vs Jina https://www.youtube.com/watch?v=XVZOQ6Fwz2c (treat vendor score claims as **unverified** until you rerun).

---

## Open Questions

- When do rerank-v4 / Voyage-class APIs obsolete self-hosting on **cost** (not just quality)?  
- Score calibration across domains — can thresholds be absolute?  
- Rerank raw chunks vs expanded parent windows?  
- Instruction-aware rerankers (Qwen3-Reranker, BGE-gemma prompts) vs classic CE heads?  
- Distilled CE on CPU vs GPU BGE at 100 QPS — where does the Pareto flip?

---

## Sources

- https://docs.cohere.com/reference/rerank  
- https://docs.cohere.com/docs/rerank  
- https://docs.cohere.com/docs/reranking-best-practices  
- https://docs.cohere.com/docs/rerank-on-langchain  
- https://cohere.com/rerank  
- https://huggingface.co/BAAI/bge-reranker-v2-m3  
- https://github.com/FlagOpen/FlagEmbedding  
- https://arxiv.org/abs/2402.03216 (BGE-M3 paper, cited on the reranker card)  
- https://www.pinecone.io/learn/series/rag/rerankers/  
- https://docs.pinecone.io/guides/search/rerank-results  
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://docs.langchain.com/oss/python/integrations/retrievers/cohere-reranker  
- https://docs.langchain.com/oss/python/integrations/document_transformers/cross_encoder_reranker  
- https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/  
- https://github.com/agentset-ai/awesome-rerankers/  
- https://www.youtube.com/watch?v=ZFbaA9eM0uo  
- https://www.youtube.com/watch?v=UsQa-G2-Os0  
- https://www.youtube.com/watch?v=XVZOQ6Fwz2c  
