# 99 — Week 6 master source map

> Consolidated index of official docs, vendor blogs, talks, arXiv. Legal sources only. Chip Huyen via **public blog only** (no pirated *AI Engineering* book).

---

## Chip Huyen (public blog)

| Topic | URL |
|-------|-----|
| GenAI platform: RAG needs manageable chunks; size from context + latency; see Pinecone / LangChain / LlamaIndex / Kamradt (explicitly *not* the book chapter) | https://huyenchip.com/2024/07/25/genai-platform.html |
| Open challenges: RAG phase 1 **chunking/indexing**; context *capacity* ≠ context *efficiency*; lost-in-the-middle pointer | https://huyenchip.com/2023/08/16/llm-research-open-challenges.html |
| Pitfalls: start too complex (vectordb before boring retrieval/ingest); compliance on retrieval/caching | https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html |
| Production LLM apps (adjacent; eval/unit-test components) | https://huyenchip.com/2023/04/11/llm-engineering.html |

---

## LangChain — splitters

| Topic | URL |
|-------|-----|
| **RecursiveCharacterTextSplitter** (recommended generic; separators `["\n\n","\n"," ","]`; `length_function`; CJK separators) | https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter |
| Character splitter | https://docs.langchain.com/oss/python/integrations/splitters/character_text_splitter |
| Splitter index (start with recursive; structure-based family) | https://docs.langchain.com/oss/python/integrations/splitters |
| JS: start with recursive | https://docs.langchain.com/oss/javascript/integrations/splitters |
| MarkdownHeaderTextSplitter (header metadata; overlap does not cross sections; `split_documents`) | https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter |
| HTMLHeader / HTMLSemanticPreservingSplitter (tables/lists intact) | https://docs.langchain.com/oss/python/integrations/splitters/split_html |
| Code splitter / `from_language` | https://docs.langchain.com/oss/python/integrations/splitters/code_splitter |
| Recursive JSON splitter | https://docs.langchain.com/oss/python/integrations/splitters/recursive_json_splitter |
| Docling loader (`DOC_CHUNKS` vs Markdown + header split) | https://docs.langchain.com/oss/python/integrations/document_loaders/docling |
| Experimental SemanticChunker source (`breakpoint_threshold_type`) | https://github.com/langchain-ai/langchain-experimental/blob/main/libs/experimental/langchain_experimental/text_splitter.py |

---

## LlamaIndex — node parsers & metadata

| Topic | URL |
|-------|-----|
| **Node parser modules** (`SentenceSplitter`, `CodeSplitter`, `SemanticSplitterNodeParser` citing Kamradt `t=1933`) | https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/ |
| Node parsers API reference | https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/ |
| `CodeSplitter` example (char vs token mode) | https://developers.llamaindex.ai/python/examples/node_parsers/code_splitter_chunking/ |
| `CodeSplitter` source (AST; SweepAI credit) | https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/node_parser/text/code.py |
| `SemanticSplitterNodeParser` source (`buffer_size`, percentile threshold) | https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/node_parser/text/semantic_splitter.py |
| Metadata extraction (`TitleExtractor`, `KeywordExtractor`, `SummaryExtractor`, `QuestionsAnsweredExtractor`, `EntityExtractor`) | https://developers.llamaindex.ai/python/framework/module_guides/indexing/metadata_extraction/ |
| Extractors in `IngestionPipeline` | https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_metadata_extractor/ |
| Documents: `excluded_embed_metadata_keys` / `excluded_llm_metadata_keys`, templates | https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_documents/ |
| SEC metadata extraction example | https://developers.llamaindex.ai/python/examples/metadata_extraction/metadataextractionsec/ |
| Jina embeddings + late_chunking flag (vendor integration) | https://developers.llamaindex.ai/python/framework/integrations/embeddings/jinaai_embeddings/ |
| GCP + LlamaIndex hierarchical / auto-merge | https://cloud.google.com/blog/products/ai-machine-learning/llamaindex-for-rag-on-google-cloud |

---

## Pinecone

| Topic | URL |
|-------|-----|
| **Chunking strategies** (2025-06-28): why chunk; embedder windows; human test; long-context ≠ skip chunking; fixed-size start; recursive middle ground; structure; Kamradt semantic; Anthropic contextual; size sweep 128/256 vs 512/1024; **chunk expansion** | https://www.pinecone.io/learn/chunking-strategies/ |
| RAG evaluation (metrics context for size sweeps) | https://www.pinecone.io/learn/series/vector-databases-in-production-for-busy-engineers/rag-evaluation/ |

---

## Weaviate

