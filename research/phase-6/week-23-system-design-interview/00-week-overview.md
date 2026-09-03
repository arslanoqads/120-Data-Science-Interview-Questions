# 00 — Week overview: interview spine + STAR bank from own build

> Week 23 — System design interview  
> Research notes (raw). Phase 6 week after capstone polish (Week 22). Next: portfolio / resume language (Week 24). Do not rewrite resume bullets from this corpus — extract STAR evidence first.

This file is the **design document** for interview week: a reusable whiteboard spine, a timed-debug habit, an FDE case shape, aloud tradeoff templates, and **8–10 STAR case studies** mined from the curriculum’s own Weeks 6–22 builds. Concept files 01–05 are depth; this file is the stitched path plus the story bank.

---

## Fundamentals

Week 22 froze a demoable vertical slice. Week 23 asks: can you **repackage that work under interview constraints** — 45-minute whiteboards, broken-prompt live debug, customer-blocker scenarios, and behavioral drills that survive two follow-up depths?

Five coupled deliverables:

1. **Retrieval design framework** — 10M docs, mixed queries (file [01](01-retrieval-system-design-10m.md)).  
2. **Prompt-debug ladder** — time-boxed localization (file [02](02-prompt-debugging-under-time-pressure.md)).  
3. **FDE integration case** — blockers as the job (file [03](03-fde-integration-case-study.md)).  
4. **Aloud tradeoffs** — recall/precision, latency/quality, build/buy (file [04](04-narrating-tradeoffs-aloud.md)).  
5. **STAR packaging** — technically drillable stories (file [05](05-star-technical-case-studies.md)).

### Whiteboard spine (say in first 8 minutes)

Compose from Huyen + Anthropic + ByteByteGo + common RAG rubrics:

1. **Clarify numbers**: docs N, chunks/doc, QPS, p95, freshness SLA, wrong-answer cost, tenants.  
2. **Split offline vs online**.  
3. **Ingest**: parse → chunk (± contextualize) → embed + sparse → versioned upsert; tombstones; delta + compaction at 10M.  
4. **Query understanding**: classify / rewrite / route (doc RAG vs SQL vs web vs abstain).  
5. **Retrieve**: metadata/ACL **pre-filter** → hybrid dense+BM25 → fuse (RRF) → cross-encoder rerank → context pack + cite.  
6. **Generate**: grounded prompt; refuse on low confidence; optional faithfulness check.  
7. **Wrap**: semantic cache, tracing, golden-set eval gate, cost dashboards, guardrails.

**10M documents** breaks prototype shortcuts (full re-embed, unsharded index, post-filter ACL, dense-only, no deletion SLA). **Mixed queries** force routing: error codes → BM25; paraphrase FAQ → dense; multi-policy → agentic branch; margin analytics → SQL, not vectors ([Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval); [ByteByteGo RAG](https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data); [Huyen GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html)).

### Timed practice path

```
45m RAG whiteboard (drill card below)
        │
        ▼
20m prompt-debug on a planted failure (retrieval vs prompt vs tool)
        │
        ▼
20m FDE case: “no prod data for 2 weeks — Monday plan?”
        │
        ▼
STAR bank rehearsal (2–3 min each; 2 follow-ups)
        │
        ▼
Tradeoff one-liners with latency + $ budgets
```

### Drill card — 45-minute RAG design (10M docs)

> Design an enterprise assistant over 10M PDFs / HTML docs, 50 QPS peak, p95 ≤ 2s, multi-tenant ACL, mixed queries (IDs, semantic, multi-doc policy). Documents update continuously; deletes must stop being retrievable within 15 minutes.

Force: requirements → hybrid retrieve → ACL pre-filter → incremental index → rerank budget → abstain → eval metrics → cost → one agentic branch **only if justified**.

