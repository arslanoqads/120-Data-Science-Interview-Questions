# 06 — Tables, code, and structured content vs prose

> Week 6 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

Prose splitters (`RecursiveCharacterTextSplitter` defaults, `SentenceSplitter`) assume a **linear narrative** with paragraphs and sentences. **Tables** lose meaning when rows separate from headers. **Code** breaks when a function is cut mid-body. **HTML/Markdown** store hierarchy in tags and ATX headers. **JSON** is a tree, not a novel.

Pinecone “document structure-based chunking” and Weaviate “document-based chunking” say the same thing: for PDF/HTML/Markdown/LaTeX/code, **parse format-specific elements** (headings, tags, fences, environments, functions) instead of blind character cuts. LangChain’s splitter index groups these under **document structure-based** integrations: Markdown, HTML, JSON, code. LlamaIndex node parsers: `MarkdownNodeParser`, `HTMLNodeParser`, `JSONNodeParser`, `CodeSplitter` (AST via tree-sitter; SweepAI lineage).

**MIME/type router** is the production object. Kamradt Level 3 is this layer. Level 5 (agentic) is an expensive way to choose Level 3 tools (concept 03). Huyen pitfalls: start with the boring router, not an agent.

### Markdown / HTML

`MarkdownHeaderTextSplitter`: split on `#` / `##` / …; attach header path as metadata; default **strips** header lines from body (`strip_headers=False` to keep them). Oversized sections → recursive `split_documents` **inside** the section; overlap does **not** cross H1→H2 boundaries.

`HTMLHeaderTextSplitter` is the HTML analog. `HTMLSemanticPreservingSplitter` exists specifically so **tables and lists are not torn across chunks** (headers stay with rows). That is the official LangChain answer to “recursive wrecked my table.”

Weaviate: convert PDFs to **clean Markdown** (OCR if needed) *before* any of these strategies. Columns, headers, scanned pages make naive `pdftotext` + recursive a trap.

### Code

LangChain `RecursiveCharacterTextSplitter.from_language(Language.PYTHON)` uses language-aware separator lists (`class`, `def`, etc.)—still recursive, not a full AST.

LlamaIndex `CodeSplitter`: parse AST; `chunk_lines`, `chunk_lines_overlap`, `max_chars` / `count_mode` `"char"|"token"`, `max_tokens`. Official example walks character vs token limits. Metadata should include `symbol_name`, `language`, `start_line` for BM25 on identifiers (Week 7 hybrid).

Do not run English sentence regex on source (semantic chunker’s documented English bias is a disaster here).

### Tables

Options, in order of integrity:

1. **Keep the table intact** if it fits the embedder window.
2. **Row + replayed column headers** (each row is a mini-record the LLM can interpret).
3. **Embed a textual/LLM summary**; store raw HTML/CSV in metadata or object storage for the generator to fetch by `table_id` (parent-document pattern).
4. **Table-as-image** multimodal embeddings when grid lines beat HTML (scanned 10-K exhibits). Different size units (concept 04).

Never: recursive character split **mid-row**.

### JSON / APIs

LangChain `RecursiveJsonSplitter` splits by object/array structure with a size cap. For agent tool schemas, chunking “the OpenAPI spec” as prose loses method identity—split by **path + method** as the unit, metadata `operation_id`.

### Notebooks

Cell-level chunks (code cells vs markdown cells). Concatenating all cells then fixed-size mixes stdout dumps with functions.

Pinecone/Weaviate human test still applies: a headerless row or half-function does **not** make sense alone, so it will not make sense to the model—even if BM25 found the token.

---

## Alternatives & Tradeoffs

| Content | Prefer | Avoid |
|---------|--------|-------|
| Markdown docs / wikis | Header splitter → recursive fallback; keep `header_path` | Fixed 500-char cuts across `#` sections |
| HTML product pages | Header or semantic-preserving HTML splitter | `get_text()` then recursive |
| Code | AST `CodeSplitter` or `from_language`; symbol metadata | Sentence tokenizers; semantic Level 4 |
| Tables | Whole table / row+headers / summary+raw sidecar | Mid-row character splits |
| PDFs with layout | Layout/OCR → Markdown or page/layout chunks | Plain dump + recursive only |
| LaTeX | Environment/section-aware (Pinecone) | Treating `$` math as separators |
| Nested JSON / OpenAPI | Recursive JSON or per-operation nodes | Pretty-print then `chunk_size=1000` |
| Mixed notebooks | Per-cell, typed metadata | Concatenate then fixed-size |
| One recursive splitter for everything | Demo speed | Every structured failure mode in this table |

**Page-level PDF** (industry summaries of NVIDIA 2024 paginated benchmarks) can beat recursive on *true* paginated reports. It is the wrong unit for a 2-page poster or a 1-token running header. Measure.

