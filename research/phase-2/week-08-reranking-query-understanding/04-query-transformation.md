# 04 — Query transformation (HyDE, decomposition, expansion)

> Week 8 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

Rerankers order **candidates that exist**. If the user’s wording lives far from document wording — or the question is multi-hop — **stage-1 recall collapses** and Week 8 precision never runs. **Query transformation** is the query-side fix: change what you embed / BM25 **before** retrieval. The syllabus rule is **one transform, then measure delta** — not HyDE + multi-query + sub-questions on every turn.

### HyDE — Hypothetical Document Embeddings

**Paper:** Luyu Gao, Xueguang Ma, Jimmy Lin, Jamie Callan. *Precise Zero-Shot Dense Retrieval without Relevance Labels.* arXiv:**2212.10496** (ACL 2023 long; Anthology 2023.acl-long.99). CMU LTI + Waterloo. Code: https://github.com/texttron/hyde. **No models were trained** for the pre-print: InstructGPT + Contriever used off the shelf.

**Procedure:**

1. Instruction-following LLM (paper: InstructGPT) is told to **write a document that answers the question** — a *hypothetical* document. It captures relevance **patterns** but is unreal and may contain **false details**.  
2. An unsupervised **contrastive encoder** (paper: Contriever / mContriever) embeds that hypothetical doc. The dense bottleneck is a **lossy compressor** intended to drop hallucinated specifics and keep topical neighborhood.  
3. Retrieval is **document–document** similarity against the corpus. Query–document similarity is **not** explicitly scored. Inner product comes from the encoder’s contrastive pretraining.

**Why it exists:** fully zero-shot dense retrieval without relevance labels is hard; MS-MARCO transfer cannot be assumed (BEIR-style transfer is a different, often commercially restricted, setup). HyDE “pivots” through a generated example of relevance.

**Empirical headline (paper):** HyDE significantly outperforms Contriever-only unsupervised dense retrieval and is comparable to fine-tuned retrievers across web search, QA, fact verification, and non-English (e.g. sw, ko, ja). 11 query sets in their writeup.

**Hallucinations are acceptable** in the hypothesis; grounding is the nearest **real** corpus vectors. If the LLM’s hypothesis is in the wrong neighborhood (alien domain, empty knowledge), Contriever retrieves the wrong street.

LangChain: JS `HydeRetriever` (`@langchain/classic/retrievers/hyde`) — LLM generates hypothetical answer, embed that, search; default prompts from the paper, overridable `{question}` prompt. Python historically `HypotheticalDocumentEmbedder` / HyDE chain under `langchain_classic` (paths move; verify at implement time). LlamaIndex: `HyDEQueryTransform` as a pre-retrieval transform (community/examples; confirm current import path).

### Query expansion / multi-query

Generate **paraphrases** or related terms (LLM or classic IR expansion); retrieve for each; **fuse** (union + dedupe, or **RRF** — Week 7). LangChain **`MultiQueryRetriever.from_llm`**: typically ~3 variants; `include_original` if you still want the user string. Wins on vocabulary mismatch and latent ambiguity. Cost: **K ×** ANN/BM25 plus one LLM hop.

Related **Query2doc** (Wang, Yang, Wei; arXiv:**2303.07678**): few-shot LLM writes a **pseudo-document**, then **concatenates it to the query** for BM25 and/or dense — unlike HyDE’s “embed the hypothesis alone.” They argue HyDE’s assumption (pseudo-doc ≈ gold semantics) can fail; expansion-by-concatenation still helps sparse retrievers (reported BM25 lifts on MS-MARCO / TREC DL without fine-tuning). If you already have BM25 from Week 7, Query2doc-style expansion is a lexical-friendly cousin of HyDE.

### Query decomposition

Split a **multi-hop / multi-constraint** question into sub-queries; retrieve (and often generate) per sub-query; synthesize. LlamaIndex **`SubQuestionQueryEngine`**: break a complex query into sub-questions per relevant data source/tool, gather intermediate answers, synthesize (example: compare Uber vs Lyft revenue growth 2020–2021). Implemented with `QueryEngineTool`s. LangChain patterns: multi-query is not the same as decomposition — paraphrases vs **atomic sub-questions**. Error cascades: a bad split retrieves the wrong evidence forever.

### Step-back (adjacent, not the third required technique)

Zheng et al. step-back prompting: rewrite to a **more abstract** question, retrieve on the abstraction, answer the specific question with both. YouTube explainer (query transforms): https://www.youtube.com/watch?v=feiXQdMjk5o (multi-query, HyDE, step-back). Useful when the user query is hyperspecific (“locked out at 3am”) and docs state a **policy**. Extra LLM call; can over-generalize. Treat as an alternative router branch, not stacked with HyDE by default.

These are **query-side** recall tools. After any of them, still run **hybrid + rerank** on the transformed retrieves. Cache expansions for repeated FAQs.

---

## Alternatives & Tradeoffs

