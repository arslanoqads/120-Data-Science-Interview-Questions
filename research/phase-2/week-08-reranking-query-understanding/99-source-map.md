# 99 — Week 8 master source map

> Consolidated index of official docs, vendor blogs, papers, talks. Legal sources only. Chip Huyen via **public blog only** (no pirated *AI Engineering* book).

---

## Chip Huyen (public blog)

| Topic | URL |
|-------|-----|
| Open challenges: RAG phases; **context length ≠ context use**; cites Lost in the Middle | https://huyenchip.com/2023/08/16/llm-research-open-challenges.html |
| GenAI platform: term vs embedding vs hybrid; **sequential** vs ensemble retrieval; rank vs inclusion / LITM | https://huyenchip.com/2024/07/25/genai-platform.html |
| Pitfalls: **start too complex** — do not invent an agent framework instead of retrieval + rerank | https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html |

---

## Two-stage retrieval / Sentence-Transformers

| Topic | URL |
|-------|-----|
| **Retrieve & Re-Rank** (~100 hits; lexical *or* bi-encoder → CrossEncoder) | https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html |
| GitHub copy of the same guide | https://github.com/huggingface/sentence-transformers/blob/main/examples/sentence_transformer/applications/retrieve_rerank/README.md |
| Cross-encoder applications (no indexable embeddings; clustering time contrast) | https://github.com/huggingface/sentence-transformers/blob/main/examples/cross_encoder/applications/README.md |
| Osanseviero public explainer (bi vs cross; retrieve-then-rerank) | https://osanseviero.github.io/hackerllama/blog/posts/sentence_embeddings2/ |

---

## Pinecone (two-stage + LITM motivation)

| Topic | URL |
|-------|-----|
| Rerankers and two-stage retrieval (slow rerankers, fast retrievers; retrieve 25 → top 3; cites Liu et al.) | https://www.pinecone.io/learn/series/rag/rerankers/ |
| Refine with rerank (LITM; long context still capped by doc quality) | https://www.pinecone.io/learn/refine-with-rerank/ |
| Hosted rerank docs (`bge-reranker-v2-m3`, integrated vs standalone) | https://docs.pinecone.io/guides/search/rerank-results |
| Inference rerank announcement (lost-in-the-middle; token reduction claim) | https://www.pinecone.io/blog/introducing-reranking-to-pinecone-inference/ |
| pinecone-rerank-v0 announcement (CE; chunk→page expansion eval) | https://www.pinecone.io/blog/pinecone-rerank-v0-announcement/ |

---

## Cohere Rerank

| Topic | URL |
|-------|-----|
| Product | https://cohere.com/rerank |
| Model details (`rerank-v4.0-pro/fast`, `rerank-v3.5`, v3.0 EN/multilingual; 4096 context) | https://docs.cohere.com/docs/rerank |
| **Rerank API v2** (`model`, `query`, `documents`, `top_n`, `max_tokens_per_doc`; ≤1000 docs rec.) | https://docs.cohere.com/reference/rerank |
| Best practices (chunking, 10k cap, query 2048 truncation) | https://docs.cohere.com/docs/reranking-best-practices |
| LangChain integration guide | https://docs.cohere.com/docs/rerank-on-langchain |
| LlamaIndex integration | https://docs.cohere.com/docs/llamaindex |

---

## BGE / BAAI / FlagEmbedding

| Topic | URL |
|-------|-----|
| **`BAAI/bge-reranker-v2-m3` model card** (FlagReranker, Transformers, sigmoid, eval top-100) | https://huggingface.co/BAAI/bge-reranker-v2-m3 |
| FlagEmbedding GitHub | https://github.com/FlagOpen/FlagEmbedding |
| BGE-M3 paper (cited on card) | https://arxiv.org/abs/2402.03216 |
| LLM-as-foundation for dense retrieval (cited on card) | https://arxiv.org/abs/2312.15503 |
| BGE tutorial reranking page (family table, 568M v2-m3) | https://bge-model.com/tutorial/5_Reranking/5.2.html |

---

## LangChain / LlamaIndex rerank wiring