| Topic | URL |
|-------|-----|
| **Chunking strategies for RAG** (2025-09-04): findable vs usable; lost-in-middle; pre vs **post-chunking** / Elysia; fixed + 10–20% overlap; recursive; document-based; semantic; LLM-based; **agentic**; **late chunking**; hierarchical | https://weaviate.io/blog/chunking-strategies-for-rag |
| Academy: standalone chunking unit | https://docs.weaviate.io/academy/py/standalone/chunking |

---

## Greg Kamradt — 5 Levels of Text Splitting

| Topic | URL |
|-------|-----|
| YouTube talk | https://youtu.be/8OJC21T2SL4 |
| Semantic section timestamp (LlamaIndex citation) | https://youtu.be/8OJC21T2SL4?t=1933 |
| Public notebook | https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb |

Levels used in this week: 1 character/fixed → 2 recursive → 3 document structure → 4 semantic → 5 agentic.

---

## Anthropic — contextual retrieval (LLM chunk *augmentation*)

| Topic | URL |
|-------|-----|
| Engineering post: contextual embeddings + contextual BM25; 35% / 49% / 67% (with rerank) failure-rate reductions; ~50–100 token prefixes; prompt cache | https://www.anthropic.com/engineering/contextual-retrieval |
| Claude cookbook: contextual embeddings guide | https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide |
| Milvus reproduction notebook (secondary) | https://milvus.io/docs/v2.5.x/contextual_retrieval_with_milvus.md |

---

## Late chunking (pooling, not an LLM splitter)

| Topic | URL |
|-------|-----|
| arXiv **2409.04701** Günther, Mohr, Williams, Wang, Xiao (Jina / Weaviate) | https://arxiv.org/abs/2409.04701 |
| PDF | https://arxiv.org/pdf/2409.04701 |
| Jina blog part 1 | https://jina.ai/news/late-chunking-in-long-context-embedding-models |
| Jina blog part 2 (what it is / is not) | https://jina.ai/news/what-late-chunking-really-is-and-what-its-not-part-ii |
| Reference code | https://github.com/jina-ai/late-chunking |

---

## Lost in the middle / long context

| Topic | URL |
|-------|-----|
| Liu et al. arXiv **2307.03172** | https://arxiv.org/abs/2307.03172 |
| Cited by Huyen open-challenges, Pinecone chunking, Weaviate chunking | (see those rows) |

---

## Secondary industry roundups (legal blogs; not primary)

| Topic | URL |
|-------|-----|
| Firecrawl: recursive 400–512 tokens / 10–20% overlap as common default; page-level vs semantic notes | https://www.firecrawl.dev/blog/best-chunking-strategies-rag |

Use for “what tutorials repeat,” not as a substitute for Pinecone/Weaviate/LangChain/LlamaIndex.

---

## Map onto concept files

| File | Primary sources |
|------|-----------------|
| [00-week-overview.md](00-week-overview.md) | Huyen three posts; Pinecone; LangChain recursive; LlamaIndex modules; Weaviate; Kamradt; 2307.03172 |
| [01-fixed-vs-recursive-splitting.md](01-fixed-vs-recursive-splitting.md) | LangChain recursive + character + JS overview; Pinecone fixed vs recursive; Weaviate recursive; Kamradt L1–L2 |
| [02-semantic-chunking.md](02-semantic-chunking.md) | Kamradt `t=1933` + notebook; LlamaIndex `SemanticSplitterNodeParser`; LangChain experimental `SemanticChunker`; Pinecone semantic section |
| [03-agentic-llm-chunking.md](03-agentic-llm-chunking.md) | Weaviate agentic/LLM/late/post-chunk; Kamradt L5; **Anthropic contextual retrieval**; arXiv 2409.04701 + Jina blogs; Pinecone contextual section |
| [04-chunk-size-overlap-tradeoffs.md](04-chunk-size-overlap-tradeoffs.md) | Pinecone sweep + expansion; Weaviate 10–20%; LangChain `chunk_size`/`length_function`; Huyen size-by-latency; 2307.03172; Firecrawl heuristic |
| [05-metadata-per-chunk.md](05-metadata-per-chunk.md) | LlamaIndex extractors + exclude keys; LangChain metadata on splitters; GCP auto-merge; Huyen pitfalls/privacy |
| [06-tables-code-structured-content.md](06-tables-code-structured-content.md) | Pinecone/Weaviate structure; LangChain MD/HTML/code/JSON; LlamaIndex `CodeSplitter`; Docling |

---

## Syllabus PDF

- AQ AI Engineer FDE Syllabus (uploaded): Week 6 ingest pipeline — type detect → structure-aware split → else recursive ~512 embedder tokens / ~10–20% overlap → metadata → persist.

---

## Explicitly unused

- Chip Huyen *AI Engineering* book text from pirate mirrors (pdfcoffee, libgen, etc.).
- Unofficial “full book PDF” dumps. Public `huyenchip.com` posts only.
