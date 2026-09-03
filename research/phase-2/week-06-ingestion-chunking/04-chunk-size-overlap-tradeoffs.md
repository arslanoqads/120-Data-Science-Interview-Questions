# 04 — Chunk size and overlap tradeoffs

> Week 6 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

**Chunk size** trades **granularity** (small → precise match, less self-contained context) against **completeness** (large → more local context, noisier embedding). Pinecone: too small or too large both produce imprecise search or missed content. Weaviate: oversized chunks mix topics into an averaged vector; undersized chunks fail the “makes sense alone” test and starve the generator.

**Overlap** is a sliding window so an idea that straddles a cut appears in both neighbors. Weaviate’s fixed-size section treats **10–20%** overlap as the typical starting band. Industry blogs (Firecrawl summarizing recursive defaults) repeat **~400–512 tokens with 10–20% overlap** as the usual first setting. That is a **heuristic**, not a law.

Chip Huyen (public platform post): chunk size should reflect **model context limits and application latency**; she refuses a magic number and points to Pinecone, LangChain, LlamaIndex, and Kamradt. Open-challenges (2023): RAG phase 1 is chunking/indexing; longer windows let you *squeeze more chunks into generation*, which is not the same as using them well. Liu et al. (arXiv 2307.03172) **lost-in-the-middle**: models use beginnings and ends of long contexts better than the middle. Pinecone 2025: even when o1 / Claude 200k can *fit* un-chunked docs, large blobs raise latency/cost and still suffer lost-in-middle. The fix is passing an **optimal amount** of information downstream—not the whole PDF.

**Units.** LangChain recursive docs: `chunk_size` is whatever `length_function` returns. Canonical demo uses `len` (characters). Embedders think in **tokens**. A 1000-character English paragraph ≈ 200–300 tokens; the same length of Python or CJK is a different count. Production size/overlap **must** be in **embedding-tokenizer tokens**. Overlap of 200 *characters* on a 1000-character tutorial copy is not 20% of what the embedder saw.

**Embedder windows are a hard ceiling.** Overflow is truncated (Pinecone). A “1024-token chunk” that is actually 1800 tokenizer tokens silently drops the tail—the worst kind of overlap failure, because you think the table footer is in the vector.

**Query shape.** Pinecone’s decision list: document length/structure, embedder domain, **expected query length/complexity**, and downstream use (human search snippet vs RAG vs agent tool context). Short error-code queries want small lexical units; “summarize the refund procedure” wants a complete section.

---

## Alternatives & Tradeoffs

| Setting | Argue for | Argue against |
|---------|-----------|---------------|
| 128–256 tokens | High precision FAQ; sentence-oriented embedders; error codes | Fragments multi-step procedures; more vectors = storage + ANN + $ |
| **400–512 tokens** | Fits many embedders; ~few prose paragraphs; Firecrawl/Weaviate starting band | Still splits tables/code; not sacred |
| 1024+ tokens | Richer local context; fewer vectors | Diluted embeddings; more lost-in-middle *inside the chunk* at generate if you also retrieve many |
| 0% overlap | Smaller index; no duplicate bias | Boundary information loss on size-driven splitters |
| **10–20% overlap** | Cheap insurance when cuts ignore semantics | Duplicate vectors; overlapped phrases rank twice |
| >30% overlap (OpenAI Assistants-style 50% on 800/400 appears in community benches) | Rare pathological boundaries | Index bloat; rerank sees clones; some public benches show **worse** precision than modest overlap |
| Huge overlap instead of **expansion** | All context in the index | Pays storage forever for a query-time problem |

**Argue against the 512/15% default:**

- Highly **lexical** queries (SKU, exception class): smaller chunks + hybrid/BM25 beat large overlapping prose (Week 7).
- **Parent-document / auto-merging** (LangChain ParentDocumentRetriever; LlamaIndex hierarchical / auto-merge): **leaf** chunks can be 128–256 because **parents** restore context at generate. Overlap on leaves is often wasted.
- **Chunk expansion** (Pinecone): retrieve neighbors (paragraph, page, whole doc) **at query time**. Couple a moderate ingest size with expansion instead of 40% overlap.
- **Contextual prefixes** (concept 03): situating text can replace some overlap that existed only to carry the section title across a cut.
- **Structure-aware splitters**: if every chunk is already a full `##` section under the size cap, overlap **does not cross sections** (LangChain markdown docs: overlap applies only when a *single section* is recursively split). Setting `chunk_overlap=200` and seeing no overlap is expected.

