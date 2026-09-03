# 00 — Week overview & syllabus mapping

> Week 6 — Ingestion & Chunking  
> Research notes (raw).

---

## Fundamentals

Week 6 is the **quality floor** of Phase 2 RAG. Weeks 4–5 gave a provider-agnostic client and versioned prompts. Week 6 decides **what vectors exist at all**. Retrieval (Week 7), reranking (Week 8), failure taxonomies (Week 9), and evals (Week 10) all operate on the units produced here. A perfect hybrid retriever over half-sentences and headerless table rows still fails.

Chip Huyen’s public platform post is explicit: RAG exists because naively stuffing whole documents into context is unbounded; documents must be split into **manageable chunks** whose size is set by embedding/context limits and latency. She does **not** prescribe a magic number—she points practitioners at Pinecone, LangChain, LlamaIndex, and Greg Kamradt. Her 2023 open-challenges post names **chunking (indexing)** as phase 1 of RAG: gather docs → divide into chunks → embed → store. Longer context windows do not retire this step: *how much context a model can use* ≠ *how efficiently it uses it* (lost-in-the-middle, Liu et al. 2023).

Pinecone’s 2025 chunking guide adds the two embedding constraints: (1) every embedder has a context window—overflow is truncated, so important tokens never enter the vector; (2) a chunk that is not independently meaningful will not surface at query time. Their human test: **if a chunk makes sense without surrounding context to a human, it will make sense to the model.** Weaviate restates the dual objective: chunks must be **findable** (precise embeddings) and **usable** (enough context for generation).

The syllabus spine:

1. **Fixed vs recursive splitting** — why recursive is the sane generic default.  
2. **Semantic chunking** — embedding-distance topic breaks when markup is weak.  
3. **Agentic / LLM chunking** — per-doc strategy selection and contextual prefixes.  
4. **Size & overlap** — the 400–512 token / 10–20% overlap heuristic and when to reject it.  
5. **Metadata per chunk** — citations, filters, ACL, embed vs LLM visibility.  
6. **Structured content** — tables, code, Markdown/HTML/JSON are not prose.

These six are one pipeline: **choose a splitter that respects structure** → **size to the embedder and query shape** → **label every chunk** → **route special MIME types**. Skipping any step shows up as “the vector DB is bad” when the real bug is ingestion.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Dump whole PDFs / skip chunking | Demo speed; “long context will save us” | Truncation, lost-in-middle, cost, unusable citations |
| One global `CharacterTextSplitter` | Predictable lengths | Mid-sentence cuts; orphaned pronouns |
| Recursive only (syllabus default) | Cheap, structure-first, O(text) | Weak on unmarked prose; still size-driven |
| Semantic / LLM / agentic first | Topic coherence / format routing | Ingest $ and latency; variable sizes; irreproducible without versioning |
| Huge overlap instead of expansion | Cheap insurance at ingest | Index bloat; duplicate retrieval bias |
| Tiny leaves + parent merge (hierarchical) | Precision + restore context at generate | Index + retriever complexity (LlamaIndex auto-merge) |

For the flagship RAG chatbot, Week 6 should prefer **format router + recursive/sentence fallback + metadata**, with a **measured** size/overlap sweep. Do not start at agentic chunking. Huyen’s pitfalls post: start too complex, abstract away the details you need to debug.

---

## Necessity

Concrete failure modes if Week 6 is skipped:

- Embeddings of broken spans dilute meaning; generation answers from incomplete evidence.  
- Two topics in one vector → mushy average; neither topic retrieves.  
- Headerless table rows and half-functions look “retrieved” but cannot be interpreted.  
- No `source`/`page`/`version` → cannot cite, cannot filter Q3 docs from Q4, cannot enforce tenant ACL.  
- Copied tutorial `chunk_size=1000, chunk_overlap=200` **characters** while the embedder thinks in **tokens**.  
- Over-investing in vector DB choice before chunk quality exists (Huyen: don’t start too complex).

---

## Industry Practice

- **Common (demo AI):** one `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` on concatenated PDF text; `{source}` metadata only.  
- **Strong:** MIME/type router; recursive or `SentenceSplitter` in **embedder tokens**; header path + page + `doc_id`; sweep sizes on a golden query set; chunk **expansion** (neighbors) instead of huge overlap (Pinecone).  
- **FDE bar:** can explain why Pinecone still says start with fixed-size *then* iterate; why LangChain documents recursive as the generic recommended splitter; when Kamradt Level 4/5 is worth the embed/LLM cost; why Anthropic contextual prefixes and Jina-style late chunking solve different problems (text augmentation vs pooling over long-context token states).

Kamradt’s “5 Levels of Text Splitting” is the industry shared vocabulary: Level 1 character → 2 recursive → 3 document-structure → 4 semantic → 5 agentic.

---

## Concrete Scenario

Syllabus build: load product runbooks + Markdown docs + a few Python snippets. Route `*.md` through `MarkdownHeaderTextSplitter` then recursive fallback; `*.py` through `RecursiveCharacterTextSplitter.from_language(Language.PYTHON)` or LlamaIndex `CodeSplitter`; remaining prose through recursive **512 tokens / ~10% overlap** using the embedding tokenizer as `length_function`. Each `Document`/`Node` carries `source`, `header_path` or `symbol_name`, `doc_id`, `ingested_at`. A 20-query golden set fails on two “policy vs procedure” collisions → try semantic only on the long unmarked FAQ corpus, not on headed wikis.

Related public bar: Pinecone chunking strategies walkthrough (fixed → recursive → structure → semantic → contextual); Kamradt talk at ~32:13 for semantic (YouTube `t=1933`); Anthropic contextual retrieval failure-rate reductions when prefixes + BM25 + rerank.

URL: https://www.pinecone.io/learn/chunking-strategies/  
Companions: https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter · https://huyenchip.com/2024/07/25/genai-platform.html · https://youtu.be/8OJC21T2SL4

---

## Open Questions

- Should “sane default” always be **tokens of the embedding tokenizer**, never characters? (LangChain recursive still documents character `length_function=len` in the canonical demo.)  
- Do long-context generation models retire chunking, or only change the **generate** window while retrieval still needs small units? (Pinecone: un-chunked docs may fit Claude/o-class windows; lost-in-middle and latency remain.)  
- Git vs object-store as source of truth for **chunker version** (`splitter_id`, separator list, token model)—same debate as Week 5 prompts.  
- When does post-chunking at query time (Weaviate/Elysia) beat pre-chunked indexes for sparse-query corpora?

---

## Sources

- Syllabus PDF (uploaded): AQ AI Engineer FDE Syllabus  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html  
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html  
- https://www.pinecone.io/learn/chunking-strategies/  
- https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter  
- https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/  
- https://weaviate.io/blog/chunking-strategies-for-rag  
- https://youtu.be/8OJC21T2SL4  
- https://arxiv.org/abs/2307.03172  
