# 01 — Retrieval system design for ~10M docs (mixed query types)

> Week 23 — System design interview  
> Research notes (raw). Meta-concept: reusable whiteboard framework for enterprise RAG / agent platforms under scale stress.

---

## Fundamentals

Classic FAANG “URL shortener” muscle does not transfer cleanly. AI Engineer / FDE system design interviews typically probe **RAG / agent platforms**: corpus scale, mixed query types (keyword ID lookup, semantic FAQ, multi-hop, analytics), freshness, ACL, latency, cost, and evals.

### Clarify before you draw

| Number to pin | Why interviewers care | Weak default |
|---------------|----------------------|--------------|
| Docs N + chunks/doc | Index size, shard plan, re-embed cost | “Millions of vectors” handwave |
| QPS peak + p95 | Latency budget across stages | “We’ll cache” without hit assumptions |
| Freshness / delete SLA | Incremental index + tombstones | Nightly batch only |
| Wrong-answer cost | Abstain vs always-answer | Ignore refusal |
| Tenants / ACL model | Pre-filter placement | Post-filter after ANN |

### Offline vs online split

**Offline / async ingest:** parse → clean → chunk (± contextualize per Anthropic) → embed + sparse index → versioned upsert; tombstones for deletes; delta index + compaction at 10M scale; eval gate on index build.

**Online request path:** auth/tenant → query understanding (classify/rewrite/route) → retrieve (ACL pre-filter → hybrid → fuse → rerank) → context pack + cite → generate → guardrail/faithfulness → log traces + cost.

Chip Huyen’s GenAI platform essay is the progressive checklist: model API → guardrails → context (RAG/tools) → cache/route → logging/evals — add complexity when failure modes demand it ([Building a Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html)).

### Mixed query types force routing

| Query shape | Example | Prefer |
|-------------|---------|--------|
| Exact ID / error code | `TS-999`, invoice `INV-1042` | BM25 / metadata filter (Anthropic TS-style example) |
| Paraphrase FAQ | “How do contractors expense travel?” | Dense + hybrid |
| Multi-hop policy | “Policy for contractors remote work across EU entities” | Multi-retrieve / light agentic loop |
| Analytics | “Top 10 SKUs by margin” | Structured store / SQL tool — **not** vectors |

