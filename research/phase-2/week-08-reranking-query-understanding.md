# Week 8 — Reranking & Query Understanding

> RAW SOURCE MATERIAL for AI Engineer / FDE curriculum. Legal sources only. Chip Huyen via public blog/talks only (no pirated book PDFs).

---

## Concept 1: Two-stage retrieval (broad recall → reranker → top-k)

### Fundamentals
**Stage 1 (retriever):** cheap, high-recall search over the full corpus—bi-encoder ANN, BM25, or hybrid—returning e.g. 50–100 candidates.  
**Stage 2 (reranker):** expensive, high-precision model (usually cross-encoder) scores each (query, candidate) and keeps top-k (5–20) for the LLM.

Pinecone’s rerankers chapter: search engineers have long used this pattern because scoring the whole corpus with a reranker is too slow; retrievers are fast, rerankers are accurate.

Sentence-Transformers “Retrieve & Re-Rank” is the canonical open-source formulation of the same pipeline.

### Alternatives & Tradeoffs
| Design | Tradeoff |
|--------|----------|
| Single-stage top-k dense | Simple; weak precision |
| Hybrid stage-1 + no rerank | Better recall mix; ranking still coarse |
| **Two-stage retrieve→rerank** | Best quality/$ for many RAG apps; +latency |
| Three-stage (retrieve→RRF→rerank→LLM) | Strong default for enterprise search |
| End-to-end late interaction (ColBERT) | Different cost curve; ops complexity |

Stage-1 depth (`fetch_k`) must be high enough that the true answer is **in the candidate set**—rerankers cannot recover what stage-1 never retrieved.

### Necessity
Without stage-2, noisy neighbors consume context window slots and degrade answers (see lost-in-the-middle). Without a broad stage-1, the reranker never sees the right doc. Two-stage is how you get both recall and precision under latency budgets.

### Industry Practice
**Common:** embed → top-5 → LLM (no rerank).  
**Strong:** hybrid retrieve 50–100 → rerank to 5–10 → generate; log both stages for eval; tune `fetch_k` on recall@k before touching the generator prompt.

### Concrete Scenario
Pinecone “Rerankers and Two-Stage Retrieval” (motivation, why rerankers are slow, notebook-oriented walkthrough):  
https://www.pinecone.io/learn/series/rag/rerankers/  

Sentence-Transformers pipeline (retrieve ~100 → CrossEncoder → present top hits):  
https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html

### Open Questions
- Optimal `fetch_k` vs rerank model size under fixed p95 latency?
- Listwise / LLM-as-reranker vs classic cross-encoder?
- Can agentic “retrieve more if confidence low” replace static two-stage depths?

### Sources
- https://www.pinecone.io/learn/series/rag/rerankers/
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
- https://cohere.com/rerank
- https://osanseviero.github.io/hackerllama/blog/posts/sentence_embeddings2/

---

## Concept 2: Cross-encoder rerankers (Cohere Rerank, BGE-reranker) — latency / quality tradeoff

### Fundamentals
Cross-encoder rerankers score query–document pairs with full attention. **Cohere Rerank** is a managed API (`/v2/rerank`) returning relevance scores in \([0,1]\) and reordered indices—drop-in precision layer for RAG. **BGE-reranker** (e.g. `BAAI/bge-reranker-v2-m3`) is an open multilingual cross-encoder you self-host (FlagEmbedding / Transformers / Sentence-Transformers `CrossEncoder`).

Quality↑ usually accompanies latency↑ and $↑: every candidate is a forward pass (or API call). Truncation limits (`max_tokens_per_doc`) matter for long chunks.

### Alternatives & Tradeoffs
| Option | Latency / ops | Quality / fit |
|--------|---------------|---------------|
| No rerank | Fastest | Baseline |
| Small CE (`MiniLM` MS MARCO) | Low GPU/CPU | Good English baseline |
| **BGE-reranker-v2-m3** | Self-host GPU; free weights (Apache 2.0 per model card) | Strong multilingual OSS |
| **Cohere Rerank** (e.g. `rerank-v3.5`) | Network RTT; zero ML ops | Strong managed quality; enterprise deploy options |
| LLM listwise rerank | Highest latency/$ | Flexible; overkill for many stacks |

Cohere product framing: pass fewer, better docs into the generator—often **reduces** total tokens/cost despite rerank spend.

### Necessity
If stage-1 hybrid still returns near-misses, the generator will quote them confidently. Reranking is the cheapest precision lever after hybrid search for many teams—skipping it leaves quality on the table when latency budget allows ~50–200 ms extra.

### Industry Practice
**Common:** Skip rerank or call Cohere with defaults on top-20.  
**Strong:** Benchmark Cohere vs BGE on **your** corpus (BEIR/MTEB are directional only); cap documents per request; batch; set `top_n` to generator budget; monitor p95 separately from embed search; for VPC/data residency, prefer self-host BGE or Cohere private deploy.

### Concrete Scenario
Cohere Rerank API reference (`model`, `query`, `documents`, `top_n`, `max_tokens_per_doc`):  
https://docs.cohere.com/reference/rerank  
Product overview: https://cohere.com/rerank  
Docs hub: https://docs.cohere.com/docs/reranking  

BGE reranker model card (usage via FlagReranker / Transformers):  
https://huggingface.co/BAAI/bge-reranker-v2-m3  

Pinecone series chapter tying rerankers to two-stage systems:  
https://www.pinecone.io/learn/series/rag/rerankers/

### Open Questions
- When does rerank-v4 / newer APIs obsolete self-hosting on cost grounds?
- Score calibration across domains—can thresholds be absolute?
- Rerank raw chunks vs expanded parent windows?

### Sources
- https://docs.cohere.com/reference/rerank
- https://docs.cohere.com/docs/reranking
- https://cohere.com/rerank
- https://huggingface.co/BAAI/bge-reranker-v2-m3
- https://www.pinecone.io/learn/series/rag/rerankers/
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
- https://github.com/agentset-ai/awesome-rerankers/

---

## Concept 3: “Lost in the middle” and why reranking mitigates it

### Fundamentals
Liu et al. (TACL 2024 / arXiv:2307.03172) show that when relevant information is placed in a long context, model performance is often **U-shaped**: best when the needle is at the **beginning or end**, worst in the **middle**—even for long-context models. Multi-document QA (retriever-reader style) and synthetic key-value retrieval both exhibit the effect. Open-domain case study: adding more retrieved Wikipedia docs eventually stops helping because models fail to use them.

**Why reranking helps:** If you only pass top-5 highly relevant docs (and optionally order best first / best last), you shrink context and put signal at primacy/recency-friendly positions—less “middle mud.” Reranking does not rewrite attention; it reduces the chance the answer lives in ignored middle distractors.

Chip Huyen’s public “Open challenges in LLM research” cites Lost in the Middle when discussing RAG context efficiency: longer context ≠ better use of context.

### Alternatives & Tradeoffs
| Mitigation | Idea |
|------------|------|
| **Rerank → fewer docs** | Primary production fix |
| Best-first / alternating “lost-in-middle” reorder | Put strong docs at edges |
| Query-aware contextualization | Mixed results in the paper |
| Smaller chunks + citations | Less hay per needle |
| Long-context models alone | Paper: extended context ≠ robust middle use |

### Necessity
Naïvely stuffing top-20 cosine hits into the prompt invites middle-context failures that look like “model dumbness” or hallucinations. Without position-aware eval, you may increase `k` and watch quality drop.

### Industry Practice
**Common:** `k=5` folklore without position testing.  
**Strong:** Measure answer accuracy vs gold-doc position; keep prompt packs short; put highest-rerank doc first (or first+last); treat “more context” as a hypothesis to falsify. Pinecone’s rerankers chapter cites Lost in the Middle as part of the motivation stack.

### Concrete Scenario
Paper (arXiv abstract + PDF):  
https://arxiv.org/abs/2307.03172  
https://arxiv.org/pdf/2307.03172  
ACL Anthology: https://aclanthology.org/2024.tacl-1.9/  

Huyen discussion linking RAG chunking/querying to Lost in the Middle:  
https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  

Pinecone rerankers chapter reference to Liu et al.:  
https://www.pinecone.io/learn/series/rag/rerankers/

### Open Questions
- Have post-2024 models flattened the U-curve enough to change `k` defaults?
- Is edge-ordering still helpful after strong reranking?
- Does RAG-with-citations change how models attend vs plain concatenation?

### Sources
- https://arxiv.org/abs/2307.03172
- https://arxiv.org/pdf/2307.03172
- https://aclanthology.org/2024.tacl-1.9/
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html
- https://www.pinecone.io/learn/series/rag/rerankers/
- https://doi.org/10.1162/tacl_a_00638

---

## Concept 4: Query transformation — HyDE, query decomposition, query expansion

### Fundamentals

**HyDE (Hypothetical Document Embeddings)** — Gao et al., arXiv:2212.10496. An instruction-following LLM writes a *hypothetical* answer document; a contrastive encoder embeds that doc; retrieval becomes **document–document** similarity against the corpus. Hallucinated facts are acceptable—the embedding bottleneck is meant to keep topical signal. No relevance labels required for the HyDE procedure itself.

**Query decomposition** — Split a multi-hop / multi-aspect question into sub-queries; retrieve per sub-query; merge evidence before generation (LangChain multi-query / LlamaIndex sub-question patterns).

**Query expansion / multi-query** — Generate paraphrases or related terms (LLM or classic IR expansion); retrieve for each; fuse (often RRF). Related: Query2doc (LLM writes a pseudo-doc differently framed than HyDE’s zero-shot InstructGPT setup).

These are **query-side** fixes when the user’s wording lives far from document wording—or when one vector cannot cover multi-hop intent.

### Alternatives & Tradeoffs
| Technique | Helps when | Costs / risks |
|-----------|------------|---------------|
| **Multi-query expansion** | Vocabulary mismatch, broad intent | More ANN calls; need fusion |
| **HyDE** | Short questions vs long answer-like docs; zero-shot dense gaps | LLM latency; bad hyps in alien domains |
| **Decomposition** | Multi-hop / multi-constraint questions | Orchestration complexity; error cascades |
| Step-back prompting | Need abstract context first | Extra call; may over-generalize |
| No transformation | Latency-critical, in-domain queries | Misses hard queries |

### Necessity
Embeddings match **surface/semantics of the query string**. If users ask like customers and docs read like engineers—or questions require composing two facts—stage-1 recall collapses before rerankers matter. Query transforms are how you buy recall without re-embedding the corpus.

### Industry Practice
**Common:** Raw user query → embed.  
**Strong:** Router by query type (factual / multi-hop / keyword-heavy); HyDE or multi-query for semantic gaps; decomposition for multi-hop; still apply hybrid + rerank on transformed retrieves; cache expansions; evaluate incremental latency vs nDCG/recall.

LangChain historically exposes `HypotheticalDocumentEmbedder` (HyDE chain) and multi-query retrievers; verify current package paths (`langchain_classic` vs modern LCEL patterns) when implementing.

### Concrete Scenario
HyDE paper (abstract/PDF):  
https://arxiv.org/abs/2212.10496  
https://arxiv.org/pdf/2212.10496  

Gao et al. method summary: generate hypothetical doc with InstructGPT-style instruction model → encode with Contriever → nearest real docs; strong zero-shot gains across web search/QA/fact verification and multiple languages.

Sentence-Transformers retrieve-rerank remains the downstream precision stage after any query transform:  
https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html

### Open Questions
- HyDE vs fine-tuned query rewriter models—when is generation wasteful?
- Should expansions feed BM25, dense, or both?
- Multi-agent decomposition vs single structured rewrite?
- Interaction with conversational query rewriting (history compression)?

### Sources
- https://arxiv.org/abs/2212.10496
- https://arxiv.org/pdf/2212.10496
- https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain_classic/chains/hyde/base.py (implementation reference; path may move)
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
- https://www.pinecone.io/learn/series/rag/rerankers/
- https://huyenchip.com/2024/07/25/genai-platform.html (retrieval stack context)

---

## Week 8 synthesis notes (for later curriculum writing)

**Recommended teaching stack:**  
hybrid retrieve (Week 7) → **rerank** (Cohere or BGE) → pack **few** docs with intentional ordering → generate. Add **query transforms** when eval slices show vocabulary mismatch or multi-hop failures—not by default on every request.

**Huyen public through-line:** RAG needs chunking + retrieval; context length ≠ context use (Lost in the Middle); avoid premature complexity (pitfalls)—rerankers often beat inventing a new agent framework.

### Talk / video pointers
- Greg Kamradt text splitting (upstream of what you rerank): https://youtu.be/8OJC21T2SL4  
- AI Engineer hybrid lab (pairs with rerank optional step): https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a  
- AI Engineer GraphRAG talk (when graph expansion needs its own rank stage): https://ai.engineer/talks/graphrag

### Cross-paper quick refs
| Paper | ID | Use in curriculum |
|-------|-----|-------------------|
| Lost in the Middle (Liu et al.) | arXiv:2307.03172 | Why top-k packing/order matters |
| HyDE (Gao et al.) | arXiv:2212.10496 | Query→hypothetical doc→retrieve |
| Sentence-BERT / CE vs BE (Reimers & Gurevych lineage) | see SBERT docs / HF paper 1908.10084 | Why cross-encoders win on pairs |
