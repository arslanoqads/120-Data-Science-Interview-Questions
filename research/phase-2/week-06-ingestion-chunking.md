# Week 6 — Ingestion & Chunking

> RAW SOURCE MATERIAL for AI Engineer / FDE curriculum. Legal sources only (official docs, vendor blogs, arXiv, public talks). Chip Huyen via public blog only.

---

## Concept 1: Fixed-size vs recursive character splitting (why recursive is the sane default)

### Fundamentals
Fixed-size chunking cuts text every N characters or tokens (optionally with overlap), ignoring sentence and paragraph boundaries. Recursive character splitting tries a hierarchy of separators—typically `["\n\n", "\n", " ", ""]`—and only falls back to finer separators when a piece still exceeds `chunk_size`. That keeps paragraphs together when possible, then sentences, then words, instead of bisecting mid-thought.

LangChain documents `RecursiveCharacterTextSplitter` as **the recommended splitter for generic text** precisely because it preserves the strongest semantic units available under a size budget.

### Alternatives & Tradeoffs
| Approach | Pros | Cons |
|----------|------|------|
| Fixed-size | Trivial, predictable lengths, cheap | Mid-sentence cuts; orphaned pronouns/tables |
| Character splitter (single separator) | Slightly structure-aware if separator is `\n\n` | One separator is brittle across corpora |
| Recursive character | Structure-first, still O(text) string work, no model calls | Still size-driven; weak on docs without newlines |
| Document-specific (Markdown/HTML/code) | Aligns with real structure | Needs format routing |

Pinecone notes fixed-size as a common starting path and recursive as a “great middle ground” between naive character splits and semantic splitters while still enforcing size limits.

### Necessity
If you skip structure-aware splitting, retrieval returns half-sentences and severed definitions. Embeddings of broken spans dilute meaning; the LLM then answers from incomplete evidence. Chip Huyen’s platform post frames chunking as required so external memory fits embedding/context budgets—bad chunks → bad retrieved context → bad generation.

### Industry Practice
**Common:** `RecursiveCharacterTextSplitter` (LangChain) or LlamaIndex `SentenceSplitter` with ~400–512 token targets.  
**Strong:** Format routers (Markdown headers → code AST → recursive fallback); measure recall on a golden query set before changing strategy. Greg Kamradt’s “5 Levels of Text Splitting” treats recursive as Level 2—the practical baseline before semantic/agentic spend.

### Concrete Scenario
LangChain’s recursive splitter guide demonstrates splitting the State of the Union with `chunk_size=100`, `chunk_overlap=20`, default separators—chunks break at paragraph/sentence boundaries rather than arbitrary character offsets:  
https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter

Pinecone’s chunking guide walks fixed-size → recursive → structure-based → semantic progression:  
https://www.pinecone.io/learn/chunking-strategies/

### Open Questions
- Should “sane default” be measured in **tokens of the embedding tokenizer** rather than characters?
- When is page-level PDF chunking (NVIDIA-style benchmarks cited in industry writeups) better than recursive for scanned enterprise PDFs?
- Does late chunking / contextual retrieval reduce the need for careful recursive separators?

### Sources
- https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
- https://docs.langchain.com/oss/python/integrations/splitters/character_text_splitter
- https://www.pinecone.io/learn/chunking-strategies/
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://youtu.be/8OJC21T2SL4 (Greg Kamradt — 5 Levels of Text Splitting)

---

## Concept 2: Semantic chunking

### Fundamentals
Semantic chunking embeds consecutive sentences (often with a small buffer window), measures embedding distance between neighbors, and places chunk boundaries where distance spikes—topic shifts—rather than at a global character count. Thresholds are typically percentile, standard deviation, or interquartile of those distances (LangChain `SemanticChunker` / Kamradt method).

### Alternatives & Tradeoffs
| Choice | Upside | Downside |
|--------|--------|----------|
| Recursive only | Cheap, stable sizes | May join unrelated adjacent sections |
| Semantic | Topic-coherent chunks; can lift recall a few points | Embed every sentence at ingest; variable chunk sizes; threshold tuning |
| Proposition / factoid chunking | Atomic claim units | Extra LLM/NLP pipeline cost |
| Hierarchical (small leaves + parent merge) | Precision at leaf, context at parent | Index + retrieval complexity |