| Topic | URL |
|-------|-----|
| LangChain **CohereRerank** + `ContextualCompressionRetriever` (k=20 example) | https://docs.langchain.com/oss/python/integrations/retrievers/cohere-reranker |
| LangChain **CrossEncoderReranker** + `BAAI/bge-reranker-v2-m3` (retrieve 20 → top 3) | https://docs.langchain.com/oss/python/integrations/document_transformers/cross_encoder_reranker |
| LangChain v1: MultiQueryRetriever lives in `langchain_classic` | https://docs.langchain.com/oss/python/migrate/langchain-v1 |
| LangChain JS **HydeRetriever** | https://docs.langchain.com/oss/javascript/integrations/retrievers/hyde |
| LlamaIndex node postprocessors (**CohereRerank**, **SentenceTransformerRerank**, **LongContextReorder**, LLM/RankGPT/ColBERT) | https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/ |
| LlamaIndex postprocessor conceptual + `CohereRerank.postprocess_nodes` | https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/ |
| LlamaIndex Cohere rerank example (top 10 → top 2 vs top 2 only) | https://developers.llamaindex.ai/python/examples/node_postprocessor/coherererank/ |
| SubQuestionQueryEngine (decomposition) | https://developers.llamaindex.ai/python/examples/cookbooks/oreilly_course_cookbooks/module-6/router_and_subquestion_queryengine/ |
| QueryEngine / Sub Question concept (TS) | https://developers.llamaindex.ai/typescript/framework/modules/rag/query_engines/ |

---

## Papers (arXiv + venue)

| Paper | ID | URL |
|-------|-----|-----|
| **Lost in the Middle** (Liu et al.) | arXiv:2307.03172 · TACL 2024 | https://arxiv.org/abs/2307.03172 · https://arxiv.org/pdf/2307.03172 · https://aclanthology.org/2024.tacl-1.9/ · https://doi.org/10.1162/tacl_a_00638 |
| **HyDE** (Gao, Ma, Lin, Callan) | arXiv:2212.10496 · ACL 2023 | https://arxiv.org/abs/2212.10496 · https://arxiv.org/pdf/2212.10496 · https://aclanthology.org/2023.acl-long.99/ · https://github.com/texttron/hyde |
| Query2doc (Wang, Yang, Wei) | arXiv:2303.07678 | https://arxiv.org/abs/2303.07678 |
| SBERT / CE vs BE lineage | arXiv:1908.10084 | https://huggingface.co/papers/1908.10084 |

---

## YouTube / talks (public)

| Topic | URL |
|-------|-----|
| RAG query transformation: multi-query, HyDE, step-back | https://www.youtube.com/watch?v=feiXQdMjk5o |
| Advanced RAG: reranking with cross-encoders and Cohere API | https://www.youtube.com/watch?v=ZFbaA9eM0uo |
| Cohere Rerank API in Python (BM25 without training a model) | https://www.youtube.com/watch?v=UsQa-G2-Os0 |
| Reranking survey walkthrough (BM25 + CE + Cohere + Qwen3 + Jina) — verify claims | https://www.youtube.com/watch?v=XVZOQ6Fwz2c |
| Greg Kamradt text splitting (upstream of what you rerank; Week 6) | https://youtu.be/8OJC21T2SL4 |
| AI Engineer hybrid lab (pairs with optional rerank) | https://nextjs-conf-scheduler.sentry.dev/talks/aiewf-581-vector-isnt-enough-hybrid-search-retrieval-for-a |
| AI Engineer GraphRAG (when graph expansion needs its own rank stage) | https://ai.engineer/talks/graphrag |

---

## Secondary indexes

| Topic | URL |
|-------|-----|
| Awesome rerankers list | https://github.com/agentset-ai/awesome-rerankers/ |

---

## Coverage matrix (syllabus concepts → primary URLs)

| Concept file | Must-cite |
|--------------|-----------|
| 00 overview | SBERT retrieve_rerank + Pinecone rerankers + syllabus depths 50–100 → 5–10 |
| 01 two-stage | SBERT retrieve_rerank + Pinecone rerankers + LC compression retriever + LI Cohere example |
| 02 cross-encoders | Cohere `/v2/rerank` + docs/rerank + `BAAI/bge-reranker-v2-m3` + LC CE + LI postprocessors |
| 03 lost-in-the-middle | arXiv:2307.03172 + TACL + Huyen open-challenges + Pinecone + LI `LongContextReorder` |
| 04 query transform | arXiv:2212.10496 + texttron/hyde + LC HydeRetriever + LI SubQuestionQueryEngine + Query2doc 2303.07678 |

**Not used:** pirate book/PDF sites; Chip Huyen *AI Engineering* book text; unauthorized copyrighted book extracts.
