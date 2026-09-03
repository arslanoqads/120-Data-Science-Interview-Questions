# 03 — Agentic / LLM-based chunking, contextual retrieval, late chunking

> Week 6 concept research (deep). Legal sources only. Chip Huyen via public blog only.

---

## Fundamentals

Three different “use an LLM / long model at ingest” ideas get collapsed in Slack. Separate them.

### 1. LLM-based chunking (breakpoints or propositions)

A model reads (a window of) the document and **proposes cuts**, or rewrites text into **propositions** (atomic claims) that become chunks. Weaviate: the LLM identifies propositions, summarizes sections, or highlights key points so chunks preserve meaning better than punctuation rules. Cost: at least one strong-model call per document or per window. Output length is stochastic unless you constrain schema (Week 4 structured outputs).

### 2. Agentic chunking (strategy selection)

Kamradt **Level 5** and Weaviate’s agentic section: an agent inspects **type, structure, density**, then **selects or mixes** strategies—Markdown-by-header vs propositional vs page-level—and may attach metadata tags. It is not “one prompt that splits every file the same way.” It is a **router with tools** (MIME sniff, header count, table density, language). Token-cost trends made this thinkable; it is still the most expensive ingest path.

In practice, 90% of the value is a **deterministic MIME router** (concept 06) plus a few heuristics (`heading_density`, `code_fence_ratio`). The agent is justified when the corpus is heterogeneous *and* heuristics mis-route (scanned PDF that is actually a table pack; `.md` that is really a CSV dump).

### 3. Contextual retrieval (Anthropic, 2024) — text augmentation, not a splitter

Documents are still split by an ordinary chunker. For each chunk, Claude sees **the whole document + the chunk** and writes ~**50–100 tokens** of situating context (“this chunk is from the Q3 enterprise refund policy, not SMB”). That prefix is prepended **before embedding and before BM25**. Prompt caching holds the document while you iterate chunks.

Anthropic’s published reductions on their internal mix (codebases, papers, fiction), top-20-chunk retrieval **failure rate**:

| Stack | Failure rate | Relative reduction vs baseline 5.7% |
|-------|--------------|-------------------------------------|
| Contextual embeddings only | 3.7% | ~35% |
| Contextual embeddings + contextual BM25 | 2.9% | ~49% |
| Above + rerank | 1.9% | ~67% |

This fixes **anaphora and local ambiguity** (“the policy”, “its”, “Berlin” as a later pronoun). It does **not** choose recursive vs semantic. Pinecone’s 2025 guide describes the same pattern under “Contextual Chunking with LLMs.”

### 4. Late chunking (Günther et al., arXiv 2409.04701; Jina + Weaviate coauthors)

**Architectural change to embedding**, not an LLM editor. Naive path: split → embed each chunk in isolation → pronouns and “the city” lose the antecedent. Late path: run a **long-context** embedding transformer over the whole document (or max window); take **token states**; **mean-pool** those states inside each chunk span. Chunk vectors are conditioned on document context. Requires a mean-pooling long-context embedder (e.g. Jina v2 8k). Does **not** require extra training for the basic method; the paper also proposes dedicated fine-tuning.

Berlin toy example from the paper: naive embeddings of “Its” / “the city” barely match “Berlin”; late-chunked embeddings do, because attention already saw the city name.

**Complementarity:** recursive/semantic/agentic decide *spans*. Contextual retrieval *rewrites/prefixes* chunk text. Late chunking *pools token states* over those spans. You can combine them; you should not treat them as one checkbox named “agentic.”

Huyen (genai-platform): RAG exists because whole-document stuffing is unbounded; she will not prescribe Level 5. Pitfalls: **start too complex**—agentic ingest before a recursive baseline is exactly that.

---

## Alternatives & Tradeoffs

| Method | Cost at ingest | Best for | Failure mode |
|--------|----------------|----------|--------------|
| Recursive / Markdown / Code splitters | Low, deterministic | Known formats, high volume | Wrong MIME → silent quality drop |
| MIME + heuristics router | Low | 90% of enterprise packs | Weird files misclassified |
| Single-prompt LLM breakpoints | Medium, variable sizes | Messy narrative PDFs | Unreproducible cuts; JSON parse fails |
| Propositional LLM rewrite | High | Factoid QA over contracts | Destroys procedure order |
| Agentic per-doc routing | High (many tool/LLM calls) | Extreme heterogeneity | You cannot replay ingest without traces |
| Contextual prefixes (Anthropic) | High but **cacheable** (~$1.02 / M doc tokens in their writeup with caching) | Long docs, pronouns, “this section of that policy” | Prefix drift if the prompt isn’t versioned; PII in prefixes |
| Late chunking | Embed-time compute on long context; no extra LLM | Models with long-context + mean pool; cross-chunk references | Docs longer than embedder window; APIs that do not expose token states |

Weaviate also contrasts **pre-chunking** (async, fast query) vs **post-chunking** (embed whole docs, chunk at query time on retrieved docs, cache—Elysia). Post-chunking is another way to avoid a global ingest strategy; it is not free (first-access latency).