Empirically, community writeups often report recursive already near semantic on well-headed docs; semantic shines on long prose without clear markup.

### Necessity
Without some semantic or structural coherence, a chunk can mix two topics so the embedding is a mushy average—neither topic retrieves reliably. Semantic chunking is one way to enforce “one idea per vector.”

### Industry Practice
**Common:** Skip until recursive + eval shows boundary failures.  
**Strong:** Use semantic (or Anthropic-style contextual enrichment) on narrative corpora; keep recursive for structured wikis/docs; always cap max chunk size so oversized “topics” still fit embedding windows. Pinecone documents the Kamradt-style pipeline and points to experimental tooling.

### Concrete Scenario
Greg Kamradt’s public notebook/video introduces Level 4 semantic splitting via embedding distance walks; LlamaIndex adapted it as a Semantic Chunker pack citing the same talk:  
https://youtu.be/8OJC21T2SL4?t=1933  
https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb  
Pinecone overview: https://www.pinecone.io/learn/chunking-strategies/

### Open Questions
- Is percentile-95 always portable across embedding models, or must thresholds be retuned per embedder?
- How do variable-length semantic chunks interact with ANN indexes that prefer uniform payloads?
- Late chunking / contextual retrieval vs semantic boundaries—complementary or redundant?

### Sources
- https://www.pinecone.io/learn/chunking-strategies/
- https://youtu.be/8OJC21T2SL4
- https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://www.firecrawl.dev/blog/best-chunking-strategies-rag

---

## Concept 3: Agentic / LLM-based chunking for structured documents

### Fundamentals
LLM-based chunking asks a model to propose breakpoints (e.g., “where does the topic shift?”) or to group propositions. **Agentic chunking** goes further: an agent inspects document type, structure, and density, then **selects or mixes strategies** (Markdown-by-header vs propositional vs page-level) and may attach metadata. Kamradt’s Level 5 frames this as viable when token cost trends down.

Weaviate’s chunking blog describes agentic chunking as dynamically deciding strategy from whole-document structure—not one prompt for every file.

### Alternatives & Tradeoffs
| Method | Cost | Best for |
|--------|------|----------|
| Recursive / Markdown / Code splitters | Low | Known formats, high volume |
| Single-prompt LLM breakpoints | Medium | Messy narrative PDFs |
| Agentic per-doc routing | High | Heterogeneous enterprise corpora |
| Contextual retrieval (Anthropic pattern: LLM writes chunk context from full doc) | High but cacheable | Long docs where local chunks lose global meaning |

### Necessity
Structured enterprise packs (10-Ks, SOPs, runbooks, mixed Markdown+tables) defeat one-size recursive rules. Wrong strategy on the wrong MIME type is a silent quality regression—agentic routing is how you avoid applying sentence splits to Python modules.

### Industry Practice
**Common:** Hand-written routers by file extension (`*.md` → header splitter, `*.py` → AST/`CodeSplitter`, PDF → page or layout parser).  
**Strong:** LLM-assisted structure extraction + metadata; evaluate cost per million tokens ingested. Production teams often stop at “smart routing” without a full agent loop unless corpus variance is extreme.

### Concrete Scenario
Weaviate’s “Chunking Strategies to Improve LLM RAG Pipeline Performance” contrasts document-structure splitters with agentic chunking that picks strategy per document:  
https://weaviate.io/blog/chunking-strategies-for-rag  

Kamradt Level 5 agentic splitting in the same 5-levels notebook/talk:  
https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb

### Open Questions
- Can cheaper classifiers (MIME + heuristics) replace LLM agents for 90% of routing?
- How do you version agentic chunk decisions for reproducibility/evals?
- Should agents chunk, or only **label structure** for deterministic splitters?

### Sources
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb
- https://www.pinecone.io/learn/chunking-strategies/ (contextual chunking with LLMs / Anthropic contextual retrieval mention)
- https://machinelearningmastery.com/essential-chunking-techniques-for-building-better-llm-applications/

---

## Concept 4: Chunk size & overlap tradeoffs (~400–512 tokens, 10–20% overlap)

### Fundamentals
Chunk size trades **granularity** (small → precise match, less context) against **completeness** (large → more context, noisier embedding). Overlap is a sliding window so ideas straddling boundaries appear in both neighbors. Industry starting heuristic often cited: **~400–512 tokens** with **10–20% overlap** (e.g., 50–100 tokens on a 500-token chunk).

