# 01 — Two-stage retrieval (broad recall → reranker → top-k)

> Week 8 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

**Two-stage retrieval** is the production IR pattern that RAG inherited:

**Stage 1 (retriever):** cheap, high-recall search over the full corpus. Implementations: bi-encoder + ANN, BM25 / inverted index, learned sparse, or **hybrid + RRF** (Week 7). Returns a candidate pool of tens to low hundreds — syllabus default **50–100**. The job is **not** to order perfectly. The job is to put the true answer **in the set**.

**Stage 2 (reranker):** expensive, high-precision model — usually a **cross-encoder** — scores each `(query, candidate)` pair with full attention and keeps **top-k** (syllabus **5–10**, literature often 5–20) for the LLM. The reranker never sees documents stage-1 dropped.

Pinecone (“Rerankers and Two-Stage Retrieval”): search engineers have used this for a long time because scoring the whole corpus with a reranker is too slow. Retrievers are fast; rerankers are accurate. The RAG-specific twist: you are not only optimizing search nDCG for a SERP — you are optimizing **what occupies a finite, position-sensitive context window**. Their recipe in the chapter’s notebook-style walkthrough: retrieve more (`top_k=25` in one example), rerank to a handful (`top_n=3`). Pinecone’s hosted-rerank docs generalize: first query the index for a given number of results, then send query + results to a reranking model.

Sentence-Transformers “Retrieve & Re-Rank” is the canonical open-source formulation: retrieve e.g. **100** possible hits with Elasticsearch **or** a `SentenceTransformer` bi-encoder; then a `CrossEncoder` scores relevancy of all candidates; present the ranked list. Explicit constraint: “Scoring thousands or millions of (query, document)-pairs would be rather slow. Hence, we use the retriever to create a set of e.g. 100 possible candidates.”

Chip Huyen (public GenAI platform post) describes the same idea as **sequential** composition: a cheap retriever fetches candidates; a more precise, more expensive mechanism orders them. She contrasts that with **ensemble** (parallel retrievers then combine — Week 7). Week 8 owns the sequential second hop after ensemble fusion.

**Why two stages instead of “just retrieve 5 well”:** a bi-encoder must compress each document into one vector *without seeing this query* (Pinecone’s compression argument). Neighbors in embedding space include topical near-misses. The cross-encoder reads the raw pair at query time. You cannot afford that over millions of chunks, so you **bound** the pairwise work.

**Three-stage** (retrieve per modality → RRF → cross-encoder → LLM) is the enterprise default when Week 7 hybrid exists: RRF is still stage-1 fusion, not a reranker. Do not confuse rank-fusion with cross-encoding.

**Late interaction (ColBERT)** is a different cost curve: token-level MaxSim with precomputable document token vectors. LlamaIndex ships `ColbertRerank` as a postprocessor. Treat it as an alternative mid-stage, not a reason to skip lexical hybrid or to cross-encode the corpus.

**Invariant:** stage-1 depth (`fetch_k`) must be high enough that gold is **in the candidate set**. Rerankers cannot recover what stage-1 never retrieved. Pinecone states this as the first-stage constraint; SBERT implies it by retrieving ~100 before the CrossEncoder.

---

## Alternatives & Tradeoffs

| Design | Tradeoff |
|--------|----------|
| Single-stage top-k dense | Simple; weak precision; no pairwise interaction |
| Hybrid stage-1 + no rerank | Better recall mix; ranking still coarse; more docs → lost-in-middle |
| **Two-stage retrieve→rerank** | Best quality/$ for many RAG apps; +latency; needs `fetch_k` tuning |
| Three-stage (retrieve→RRF→rerank→LLM) | Strong default for enterprise search; more logs to maintain |
| End-to-end late interaction (ColBERT) | Quality between bi and full cross; index size; ops complexity |
| Sequential BM25-then-dense (Huyen sequential, no CE) | Cheap candidate cut; gold with no lexical overlap dies |
| Raise `k` into a long-context model | Looks like using the window; Liu et al. open-domain saturation |
| LLM listwise rerank of 50 | Models set effects; highest latency/$ |

Knobs that are actually the design:

| Knob | If too small | If too large |
|------|----------------|--------------|
| `fetch_k` / `similarity_top_k` | Gold never reaches CE; “reranker doesn’t work” | CE/API latency and $; Cohere recommends against >1000 docs/request |
| Packed `top_n` | Missing supporting evidence / multi-hop | Middle mud; token cost; U-curve |
| Rerank input text | Truncation (`max_tokens_per_doc`, BGE `max_length=512`) drops the needle | Sending whole PDFs wastes context of the *reranker* |
| Batch size (self-host) | GPU underused; p95 worse | OOM |