Public mock / prep videos to calibrate pacing: Chip Huyen [ML interviews](https://www.youtube.com/watch?v=pli1K75PSa8); semantic search at scale [Ep. 45](https://www.youtube.com/watch?v=MUs3JFkevak); RAG architect Qs [500M docs](https://www.youtube.com/watch?v=BY5hk_tMgyA).

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| Whiteboard + timed debug + STAR bank | New retrieval theory (Weeks 6–8) — **reuse** those decisions |
| FDE customer-blocker rehearsal | Capstone polish / new features (Week 22) |
| Aloud tradeoff templates | Resume / portfolio copy (Week 24) |
| Extract metrics from *your* evals | Judge calibration deep-dive (Week 17) |

---

## STAR case studies from own build (9)

These are **curriculum-shaped** templates. Replace placeholders with your real numbers, repos, and trace IDs. Each maps to a Phase 2–6 week so interviewers can drill systems you actually touched. Full packaging guidance: file [05](05-star-technical-case-studies.md).

### STAR 1 — Chunk boundaries beat fine-tuning (Week 6 → 22)

| Field | Content |
|-------|---------|
| **Situation** | Capstone KB answers truncated mid-policy; golden faithfulness ~58%. |
| **Task** | Raise grounded pass rate without fine-tuning or model swap. |
| **Action** | I open-coded 40 traces; axial-coded `chunk_boundary_split_section`; retuned chunk size/overlap + section-aware split; added contextual prefixes (Anthropic-style); promoted failing queries to golden set. |
| **Result** | Faithfulness 58%→81%; p95 +120ms (accepted); rejected fine-tune as higher ops cost. |
| **Follow-ups** | Chunk size chosen? How measured? What still fails? |
| **Track** | Applied AI (eval → data fix) |

### STAR 2 — Hybrid BM25 for exact error codes (Week 7)

| Field | Content |
|-------|---------|
| **Situation** | Dense-only miss on `TS-999`-style IDs; support analysts lost trust. |
| **Task** | Fix exact-ID recall without killing semantic FAQ quality. |
| **Action** | I added BM25 + dense with RRF; metadata boost on `error_code`; eval slice for ID queries separate from paraphrase FAQ. |
| **Result** | ID-query recall@5 41%→93%; FAQ NDCG flat within 2 pts. |
| **Follow-ups** | Fusion weights? Why not sparse-only? Rerank interaction? |
| **Track** | Applied AI (retrieval) — cite Anthropic hybrid failure reductions |

### STAR 3 — Rerank inside a 2s budget (Week 8 / 20)

| Field | Content |
|-------|---------|
| **Situation** | Cross-encoder on top-50 blew p95 past 2.8s at 50 QPS peak. |
| **Task** | Keep quality lift; hit p95 ≤ 2s. |
| **Action** | I budgeted stages (embed 80ms / retrieve 200 / rerank 250 / TTFT+decode rest); cut rerank candidates 50→12; smaller generator on cache hit; logged stage timings. |
| **Result** | p95 2.8s→1.7s; faithfulness −1.5 pts (accepted); $/1k −18% via shorter context. |
| **Follow-ups** | Why 12? Batching? GPU vs API rerank? |
| **Track** | Applied AI (latency/cost) |

### STAR 4 — Filter ACL before rank (Week 9 / 19)

| Field | Content |
|-------|---------|
| **Situation** | Post-filter ACL dropped top hits → empty context → hallucinations on other-tenant phrasing in prompt history. |
| **Task** | Eliminate cross-tenant retrieval leakage. |
| **Action** | I moved tenant/ACL predicates into the retrieval query (pre-filter); stripped other-tenant text from logs in demos; added red-team goldens. |
| **Result** | Leak golden suite 0/50 pass; empty-retrieve abstain rate up (correct). |
| **Follow-ups** | Shard by tenant? How encode ACLs in vectors? Defense in depth? |
| **Track** | FDE / enterprise (security severity override) |

### STAR 5 — Eval taxonomy → citation off-by-one (Week 10 / 16 / 22)

| Field | Content |
|-------|---------|
| **Situation** | Demo looked fluent; Hamel-style review found citations pointing to wrong chunk IDs. |
| **Task** | Make citations machine-checkable before next stakeholder demo. |
| **Action** | I built citation aligner assert (span must appear in retrieved chunk); binary pass/fail + critique; fixed mapper; CI gate on golden set. |
| **Result** | Fake-citation class 10/40 traces → 0/40; demo “control under failure” path added. |
| **Follow-ups** | Judge vs assert? How large golden? Who labels? |
| **Track** | Applied AI (evals) — [Hamel](https://hamel.dev/blog/posts/evals/); Lenny’s [`BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c) |

### STAR 6 — Tool schema + idempotent ticket create (Week 11 / 14 / 21)

| Field | Content |
|-------|---------|
| **Situation** | Agent retried `create_ticket` after timeout → duplicate Zendesk rows. |
| **Task** | Stop duplicate side effects under at-least-once delivery. |
| **Action** | I added JSON-schema validation; minted idempotency key `(tenant, run_id, step, object_id)` at plan time; on timeout, status lookup before retry (Stripe-shaped). |
| **Result** | Duplicate tickets 7/week → 0 in soak; unknown-outcome path documented. |
| **Follow-ups** | Key retention? Exactly-once claims? Compensating actions? |
| **Track** | FDE (integration / production) |

### STAR 7 — MCP adapter when customer API undocumented (Week 12 / 21)

| Field | Content |
|-------|---------|
| **Situation** | Customer CRM “API” was a brittle SOAP export; no OpenAPI; pilot blocked. |
| **Task** | Ship a thin production slice without waiting for platform rewrite. |
| **Action** | I wrote a bounded MCP/tool adapter over a curated view + contract tests; quarantined malformed rows; escalated owner for long-term API with written freeze of pilot KPI. |
| **Result** | Pilot live in 5 days; 3 tools only; playbook codified for next engagement. |
| **Follow-ups** | Why not wait? How test without prod? Residency? |
| **Track** | FDE — [Anthropic FDE MCP language](https://job-boards.greenhouse.io/anthropic/jobs/5391016008); [Palantir compose platform](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1) |

### STAR 8 — Semantic layer before text-to-SQL (Week 21)

| Field | Content |
|-------|---------|
| **Situation** | Naive text-to-SQL on raw ERD hallucinated joins; finance rejected PoC. |
| **Task** | Safe answers for invoice/status questions only. |
| **Action** | I froze a semantic layer (3 metrics + join graph); allowlisted views; `get_invoice(id)` tool for money paths; RAG over data dictionary before any SQL. |
| **Result** | Executed-SQL error rate 34%→6% on golden; zero write queries by construction. |
| **Follow-ups** | RLS? Statement timeout? Who owns metric defs? |
| **Track** | FDE (messy systems of record) |

### STAR 9 — Scope freeze over feature sprawl (Week 22)

| Field | Content |
|-------|---------|
| **Situation** | Capstone had chat + second agent + admin UI stubs; demo flaked weekly. |
| **Task** | Make one vertical slice interview-safe in one week. |
| **Action** | I wrote a demo contract (user job, corpus/tools, metrics, non-goals); killed second agent; triaged top-5 eval bugs; scripted success + abstain + tool-error. |
| **Result** | Clean-machine happy path; golden command in README; 5-min walkthrough stable across 10 rehearsals. |
| **Follow-ups** | What did you cut? How know it’s enough? Roadmap honesty? |
| **Track** | Both — [Huyen progressive stack](https://huyenchip.com/2024/07/25/genai-platform.html); Palantir focus |

### STAR 10 (optional stretch) — Semantic cache + routing (Week 20)

| Field | Content |
|-------|---------|
| **Situation** | Repeat FAQ burned embedding + generation $; p95 fine but margin bad. |
| **Task** | Cut $/1k without silent stale answers. |
| **Action** | I added embedding-similarity cache with tenant+ACL key; TTL tied to freshness SLA; routed easy FAQ to smaller model; logged cache hit rate. |
| **Result** | $/1k −32%; staleness incidents 0 with TTL &lt; delete SLA. |
| **Follow-ups** | Collision risk? Invalidation on delete? Threshold tuning? |
| **Track** | Applied AI (cost) |

---

## Alternatives & Tradeoffs

| Interview prep strategy | Gain | Risk |
|-------------------------|------|------|
| **Own-build STAR bank** | Drillable; authentic | Needs real metrics written down now |
| **Generic FAANG behavioral pack** | Volume | Fails AI/FDE follow-ups on retrieval/evals |
| **Whiteboard memorization only** | Fast diagrams | Silent on ACL/deletes/evals → reject |
| **Live timed mocks (YouTube + peer)** | Pacing + narration | Weak if no rubric (pin numbers, pre-filter ACL, cost) |
| **Model-swap as default debug** | Feels decisive | Hides root cause; junior signal |

---

## Necessity

Without a spine: 45 minutes spent drawing “vector DB → LLM.” Without STAR metrics: Week 22 work stays invisible. Without FDE blocker practice: “wait for perfect API” fails the round that *is* the job. Without aloud tradeoffs: diagrams read as memorized.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Dense-only RAG sketch; vibe prompt fixes; STAR with “we” and no numbers |
| **Strong** | Requirements pinned; hybrid + ACL pre-filter; debug ladder narrated; 8 STAR with metrics + rejected alternatives |
| **Senior / FDE-shaped** | Incremental index + delete SLA; latency/$ budgets aloud; customer unblock Monday plan; pattern codified back to product ([OpenAI FDE](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Anthropic FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)) |

---

## Concrete Scenario (URL)

1. **Measured retrieval stack.** Anthropic: hybrid contextual retrieval −49% failures; +rerank −67% vs baseline ([Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)).  
2. **Platform progressive complexity.** Huyen adds components when failure modes demand ([GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html)).  
3. **Agentic loop cost.** ByteByteGo: loops fix ambiguity; latency/cost jump; harder to test ([Agentic RAG](https://blog.bytebytego.com/p/how-agentic-rag-works)).  
4. **Field composition.** Palantir FDSE: configure platform for one customer under time pressure ([blog](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); deskside [YouTube `bPGnvfyMuxE`](https://www.youtube.com/watch?v=bPGnvfyMuxE)).  
5. **Mock pacing.** Semantic search 100M-doc structure ([YouTube `MUs3JFkevak`](https://www.youtube.com/watch?v=MUs3JFkevak)); Chip Huyen interview framing ([`pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)).

---

## Open Questions

- At what corpus size do interviewers expect rejection of pure Postgres-pgvector?  
- Is GraphRAG expected in 2026 loops or still “nice if asked”?  
- How much prompt-debug is a named round vs buried in project deep-dives?  
- How “production” must a personal project be for frontier-lab loops?  
- Optimal STAR length before interrupt (~2–3 minutes)?

---

## Sources

- Chip Huyen GenAI platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Chip Huyen LLM engineering: https://huyenchip.com/2023/04/11/llm-engineering.html  
- Chip Huyen ML systems design TOC: https://huyenchip.com/machine-learning-systems-design/toc.html  
- Chip Huyen ML interviews (YouTube): https://www.youtube.com/watch?v=pli1K75PSa8  
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval  
- ByteByteGo RAG: https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data  
- ByteByteGo Agentic RAG: https://blog.bytebytego.com/p/how-agentic-rag-works  
- Palantir FDSE day-in-life: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- OpenAI FDE SF: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- Anthropic FDE: https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Hamel evals: https://hamel.dev/blog/posts/evals/  
- Semantic search mock (YouTube): https://www.youtube.com/watch?v=MUs3JFkevak  
- RAG architect interview Qs (YouTube): https://www.youtube.com/watch?v=BY5hk_tMgyA  