Chip Huyen: chunk size should reflect model context limits and latency; she points practitioners to Pinecone/LangChain/LlamaIndex/Kamradt rather than a single magic number.

### Alternatives & Tradeoffs
| Setting | Argue for | Argue against |
|---------|-----------|---------------|
| 128–256 tokens | High precision FAQ / sentence embedders | Fragments procedures; more vectors = cost |
| **400–512 tokens** | Fits many embedders; good prose paragraphs | May still split tables/code poorly |
| 1024+ tokens | Richer local context | Diluted embeddings; lost-in-middle risk later |
| 0% overlap | Smaller index | Boundary information loss |
| **10–20% overlap** | Cheap insurance against boundary cuts | Duplicate vectors; slight retrieval bias to overlapped phrases |
| >30% overlap | Rare hard boundary cases | Index bloat, redundant rerank candidates |

**Argue against the “default”:** If queries are highly lexical (error codes), smaller chunks + hybrid search beat large overlapping prose chunks. If you use parent-document / auto-merging retrieval, leaf chunks can be smaller because parents restore context.

### Necessity
Wrong size is the most common silent RAG failure: too small → incomplete answers; too large → retrieval of vaguely related walls of text that crowd the prompt (and worsen lost-in-the-middle).

### Industry Practice
**Common:** 512 / 50 or 1000 chars / 200 overlap copied from tutorials.  
**Strong:** Sweep {256, 512, 1024} × {0%, 10%, 20%} on a labeled query set; separate size for code vs prose; use chunk expansion (fetch neighbors) instead of huge overlaps (Pinecone).

### Concrete Scenario
Pinecone recommends testing ranges including 128/256 (granular) and 512/1024 (more context), then evaluating with representative queries—not one global constant:  
https://www.pinecone.io/learn/chunking-strategies/  

Firecrawl’s industry summary explicitly cites recursive **400–512 tokens with 10–20% overlap** as the usual starting point:  
https://www.firecrawl.dev/blog/best-chunking-strategies-rag

### Open Questions
- Should overlap be defined in **tokens of the embedder** or characters?
- Does contextual retrieval make large overlaps obsolete?
- How should size interact with multimodal / table-as-image chunks?

### Sources
- https://www.pinecone.io/learn/chunking-strategies/
- https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html (chunking phase of RAG; context efficiency)

---

## Concept 5: Metadata attachment per chunk

### Fundamentals
Each chunk (LangChain `Document`, LlamaIndex `Node`) should carry metadata: `source`, `page`, `section/header_path`, `doc_id`, `created_at`, ACL/tenant, content type, and optionally LLM-extracted titles/keywords/questions. Metadata enables **filtered retrieval**, citations, and permissioning—not just prettier logs.

LlamaIndex: children inherit parent document attributes; `MarkdownNodeParser` can store header paths; extractors (`TitleExtractor`, `KeywordExtractor`, `SummaryExtractor`, …) enrich nodes in an ingestion pipeline.

### Alternatives & Tradeoffs
| Approach | Benefit | Cost |
|----------|---------|------|
| Propagate file path + page only | Cheap, essential for citations | Weak filtering |
| Header path / section breadcrumbs | Improves grounding & filters | Needs structured parse |
| LLM metadata extractors | Rich facets for hybrid filters | Latency + $ at ingest |
| Embed metadata into text | Helps bi-encoder “see” titles | Pollutes vector; version carefully |

### Necessity
Without metadata you cannot: cite page numbers, scope search to a product version, enforce tenant isolation, or debug which PDF produced a hallucination. Filter failure often looks like “bad embeddings” when the real bug is missing `version=2024-Q3`.

### Industry Practice
**Common:** `{source, page}` from PDF loaders.  
**Strong:** Hierarchical relationships (prev/next, parent), ACL fields used as **pre-filters** in the vector DB, separate embed vs LLM metadata visibility (LlamaIndex `excluded_embed_metadata_keys` / `excluded_llm_metadata_keys` pattern).