Pinecone’s recommended **sweep**, not a constant: smaller 128/256 for granularity **and** 512/1024 for context, evaluated with **representative queries**, using multiple indices or namespaces.

---

## Necessity

Wrong size is the most common **silent** RAG failure:

- Too small → incomplete answers, “the bot stopped mid-procedure.”
- Too large → vaguely related walls of text crowd the prompt, attention dilutes, lost-in-middle (Weaviate lists this explicitly; Liu et al. measured it).
- Character/token mismatch → you think you are at 512 and you are at 900; truncation; or you think you overlap 20% and you overlap 5% of tokens.
- Copy-paste `chunk_size=1000, chunk_overlap=200` from LangChain’s **character** demo onto a **token** embedder without reading `length_function`.

Skipping a sweep means Week 10 evals attribute gains to “hybrid search” that were actually “we accidentally used 256-token chunks.” Huyen pitfalls: do not skip the boring control.

If you skip overlap *and* skip expansion *and* use fixed-size cuts, boundary straddles disappear from every vector. Recursive/header splitters reduce that need; they do not zero it for leftover oversized sections.

---

## Industry Practice

**Common:** 512/50 tokens *or* 1000/200 characters copied from the nearest tutorial. One global constant for code, tables, and prose.

**Strong:**

- Sweep `{256, 512, 1024} × {0%, 10%, 20%}` on a **labeled** query set (Pinecone procedure). Record hit@k, MRR, and a human “is the evidence complete?” flag.
- Separate budgets: prose vs code vs tables (concept 06). A 512-token function may be too small; a 512-token FAQ may be too large.
- Size in **embedder tokens**; store `token_count`, `tokenizer_name` in metadata.
- Prefer **expansion / parent merge** over >20% overlap once the index is large.
- Watch **duplicate retrieval**: if top-5 are three near-clones from overlap, lower overlap or add diversity / MMR later (Week 7–8).
- Re-run the sweep when the **embedder** changes (different tokenizer, different optimal length).
- For agents (Pinecone): chunks consume session context; oversized chunks waste tool-calling budget.

Firecrawl’s 2026 roundup is a useful *secondary* industry snapshot (recursive 400–512 / 10–20% as default; page-level cited as strong on paginated PDFs; semantic as costlier recall lift)—not a substitute for your golden set.

---

## Concrete Scenario

Pinecone: pick a range including 128/256 and 512/1024, embed into namespaces, run the same queries, iterate. There is no one-size-fits-all.

https://www.pinecone.io/learn/chunking-strategies/

LangChain recursive parameters (`chunk_size`, `chunk_overlap`, `length_function`)—read this before copying 1000/20 from the State-of-the-Union toy:

https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter

Weaviate: 10–20% overlap on fixed-size; dual objective findable vs usable; lost-in-middle if generation context is too long:

https://weaviate.io/blog/chunking-strategies-for-rag

Lost-in-the-middle paper (why stuffing 1024-token × k=20 is not “more context is better”):

https://arxiv.org/abs/2307.03172

Huyen on sizing by context + latency, and on chunking as RAG phase 1:

https://huyenchip.com/2024/07/25/genai-platform.html  
https://huyenchip.com/2023/08/16/llm-research-open-challenges.html

Syllabus pipeline: recursive **512 embedding tokens / ~10% overlap** as the **prose fallback**; sweep on 20 golden queries before touching Week 7. If procedure questions fail completeness, try 1024 or parent expansion—not 40% overlap.

---

## Open Questions

- Should overlap always be defined in **embedder tokens**, never characters? (Yes for dense index; BM25 may still care about character windows.)
- Do contextual retrieval / late chunking make large overlaps obsolete?
- How should size interact with **multimodal** table-as-image chunks (pixels ≠ tokens)?
- Is page-level chunking a size policy (one page ≈ N tokens) or a structure policy? What if pages are 80 tokens of headers?
- For hierarchical indexes, what leaf/parent ratio actually shows up in traces (not just blog diagrams)?
- When generation context is 200k, should retrieval chunks shrink further (precision) while expansion grows at generate time?

---

## Sources

- https://www.pinecone.io/learn/chunking-strategies/
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
- https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/
- https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://arxiv.org/abs/2307.03172
- https://arxiv.org/abs/2409.04701
- https://youtu.be/8OJC21T2SL4
- https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter
