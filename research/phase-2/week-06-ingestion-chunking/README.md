# Week 6 Research Corpus — RAG ingestion & chunking

> Phase 2 — RAG Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; Chip Huyen via public blog only (no pirated book).

This directory is the Week 6 research repository. Read concept files in order, then the source map.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Syllabus mapping: chunk quality as the RAG quality floor before retrieval (Week 7) |
| 01 | [01-fixed-vs-recursive-splitting.md](01-fixed-vs-recursive-splitting.md) | Fixed-size vs recursive character splitting; recursive as sane default |
| 02 | [02-semantic-chunking.md](02-semantic-chunking.md) | Kamradt-style embedding-distance breakpoints; LangChain / LlamaIndex adapters |
| 03 | [03-agentic-llm-chunking.md](03-agentic-llm-chunking.md) | LLM breakpoints, agentic strategy routing, Anthropic contextual retrieval, late chunking |
| 04 | [04-chunk-size-overlap-tradeoffs.md](04-chunk-size-overlap-tradeoffs.md) | ~400–512 tokens, 10–20% overlap debate; sweeps, expansion vs overlap |
| 05 | [05-metadata-per-chunk.md](05-metadata-per-chunk.md) | Per-chunk metadata, extractors, embed vs LLM visibility, filters/ACL |
| 06 | [06-tables-code-structured-content.md](06-tables-code-structured-content.md) | Markdown/HTML/code/tables/JSON vs prose splitters |
| — | [99-source-map.md](99-source-map.md) | Master URL / YouTube / arXiv index |

## Completeness checklist (Week 6)

- [x] All syllabus Week 6 concepts covered with 7 required fields  
- [x] Fixed-size vs recursive character splitting; LangChain recursive as recommended generic default  
- [x] Semantic chunking (Kamradt 5 levels Level 4; LlamaIndex `SemanticSplitterNodeParser`; Pinecone writeup)  
- [x] Agentic / LLM-based chunking vs cheap MIME routers; contextual retrieval vs late chunking  
- [x] Chunk size & overlap: **400–512 tokens, 10–20% overlap** as starting heuristic *and* the case against it  
- [x] Metadata attachment per chunk (LlamaIndex extractors; LangChain `create_documents`; embed vs filter-only)  
- [x] Tables, code, Markdown/HTML/JSON handled differently from prose  
- [x] LangChain + LlamaIndex + Pinecone chunking docs cited  
- [x] Chip Huyen **public blog only** (`genai-platform`, `llm-research-open-challenges`, `ai-engineering-pitfalls`) — no book scrape  
- [x] Greg Kamradt “5 Levels of Text Splitting” YouTube + public notebook cited  
- [x] arXiv where relevant (late chunking 2409.04701; lost-in-the-middle 2307.03172)  
- [x] AI/RAG-service-specific failure modes noted per concept  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 6)

Ship an **ingestion pipeline** for the FastAPI RAG chatbot: detect document type → structure-aware split when possible → else recursive **~512 embedding-tokenizer tokens / ~10–20% overlap** → attach `source`, `page`/`header_path`, `doc_id`, tenant/ACL, content type → persist chunks with stable IDs. Escalate to semantic, contextual prefixes, or agentic routing **only** when a labeled query set shows boundary failures. Do not skip this week for “just dump PDFs into a vector DB.” Week 7 retrieval cannot rescue mushy or headerless chunks.

## Default path (synthesis)

1. Format detect → Markdown/HTML/code/JSON/table parser when possible.  
2. Else recursive character (or LlamaIndex `SentenceSplitter`) sized in **embedder tokens**, not naive characters.  
3. Attach rich metadata; exclude ACL/PII from embed text.  
4. Eval sweep `{256, 512, 1024} × {0%, 10%, 20%}` before changing strategy.  
5. Semantic → LLM contextual → agentic only when evals demand it.