### Concrete Scenario
LlamaIndex metadata extraction guide chains `SentenceSplitter` with title/keyword/summary/entity extractors and shows enriched node metadata used downstream:  
https://developers.llamaindex.ai/python/framework/module_guides/indexing/metadata_extraction/

Google Cloud + LlamaIndex writeup on hierarchical nodes / auto-merging (structure in metadata/relationships):  
https://cloud.google.com/blog/products/ai-machine-learning/llamaindex-for-rag-on-google-cloud

### Open Questions
- What metadata should be embedded vs filtered-only?
- How to keep metadata consistent under re-chunking / partial re-ingest?
- PII in metadata—index risk vs retrieval utility?

### Sources
- https://developers.llamaindex.ai/python/framework/module_guides/indexing/metadata_extraction/
- https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/
- https://cloud.google.com/blog/products/ai-machine-learning/llamaindex-for-rag-on-google-cloud
- https://docs.langchain.com/oss/python/integrations/splitters/character_text_splitter (metadata propagation via `create_documents`)
- https://weaviate.io/blog/chunking-strategies-for-rag

---

## Concept 6: Handling tables, code, and structured content differently from prose

### Fundamentals
Prose splitters assume linear narrative. **Tables** lose meaning when rows separate from headers; **code** breaks when functions split mid-body; **HTML/Markdown** carry hierarchy in tags/headers. Use structure-aware parsers: Markdown/HTML header splitters, AST/`CodeSplitter`, table-as-whole or row-with-header-replay, JSON/element parsers.

Weaviate and Pinecone both recommend document-structure-based chunking (Markdown headings, HTML tags, code fences, LaTeX environments) instead of blind character cuts.

### Alternatives & Tradeoffs
| Content | Prefer | Avoid |
|---------|--------|-------|
| Markdown/docs | Header-based nodes + recursive fallback | Fixed 500-char cuts across `#` sections |
| Code | Language-aware AST / `def`/`class` separators | Sentence tokenizers |
| Tables | Keep table intact; or serialize row + column headers; or table→summary LLM | Splitting mid-row |
| PDFs with layout | Layout/OCR-aware + page-level candidates | Plain text dump + recursive only |
| Mixed notebooks | Cell-level chunks | Concatenate all cells then fixed-size |

### Necessity
A half-function or headerless table row embeds into nonsense; hybrid/lexical search may still find the token, but the LLM cannot execute or interpret incomplete structure—classic “retrieval looked fine, answer wrong” failure.

### Industry Practice
**Common:** One recursive splitter for everything.  
**Strong:** MIME/type router; LlamaIndex/LangChain code & markdown parsers; store table HTML/CSV in metadata while embedding a textual summary; for code RAG, chunk by symbol and index `symbol_name` metadata for BM25.

### Concrete Scenario
Pinecone “document structure-based chunking” section covers PDF/HTML/Markdown/LaTeX-aware splits:  
https://www.pinecone.io/learn/chunking-strategies/  

Weaviate chunking strategies: split by Markdown `#` / HTML tags; LangChain & LlamaIndex specialized splitters for Markdown, code, JSON:  
https://weaviate.io/blog/chunking-strategies-for-rag  

LlamaIndex `CodeSplitter` / `MarkdownNodeParser` docs:  
https://developers.llamaindex.ai/typescript/framework/modules/data/ingestion_pipeline/transformations/node-parser/

### Open Questions
- Table-as-image multimodal embeddings vs text serialization—when is each worth it?
- Should code retrieval use dual indexes (dense docstring + sparse identifier)?
- How to chunk deeply nested JSON APIs for agent tool use?

### Sources
- https://www.pinecone.io/learn/chunking-strategies/
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://developers.llamaindex.ai/typescript/framework/modules/data/ingestion_pipeline/transformations/node-parser/
- https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- https://huyenchip.com/2024/07/25/genai-platform.html

---

## Week 6 synthesis notes (for later curriculum writing)

1. **Default path:** format detect → structure splitter when possible → else recursive ~512 tok / ~10–20% overlap → attach rich metadata.  
2. **Escalate cost:** semantic → LLM contextual → agentic only when evals demand it.  
3. **Huyen framing (public blog):** chunking is mandatory for external memory; combine term-based + embedding retrieval later (Week 7); don’t over-invest in vectordb choice before chunk quality exists (`ai-engineering-pitfalls`).

### Cross-cutting sources
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html