**10M documents** is the canonical stress question because prototype shortcuts break: full re-embed, single unsharded index, post-filter ACL, dense-only retrieval, no deletion SLA. Public mock pacing for large-N semantic search: [YouTube `MUs3JFkevak`](https://www.youtube.com/watch?v=MUs3JFkevak); architect-scale RAG Qs: [`BY5hk_tMgyA`](https://www.youtube.com/watch?v=BY5hk_tMgyA).

### Hybrid + contextualize + rerank (measured)

Anthropic public results on Contextual Retrieval: stacking **hybrid** (Contextual Embeddings + Contextual BM25) cut retrieval failures **49%**; adding a **rerank** step cut failures **67%** vs baseline ([Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)). Interview translation: say the metric, then budget rerank latency.

ByteByteGo public diagrams cover the RAG stack, Perplexity-style hybrid + model routing, and Agentic RAG as an **optional** control loop when one-shot retrieval fails ([RAG](https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data); [Perplexity](https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google); [Agentic RAG](https://blog.bytebytego.com/p/how-agentic-rag-works)).

### Latency budget sketch (p95 ≤ 2s example)

| Stage | Budget | Notes |
|-------|--------|-------|
| Auth + query rewrite | ~50–100ms | Cache rewrite for FAQ |
| Embed query | ~50–100ms | Or sparse-first for ID class |
| Hybrid retrieve | ~100–250ms | Sharded; ACL in query |
| Rerank top-N→k | ~150–300ms | N≈10–20 not 100 |
| Generate TTFT+decode | remainder | Shorter context wins $ and latency |
| Guardrail / cite check | ~50ms | Parallel where possible |

### Rubric interviewers silently use

From public RAG interview writeups (e.g. [technoscripts 8-layer](https://technoscripts.com/python-rag-system-design/)): pin requirements before drawing; ACL filter **before** rank; name cost + latency; gate deploys on evals; mention monitoring/guardrails unprompted.

---

## Alternatives & Tradeoffs

| Decision | Option A | Option B | Say aloud |
| --- | --- | --- | --- |
| Index | pgvector / one DB | Dedicated vector DB + search engine | Ops simplicity vs scale/perf isolation; threshold often debated ~tens of millions vectors |
| Retrieval | Dense-only | Hybrid + rerank | Anthropic: hybrid contextual −49% failures; +rerank −67% vs baseline |
| Context | Stuff long context | RAG | Anthropic: ≲200k tokens may skip RAG with caching; else retrieval |
| Query path | One-shot RAG | Agentic RAG loop | ByteByteGo: loops fix ambiguity/scattered evidence; cost/latency 3–10×; harder to test |
| Sharding | By doc count | By tenant/region/source/time | Shard on query + ACL patterns, not vanity counts |
| Freshness | Batch nightly | CDC / incremental upsert | “Time to searchable” is a first-class SLA at 10M |
| Deletes | Soft hide in app | Tombstone + index purge ≤ SLA | Interviewers ask: “user deletes a PDF — when is it gone from answers?” |
| Eval gate | Manual vibe | Golden set in CI | Strong hire signal per public rubrics |

---

## Necessity

Candidates who only draw “embed → vector DB → LLM” fail follow-ups on ACL, deletes, hybrid exact match, rerank budget, and evals. Frameworks exist to force those topics into the **first 10 minutes**. At 10M, skipping incremental indexing or delete SLAs is a production outage story waiting to happen — and FDE interviews treat that as judgment, not trivia.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Single vector collection; top-k=5; no ACL story; “we’ll fine-tune later” |
| **Strong** | Requirements table; hybrid+RRF; rerank budget; abstain; golden metrics; cost dominated by context tokens |
| **Senior** | Shard + compaction plan; CDC; tenant isolation; agentic branch only for multi-hop; progressive Huyen stack |

- **Huyen GenAI platform:** production retrieval = hybrid; ANN tradeoffs; caching; progressive complexity.  
- **Anthropic Contextual Retrieval:** Contextual Embeddings + Contextual BM25; rerank; measured recall failure reductions; long-context vs RAG decision.  
- **ByteByteGo:** RAG stack; Perplexity hybrid + routing; Agentic RAG tradeoffs.  
- **Production RAG talks:** observability, security, scale ([Isaac Chung SPS24](https://www.youtube.com/watch?v=K-KhenQ3Scw)).

---

## Concrete Scenario (URL)

**Prompt:** 10M PDFs/HTML, 50 QPS peak, p95 ≤ 2s, multi-tenant ACL, mixed queries, continuous updates, deletes searchable-gone ≤ 15 minutes.

**Strong outline (abridged):**

1. Pin wrong-answer cost → abstain policy.  
2. Offline: contextual chunking; dual index; versioned upsert; tombstones compacted &lt;15m.  
3. Online: route ID→BM25-heavy; FAQ→hybrid; analytics→SQL tool.  
4. ACL predicates in retrieve; never post-filter-only.  
5. Rerank top-15→5 inside ~250ms.  
6. Generate with citations; refuse if empty/low score.  
7. Eval: recall@k slices + faithfulness + delete-SLA probe; CI gate.  
8. Cost: context tokens dominate — rerank down, don’t stuff.

Anthropic measured stack: https://www.anthropic.com/news/contextual-retrieval  
Huyen platform: https://huyenchip.com/2024/07/25/genai-platform.html  
ByteByteGo RAG / Perplexity / Agentic: linked in Sources.  
Enterprise RAG HLD practice notes: https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  
Open-ended ML systems prompts: https://huyenchip.com/machine-learning-systems-design/toc.html  

---

## Open Questions

- At what corpus size do interviewers expect you to reject pure Postgres-pgvector?  
- Is GraphRAG expected in 2026 loops or still a “nice if asked” branch?  
- How much GPU/inference serving design bleeds into Applied AI Engineer vs platform SWE interviews?  
- When does multi-index (per tenant) beat shared index + ACL filter for 10M?

---

## Sources

- Chip Huyen GenAI platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Chip Huyen ML systems design TOC: https://huyenchip.com/machine-learning-systems-design/toc.html  
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval  
- ByteByteGo RAG: https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data  
- ByteByteGo Perplexity: https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google  
- ByteByteGo Agentic RAG: https://blog.bytebytego.com/p/how-agentic-rag-works  
- RAG interview 8-layer guide: https://technoscripts.com/python-rag-system-design/  
- Enterprise RAG HLD case: https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  
- Semantic search at scale mock (YouTube): https://www.youtube.com/watch?v=MUs3JFkevak  
- RAG 500M-docs interview Qs (YouTube): https://www.youtube.com/watch?v=BY5hk_tMgyA  
- Isaac Chung — Prototype to Production RAG (YouTube): https://www.youtube.com/watch?v=K-KhenQ3Scw  
- Chip Huyen MLSys principles (YouTube): https://www.youtube.com/watch?v=c_AUuTuPA5k  