LangChain’s own cross-encoder integration copy: retrieve top-20 via embeddings, rerank down to top-5 is “one of the highest-impact quality improvements for a RAG pipeline.” Their Cohere notebook uses `search_kwargs={"k": 20}` then `CohereRerank`. LlamaIndex Cohere example: `similarity_top_k=10` then `top_n=2`, contrasted with retrieving top-2 directly (irrelevant context → hallucination). Syllabus depths (50–100 → 5–10) are the same pattern scaled to a hybrid first stage.

---

## Necessity

Without stage-2, noisy neighbors consume context-window slots and degrade answers (concept 03). Without a broad stage-1, the reranker never sees the right doc. Two-stage is how you get **both** recall and precision under a latency budget.

Service-specific failures:

- **Rerank-on-k=5:** CE permutes five near-misses; gold sat at rank 40 of ANN. Looks like “Cohere is bad.”  
- **Rerank-the-corpus:** timeout, GPU melt, or Cohere 10k-doc × chunks error (`documents * max_chunks_per_doc > 10,000`).  
- **Overwrite stage-1 logs:** Week 9 cannot tell miss-at-retrieve from miss-at-rerank.  
- **Rerank after aggressive metadata filters emptied the pool:** CE has nothing to work with; empty or off-topic top_n.  
- **Pack 50 reranked docs:** you paid for precision then reintroduced lost-in-the-middle.

---

## Industry Practice

**Common:** embed → top-5 → LLM (no rerank). Or call Cohere with defaults on top-20 once, never tune `fetch_k`.

**Strong:** hybrid retrieve 50–100 → rerank to 5–10 → generate; log both stages; tune `fetch_k` on **recall@k** before touching the generator prompt; cap documents per rerank request; set `top_n` to the generator’s evidence budget; monitor p95 of rerank **separately** from ANN. Pinecone Inference: hosted models including `bge-reranker-v2-m3`; integrated `search` with `rerank` parameter or standalone `rerank` operation. Frameworks: LangChain `ContextualCompressionRetriever`; LlamaIndex `node_postprocessors`.

**FDE bar:** draw retrieve-100 / rerank-10; explain why RRF is not a cross-encoder; refuse to evaluate a reranker until stage-1 recall@100 is measured; quote Cohere “recommend against sending more than 1,000 documents in a single request.”

---

## Concrete Scenario

**SBERT official pipeline:** Simple English Wikipedia paragraphs encoded with a bi-encoder; query encoded; retrieve a large hit list; `CrossEncoder` scores `(query, paragraph)` pairs; present top hits.

https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  

**Pinecone chapter:** motivation (rerankers slow, retrievers fast; compression vs joint attention); retrieve 25 → rerank to 3 via `pc.inference.rerank`; cites Lost in the Middle as why fewer docs help the LLM.

https://www.pinecone.io/learn/series/rag/rerankers/  

**LlamaIndex Cohere notebook pattern:** retrieve top 10, filter with `CohereRerank(top_n=2)` vs retrieve top 2 only — the latter hallucinates when those two are irrelevant.

https://developers.llamaindex.ai/python/examples/node_postprocessor/coherererank/  

**LangChain Cohere:** FAISS retriever `k=20` + `CohereRerank(model="rerank-english-v3.0")` inside `ContextualCompressionRetriever`; then a QA chain over compressed docs.

https://docs.langchain.com/oss/python/integrations/retrievers/cohere-reranker  

For the FastAPI chatbot: expose `GET /retrieve?fetch_k=80` (Week 7) and `POST /retrieve_rerank` that consumes those IDs, calls CE, returns `top_n=8`. Same golden set as Week 7; report gold-in-pool@80 vs gold-in-packed@8.

---

## Open Questions

- Optimal `fetch_k` vs rerank model size under fixed p95?  
- Listwise / LLM-as-reranker vs classic cross-encoder?  
- Can agentic “retrieve more if confidence low” replace static two-stage depths?  
- Should parent-document expansion happen **before** CE (rerank small chunks, expand winners) or after (rerank windows)? Pinecone Rerank V0 blog describes chunk retrieve → rerank → expand to page.  
- Two-stage vs learned sparse first-stage strong enough to skip CE on some corpora?

---

## Sources

- https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html  
- https://github.com/huggingface/sentence-transformers/blob/main/examples/sentence_transformer/applications/retrieve_rerank/README.md  
- https://www.pinecone.io/learn/series/rag/rerankers/  
- https://docs.pinecone.io/guides/search/rerank-results  
- https://www.pinecone.io/blog/introducing-reranking-to-pinecone-inference/  
- https://docs.cohere.com/reference/rerank  
- https://osanseviero.github.io/hackerllama/blog/posts/sentence_embeddings2/  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://docs.langchain.com/oss/python/integrations/retrievers/cohere-reranker  
- https://docs.langchain.com/oss/python/integrations/document_transformers/cross_encoder_reranker  
- https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/  
- https://developers.llamaindex.ai/python/examples/node_postprocessor/coherererank/  