**Dual indexes for code:** dense on docstrings/comments; sparse/BM25 on identifiers. Structure chunking supplies the `symbol_name` hook; Week 7 builds the query blend.

---

## Necessity

A half-function or headerless table row **embeds into nonsense**. Hybrid search may still surface the token (`ENOENT`, a SKU). The LLM cannot execute or interpret incomplete structure—classic “retrieval looked fine, answer wrong.”

Concrete RAG-service failures:

- **Support bot** cites a pricing table but the chunk is three cells without column names → it invents units.
- **Code copilot RAG** returns the middle of a `try` without the `except` → hallucinated APIs.
- **Runbook bot** splits a Markdown numbered procedure across chunks without `header_path` → skipped a warning step.
- **Agent tool-use** retrieves a fragment of JSON schema → invalid tool calls (Pinecone: bad chunks → wrong tools, wasted tokens).
- Eval dashboards blame the vector DB (Weaviate’s warning) or the Week 7 retriever.

Skipping the router also poisons **semantic** and **agentic** spend: you will embed-distance-walk a Python file (concept 02) instead of using `CodeSplitter`.

---

## Industry Practice

**Common:** one `RecursiveCharacterTextSplitter` on `Unstructured` / PyPDF text. Tables become whitespace. Code is English.

**Strong:**

- Router by MIME / extension / `content_type` with unit tests (fixtures: `.md`, `.py`, `.html` table, `.json`, scanned PDF).
- LangChain/LlamaIndex specialized parsers; fallback recursive **only** for unmarked prose.
- Store table HTML/CSV in metadata or blob store; embed summary or row records.
- Code: chunk by symbol; index `symbol_name` for BM25; token mode aligned with the embedder.
- PDF: Weaviate advice—Markdown first; consider layout models (Docling has a LangChain integration with `DOC_CHUNKS` vs Markdown export).
- Metadata: `content_type`, `header_path`, `symbol_name`, `table_id` (concept 05).
- Do not apply 400–512 / 10–20% blindly to AST chunks—function size is the unit until `max_chars` forces a split.

Firecrawl’s roundup is a secondary reminder that page-level vs recursive vs semantic is **format-dependent**; your MIME mix is the experiment design.

---

## Concrete Scenario

Pinecone structure section: PDF/HTML/Markdown/LaTeX-aware splits, LangChain utilities, Pinecone Assistant as a hosted “we’ll chunk PDFs” option:

https://www.pinecone.io/learn/chunking-strategies/

Weaviate: split by Markdown `#` / HTML tags; LangChain & LlamaIndex specialized splitters for Markdown, code, JSON; PDF→Markdown preprocessing:

https://weaviate.io/blog/chunking-strategies-for-rag

LangChain Markdown (header metadata, overlap-does-not-cross-sections):

https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter

LangChain HTML (including semantic-preserving tables/lists):

https://docs.langchain.com/oss/python/integrations/splitters/split_html

LangChain code + JSON:

https://docs.langchain.com/oss/python/integrations/splitters/code_splitter  
https://docs.langchain.com/oss/python/integrations/splitters/recursive_json_splitter

LlamaIndex `CodeSplitter` / node parser catalog:

https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/  
https://developers.llamaindex.ai/python/examples/node_parsers/code_splitter_chunking/

Syllabus build: `*.md` → `MarkdownHeaderTextSplitter` then recursive fallback; `*.py` → `from_language(PYTHON)` or `CodeSplitter`; remaining prose → recursive 512 tokens / ~10% overlap. Golden queries that fail on a table mean **fix the table serializer**, not the cosine metric.

---

## Open Questions

- Table-as-image multimodal vs text serialization—when is each worth the embedder swap?
- Dual indexes (dense docstring + sparse identifier) as default for code RAG?
- Deeply nested JSON for agent tools: per-operation nodes vs subgraph retrieval?
- Docling / layout chunkers vs “to Markdown then headers”—eval on *your* PDFs, not NVIDIA’s deck corpus.
- Should notebooks chunk by cell, by symbol *inside* cells, or both with hierarchical parents?
- Late chunking on code files: token pooling across a module vs AST chunks—does “the city” anaphora even exist in code (imports vs uses)?

---

## Sources

- https://www.pinecone.io/learn/chunking-strategies/
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://docs.langchain.com/oss/python/integrations/splitters
- https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter
- https://docs.langchain.com/oss/python/integrations/splitters/split_html
- https://docs.langchain.com/oss/python/integrations/splitters/code_splitter
- https://docs.langchain.com/oss/python/integrations/splitters/recursive_json_splitter
- https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
- https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/
- https://developers.llamaindex.ai/python/examples/node_parsers/code_splitter_chunking/
- https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/node_parser/text/code.py
- https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://youtu.be/8OJC21T2SL4
- https://docs.langchain.com/oss/python/integrations/document_loaders/docling