---

## Necessity

Structured enterprise packs (10-Ks, SOPs, runbooks, mixed Markdown+tables+Python) **defeat one recursive rule**. Applying sentence splits to Python modules, or recursive character cuts to 10-column tables, is a silent regression: retrieval “looks busy,” generation is wrong.

You need *some* routing. You do **not** automatically need a Level 5 agent. Necessity ranking:

1. **Must:** do not apply one splitter to all MIME types (concept 06).
2. **Often must:** situate chunks that are locally meaningless (Anthropic’s failure-rate numbers; late chunking’s Berlin example; lost-in-middle if you instead stuff the whole 10-K into the generator—arXiv 2307.03172).
3. **Sometimes:** LLM breakpoints on OCR soup with no headings.
4. **Rarely first:** a full agent loop per file. Huyen: fancy frameworks abstract away the details you need to debug.

If you skip *all* of this and also skip MIME routing, Week 7 hybrid search will still retrieve headerless rows and half-functions.

---

## Industry Practice

**Common:** hand-written `if suffix == ".md"` routers; recursive for everything else. No prefix, no late pooling. Fine for the syllabus chatbot v1.

**Strong:**

- Deterministic router with tests (fixture files per MIME).
- Version `router_id`, `chunker_id`, contextual-prompt hash, embedder id on every chunk (concept 05).
- Contextual retrieval **after** a measured recursive/structure baseline, with prompt caching on the document; combine with BM25 + rerank as Anthropic did—do not ship prefixes alone and call it done.
- Late chunking only if you actually control a long-context mean-pool embedder (self-hosted Jina, or an API that implements 2409.04701). OpenAI `text-embedding-3-*` as a black-box per-string API cannot late-chunk unless the vendor does it server-side.
- Agent: use as a **classifier** (“use CodeSplitter vs MarkdownHeader vs recursive”) that writes a structured label, then run **deterministic** splitters. Do not let the agent emit chunk text if you need eval replay.
- Cost dashboard: $ / million ingested tokens, cache hit rate on contextual prompts, p95 ingest latency per MIME.

Kamradt Level 5 notebook/talk is the cultural reference, not a production spec.

---

## Concrete Scenario

Anthropic’s engineering post is the primary source for prefixes + BM25 + rerank and the 35/49/67% failure-rate ladder:

https://www.anthropic.com/engineering/contextual-retrieval

Cookbook (codebases dataset, cache the file, prepend context, ingest-time cost not per-query HyDE):

https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide

Weaviate contrasts document-structure splitters, LLM-based, **agentic** (whole-document strategy choice), **late chunking**, and pre vs post-chunking:

https://weaviate.io/blog/chunking-strategies-for-rag

Kamradt Level 5 in the 5-levels notebook/talk:

https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb  
https://youtu.be/8OJC21T2SL4

Late chunking paper + Jina implementation:

https://arxiv.org/abs/2409.04701  
https://jina.ai/news/late-chunking-in-long-context-embedding-models  
https://github.com/jina-ai/late-chunking

Syllabus: do **not** start the FastAPI ingest job with an agent. Ship MIME routing + recursive. If golden queries fail on “which policy does ‘it’ refer to?”, add Anthropic-style prefixes on that doc class, version the prompt, cache the document. Consider late chunking only if the embedding stack supports token pooling.

---

## Open Questions

- Can MIME + cheap classifiers replace LLM agents for 90% of routing? (Default bet: yes.)
- How do you version agentic chunk *decisions* for evals? Store the tool transcript, or only the resulting `strategy_id`?
- Should agents chunk, or only **label structure** for deterministic splitters? (Prefer the latter.)
- Contextual retrieval vs late chunking vs both: prefixes help BM25 lexical match; late pooling helps dense match of anaphora. When is one enough?
- Post-chunking (Elysia) vs pre-chunked indexes for sparse-query corpora?
- If generation models have 200k windows, do we still chunk for *retrieval* (Pinecone: yes—latency, cost, lost-in-middle) while passing **expanded parents** at generate time?

---

## Sources

- https://www.anthropic.com/engineering/contextual-retrieval
- https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide
- https://weaviate.io/blog/chunking-strategies-for-rag
- https://www.pinecone.io/learn/chunking-strategies/
- https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/5_Levels_Of_Text_Splitting.ipynb
- https://youtu.be/8OJC21T2SL4
- https://arxiv.org/abs/2409.04701
- https://jina.ai/news/late-chunking-in-long-context-embedding-models
- https://jina.ai/news/what-late-chunking-really-is-and-what-its-not-part-ii
- https://github.com/jina-ai/late-chunking
- https://arxiv.org/abs/2307.03172
- https://huyenchip.com/2024/07/25/genai-platform.html
- https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html
- https://huyenchip.com/2023/08/16/llm-research-open-challenges.html
- https://milvus.io/docs/v2.5.x/contextual_retrieval_with_milvus.md