| Technique | Helps when | Costs / risks |
|-----------|------------|---------------|
| **No transformation** | Latency-critical; in-domain wording | Misses vocab-gap and multi-hop |
| **Multi-query expansion** | Synonyms, broad or ambiguous intent | K retrievals; fusion; LLM rewrite quality |
| **HyDE** | Short questions vs long answer-like docs; zero-shot dense gap | LLM latency; bad hyps in alien/private domains; dense-only unless you also BM25 the hyp |
| **Query2doc concat** | Want BM25 term injection from an LLM | Prompt leakage of fabricated facts into lexical match |
| **Decomposition** | Multi-hop / multi-constraint / multi-index | Orchestration; error cascades; linear cost in sub-qs |
| **Step-back** | Need abstract policy before instance | Extra call; may miss instance-specific facts |
| **Stack all of them** | Looks advanced | Unmeasurable; TTFT disaster; syllabus **forbids** as default |

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

---

## Necessity

Embeddings match **surface/semantics of the string you embed**. If users ask like customers and docs read like engineers — or the question requires composing two facts — stage-1 recall dies before rerankers matter. Query transforms buy recall **without re-embedding the corpus**.

Failure modes:

- **HyDE in a private corpus the LLM has never seen** — fluent wrong neighborhood.  
- **Always-on HyDE** adding 300–800 ms to every “reset password” query.  
- **Decomposition producing 8 sub-questions** for a single-fact lookup.  
- **Evaluating E2E only** so you cannot tell transform recall vs rerank precision.  
- **Embedding the hypothesis with a different model than the index.**  
- **Feeding HyDE output to the generator as if it were a source** — it is not evidence.

---

## Industry Practice

**Common:** raw user query → embed. Maybe a hidden “rewrite for search” prompt nobody evals.

**Strong:** router by query type; HyDE or multi-query for semantic gaps; decomposition for multi-hop; **still** hybrid + rerank; cache expansions; evaluate incremental latency vs nDCG/recall **on the slice**. LangChain: `HydeRetriever` / classic HyDE chain; `MultiQueryRetriever` now under `langchain_classic` in v1 migrations. LlamaIndex: `HyDEQueryTransform`; `SubQuestionQueryEngine`; query engines wrap retriever + synthesizer so transforms sit in the query pipeline, not only in the prompt.

**FDE bar:** explain Gao et al.’s two-step factorization (NLG then doc–doc similarity); contrast Query2doc concat vs HyDE embed; refuse to ship three transforms; show a table of recall@80 and p95 with/without the one transform.

Huyen public platform post: retrieval is a menu (term, embedding, hybrid); querying/chunking matter for RAG efficiency — transforms are part of **querying**, not a new agent framework (pitfalls: don’t start too complex).

---

## Concrete Scenario

HyDE paper:

https://arxiv.org/abs/2212.10496  
https://arxiv.org/pdf/2212.10496  
https://aclanthology.org/2023.acl-long.99/  
https://github.com/texttron/hyde  

LangChain HyDE (JS integration, paper-linked):

https://docs.langchain.com/oss/javascript/integrations/retrievers/hyde  

Query2doc (expansion cousin):

https://arxiv.org/abs/2303.07678  

LlamaIndex SubQuestionQueryEngine (decomposition):

https://developers.llamaindex.ai/python/examples/cookbooks/oreilly_course_cookbooks/module-6/router_and_subquestion_queryengine/  
https://developers.llamaindex.ai/typescript/framework/modules/rag/query_engines/  

Downstream precision after any transform remains SBERT retrieve-rerank:

https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  

YouTube: *RAG Query Transformation — Multi-Query, HyDE, and Step-Back Explained* https://www.youtube.com/watch?v=feiXQdMjk5o  

**Chatbot lab (measure delta):** 40 labeled “vocab gap” queries (user language ≠ runbook headings). A: raw query, hybrid 80, BGE rerank 8. B: same but HyDE embedding for the dense leg only; BM25 still uses the raw query (or Query2doc concat — pick **one**). Report recall@80, nDCG@8, answer EM, extra ms. Ship B only if recall lift > latency budget allows.

---

## Open Questions

- HyDE vs fine-tuned query rewriter — when is generation wasteful?  
- Should expansions feed BM25, dense, or both?  
- Multi-agent decomposition vs single structured rewrite?  
- Interaction with conversational query rewriting (history compression)?  
- Does HyDE still pay off when the dense encoder is already instruction-tuned (E5-instruct, GTE, etc.)?  
- Safety: hypothetical docs leaking into user-visible answers / citations?

---

## Sources

- https://arxiv.org/abs/2212.10496  
- https://arxiv.org/pdf/2212.10496  
- https://aclanthology.org/2023.acl-long.99/  
- https://github.com/texttron/hyde  
- https://arxiv.org/abs/2303.07678  
- https://docs.langchain.com/oss/javascript/integrations/retrievers/hyde  
- https://docs.langchain.com/oss/python/migrate/langchain-v1 (MultiQueryRetriever → langchain_classic)  
- https://developers.llamaindex.ai/python/examples/cookbooks/oreilly_course_cookbooks/module-6/router_and_subquestion_queryengine/  
- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://www.pinecone.io/learn/series/rag/rerankers/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://www.youtube.com/watch?v=feiXQdMjk5o  
