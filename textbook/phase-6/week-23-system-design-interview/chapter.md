# Chapter 23 — System design interview

> **Phase 6 — Capstone and Interview Readiness**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-6/week-23-system-design-interview/`  
> **Syllabus Build:** Syllabus treats Week 23 as **interview meta-work**: you already shipped Weeks 6–22 systems. This week you **rehearse packaging** under time pressure. (1) **Whiteboard a 10M-doc assistant.** Pin N, QPS, p95, freshness, ACL, wrong-answer cost. Split offline vs online. Force hybrid + ACL pre-filter + incremental deletes + rerank budget + abstain + eval gate ([Huyen GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval); [ByteByteGo RAG](https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data)). (2) **Run the prompt-debug ladder live.** Reproduce → localize layer → minimize → one hypothesis → golden lock. Never jump to “bigger model” first ([Huyen LLM engineering](https://huyenchip.com/2023/04/11/llm-engineering.html); [Hamel evals](https://hamel.dev/blog/posts/evals/)). (3) **Rehearse one FDE integration case.** Customer won’t give prod data / SSO blocked / undocumented API — what do you ship Monday? ([Palantir FDSE](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1); [OpenAI FDE](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Anthropic FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)). (4) **Bank 8–10 STAR stories** from *your* build. Quantify; reject an alternative aloud; survive follow-ups.

---

## Prerequisites Recap

Before this week you should already have from Week 22:

- **Scope freeze in writing:** one primary user job, one corpus + tool set, success metrics, and an explicit non-goals list; demo contract with happy path + failure demos; pinned model/prompt/index.  
- **Eval-driven fixes:** sample → open-code → axial taxonomy with counts; rank frequency × severity × leverage; top classes fixed and promoted into golden / CI evals.  
- **5-minute demo narrative:** stakes → requirements freeze → request + offline paths → live success with citations → intentional refusal/tool failure → metrics/tradeoffs → roadmap as non-goals.

You do **not** need an annotated 10M whiteboard, a timed prompt-debug transcript, a full FDE unblock case library, or an 8–10 card STAR bank yet as *finished* products — that is what this week ships. You **do** need Week 22’s frozen slice, taxonomy metrics, and demo narrative as the raw material; without them, whiteboard answers and STAR cards invent numbers you cannot defend.

---

## What this week builds

Week 22 froze a demoable vertical slice, triaged eval logs into fixes, and scripted a 5-minute walkthrough. Week 23 is the **interview packaging** week of Phase 6. Weeks 6–22 already shipped the systems; this week adds **no new product surface**. Capstone polish fails interview loops less from missing architecture knowledge and more from **unrehearsed packaging** under the clock.

This week answers five coupled questions that AI Engineer / FDE loops treat as the minimum bar for packaging a hardened slice:

1. **Can you whiteboard retrieval at ~10M docs?** (pin N, QPS, p95, freshness, ACL, wrong-answer cost — hybrid + ACL pre-filter + deletes + rerank + abstain + eval gate)  
2. **Can you debug a broken prompt/system live?** (reproduce → localize layer → minimize → one hypothesis → golden lock)  
3. **Can you unblock a customer Monday?** (no prod data / SSO / undocumented API — thin slice + escalation)  
4. **Can you narrate tradeoffs aloud?** (axes + pick + monitor; latency + $ budgets)  
5. **Can you bank drillable STAR stories?** (8–10 cards from *your* Weeks 6–22 builds; dual-track endings)

**Do not start Week 24 (portfolio / resume language — resume bullets, portfolio under 5 min, dual-track AI Engineer vs FDE) from this chapter** — this week drills **RAG-at-scale whiteboards**, **prompt debugging under the clock**, **FDE integration cases**, **aloud tradeoffs**, and a **STAR bank** extracted from your own builds. Capstone polish (Week 22) is assumed done; packaging for interview loops is the work. Do **not** reopen the Week 22 freeze or ship a second agent loop to “have more material.”

**Timed practice path**

```
45m RAG whiteboard (10M docs drill card)
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

**Default path (synthesis)**

1. **Pin requirements before boxes** ([technoscripts RAG layers](https://technoscripts.com/python-rag-system-design/); [Huyen ML interviews](https://www.youtube.com/watch?v=pli1K75PSa8)).  
2. **Hybrid + contextualize + rerank** beats dense-only vibes ([Anthropic](https://www.anthropic.com/news/contextual-retrieval)).  
3. **Agentic RAG is a branch**, not the default — cost/latency 3–10× ([ByteByteGo Agentic RAG](https://blog.bytebytego.com/p/how-agentic-rag-works)).  
4. **Debug the layer**, not the model ([Huyen](https://huyenchip.com/2023/04/11/llm-engineering.html); [Hamel](https://hamel.dev/blog/posts/evals/)).  
5. **Integration blockers are the FDE job** ([Palantir](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).  
6. **Aloud tradeoffs + STAR metrics** turn Week 22 polish into hire signal.

Interview artifact = **annotated 10M whiteboard** + **one timed prompt-debug transcript** + **one FDE unblock case** + **STAR index (title / metric / systems / 3 follow-ups)** + **tradeoff one-liners**.

| This week | Not this week |
|-----------|----------------|
| Whiteboard + timed debug + STAR bank | New retrieval theory (Weeks 6–8) — **reuse** those decisions |
| FDE customer-blocker rehearsal | Capstone polish / new features (Week 22) — freeze holds |
| Aloud tradeoff templates | Resume / portfolio copy (Week 24) |
| Extract metrics from *your* evals | Judge calibration deep-dive (Week 17) |

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) after Week 22 freeze — now packaged for whiteboard, timed debug, FDE case, and STAR rehearsal.

---

### Retrieval system design (~10M docs, mixed query types)

* **Fundamentals:**  
  Classic FAANG “URL shortener” muscle does not transfer cleanly. AI Engineer / FDE system design interviews typically probe **RAG / agent platforms**: corpus scale, mixed query types (keyword ID lookup, semantic FAQ, multi-hop, analytics), freshness, ACL, latency, cost, and evals.

  **Clarify before you draw** — pin these numbers in the first minutes:

  | Number to pin | Why interviewers care | Weak default |
  |---------------|----------------------|--------------|
  | Docs N + chunks/doc | Index size, shard plan, re-embed cost | “Millions of vectors” handwave |
  | QPS peak + p95 | Latency budget across stages | “We’ll cache” without hit assumptions |
  | Freshness / delete SLA | Incremental index + tombstones | Nightly batch only |
  | Wrong-answer cost | Abstain vs always-answer | Ignore refusal |
  | Tenants / ACL model | Pre-filter placement | Post-filter after ANN |

  **Whiteboard spine (say in first 8 minutes):**

  1. **Clarify numbers**: docs N, chunks/doc, QPS, p95, freshness SLA, wrong-answer cost, tenants.  
  2. **Split offline vs online**.  
  3. **Ingest**: parse → chunk (± contextualize) → embed + sparse → versioned upsert; tombstones; delta + compaction at 10M.  
  4. **Query understanding**: classify / rewrite / route (doc RAG vs SQL vs web vs abstain).  
  5. **Retrieve**: metadata/ACL **pre-filter** → hybrid dense+BM25 → fuse (RRF) → cross-encoder rerank → context pack + cite.  
  6. **Generate**: grounded prompt; refuse on low confidence; optional faithfulness check.  
  7. **Wrap**: semantic cache, tracing, golden-set eval gate, cost dashboards, guardrails.

  **Offline / async ingest:** parse → clean → chunk (± contextualize per Anthropic) → embed + sparse index → versioned upsert; tombstones for deletes; delta index + compaction at 10M scale; eval gate on index build.

  **Online request path:** auth/tenant → query understanding (classify/rewrite/route) → retrieve (ACL pre-filter → hybrid → fuse → rerank) → context pack + cite → generate → guardrail/faithfulness → log traces + cost.

  Chip Huyen’s GenAI platform essay is the progressive checklist: model API → guardrails → context (RAG/tools) → cache/route → logging/evals — add complexity when failure modes demand it.

  **Mixed query types force routing:**

  | Query shape | Example | Prefer |
  |-------------|---------|--------|
  | Exact ID / error code | `TS-999`, invoice `INV-1042` | BM25 / metadata filter (Anthropic TS-style example) |
  | Paraphrase FAQ | “How do contractors expense travel?” | Dense + hybrid |
  | Multi-hop policy | “Policy for contractors remote work across EU entities” | Multi-retrieve / light agentic loop |
  | Analytics | “Top 10 SKUs by margin” | Structured store / SQL tool — **not** vectors |

  **10M documents** is the canonical stress question because prototype shortcuts break: full re-embed, single unsharded index, post-filter ACL, dense-only retrieval, no deletion SLA.

  Anthropic public results on Contextual Retrieval: stacking **hybrid** (Contextual Embeddings + Contextual BM25) cut retrieval failures **49%**; adding a **rerank** step cut failures **67%** vs baseline. Interview translation: say the metric, then budget rerank latency.

  **Latency budget sketch (p95 ≤ 2s example):**

  | Stage | Budget | Notes |
  |-------|--------|-------|
  | Auth + query rewrite | ~50–100ms | Cache rewrite for FAQ |
  | Embed query | ~50–100ms | Or sparse-first for ID class |
  | Hybrid retrieve | ~100–250ms | Sharded; ACL in query |
  | Rerank top-N→k | ~150–300ms | N≈10–20 not 100 |
  | Generate TTFT+decode | remainder | Shorter context wins $ and latency |
  | Guardrail / cite check | ~50ms | Parallel where possible |

  Silent rubric from public RAG interview writeups: pin requirements before drawing; ACL filter **before** rank; name cost + latency; gate deploys on evals; mention monitoring/guardrails unprompted.

* **The Alternatives:**  

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

  The syllabus selects **hybrid + ACL pre-filter + incremental deletes + rerank budget + abstain + eval gate** as the forced whiteboard spine. Agentic RAG is a **branch** for multi-hop only — not the default path. ByteByteGo public diagrams cover the RAG stack, Perplexity-style hybrid + model routing, and Agentic RAG as an optional control loop when one-shot retrieval fails.

  `[NEEDS MORE RESEARCH]`: at what corpus size interviewers expect rejection of pure Postgres-pgvector beyond the research’s “debated ~tens of millions vectors” framing; whether GraphRAG is expected in 2026 loops or still “nice if asked.”

* **Failure Modes:**  
  - Drawing only “embed → vector DB → LLM” and failing follow-ups on ACL, deletes, hybrid exact match, rerank budget, and evals.  
  - Post-filter ACL after ANN → empty context or cross-tenant leakage.  
  - Dense-only miss on exact IDs / error codes (`TS-999`-style).  
  - Full re-embed or nightly-only freshness at 10M — no delete SLA.  
  - Rerank top-50 blowing p95 past the stated budget.  
  - Always-answer with no abstain when wrong-answer cost is high.  
  - Agentic loops as default → 3–10× latency/cost and harder tests.  
  - Cost handwave that ignores context tokens as the dominant line item.

* **Average vs. Strong Engineer:**  
  **Average / Common:** Single vector collection; top-k=5; no ACL story; “we’ll fine-tune later”; dense-only sketch.  
  **Strong:** Requirements table; hybrid+RRF; rerank budget; abstain; golden metrics; cost dominated by context tokens.  
  **Senior:** Shard + compaction plan; CDC; tenant isolation; agentic branch only for multi-hop; progressive Huyen stack. Public mock pacing for large-N semantic search: YouTube `MUs3JFkevak`; architect-scale RAG Qs: `BY5hk_tMgyA`; production RAG observability/security/scale: Isaac Chung `K-KhenQ3Scw`.

* **Worked Example:**  
  **Drill card — 45-minute RAG design (10M docs):** Design an enterprise assistant over 10M PDFs / HTML docs, 50 QPS peak, p95 ≤ 2s, multi-tenant ACL, mixed queries (IDs, semantic, multi-doc policy). Documents update continuously; deletes must stop being retrievable within 15 minutes.

  Strong outline for Deployment Copilot at that scale:

  1. Pin wrong-answer cost → abstain policy.  
  2. Offline: contextual chunking; dual index; versioned upsert; tombstones compacted &lt;15m.  
  3. Online: route ID→BM25-heavy; FAQ→hybrid; analytics→SQL tool.  
  4. ACL predicates in retrieve; never post-filter-only.  
  5. Rerank top-15→5 inside ~250ms.  
  6. Generate with citations; refuse if empty/low score.  
  7. Eval: recall@k slices + faithfulness + delete-SLA probe; CI gate.  
  8. Cost: context tokens dominate — rerank down, don’t stuff.

* **Apply It:**  
  1. Run the 45-minute drill card with a timer; force requirements before boxes.  
  2. Write a requirements table: N, QPS, p95, freshness/delete SLA, ACL model, wrong-answer cost.  
  3. Draw offline vs online; name hybrid + RRF + ACL pre-filter + tombstones.  
  4. Allocate a stage latency budget that sums to your p95.  
  5. Justify one agentic branch only if multi-hop is in scope — else one-shot hybrid.  
  6. Name eval metrics (recall@k slices, faithfulness, delete-SLA probe) and a CI gate.  
  7. Annotate the whiteboard once; keep it as the interview artifact.

---

### Prompt debugging under time pressure

* **Fundamentals:**  
  Two interview settings share the same skill:

  1. **Prompt/system debug round:** broken RAG/agent; find why outputs fail.  
  2. **AI-assisted coding round:** you must prompt a model to ship code while narrating.

  Under time pressure, strong candidates run a **diagnostic ladder**, not vibes:

  1. **Reproduce** with a fixed failing input; write expected vs actual.  
  2. **Localize layer**: retrieval miss vs ranking vs grounding vs tool schema vs prompt contradiction vs evaluator bug (reuse Week 9 RAG failure taxonomy).  
  3. **Minimize**: strip tools/context until behavior flips.  
  4. **Hypothesize aloud** one change; apply; re-run same case.  
  5. **Lock regression**: add unit/golden case before moving on.

  Chip Huyen’s production LLM theme: prefer **control flow / evals** over prompt magic. Hamel: ground yourself in **actual errors** before writing more tests or swapping models.

  **Layer checklist (say aloud):**

  | Layer | Symptom | First probe |
  |-------|---------|-------------|
  | Retrieval miss | Empty / wrong chunks | Inspect retrieved set vs gold doc IDs |
  | Ranking / lost-in-middle | Right doc low; model ignores mid context | Rerank; reorder; shrink k |
  | Grounding | Fluent lie; bad citations | Faithfulness assert; force quotes |
  | Tool schema | Wrong args / retries | Validate JSON schema; check descriptions |
  | Prompt contradiction | Refuse + answer; conflicting rules | Diff system prompt sections |
  | Evaluator bug | “Fail” on good output | Check judge rubric / reference |

  **AI-paired coding tactics** (public Meta-style / AI-coding round writeups converge on):

  - Small verified prompts &gt; mega-prompt.  
  - Specify stack, files, constraints, tests.  
  - Never paste unread diffs — verify every AI edit.  
  - Reset context when drift accumulates.  
  - Timebox: Understand → Strategy → Code → Verify.

  **20-minute planted-failure drill:**

  | Minute | Action |
  |--------|--------|
  | 0–3 | Reproduce; write expected vs actual on the board |
  | 3–8 | Localize layer with evidence (retrieval dump / prompt excerpt / tool trace) |
  | 8–14 | One hypothesis; minimal change; re-run |
  | 14–18 | Add golden / unit; narrate what you will *not* chase |
  | 18–20 | State residual risk + next offline experiment |

* **The Alternatives:**  

  | Move | When good | When bad |
  | --- | --- | --- |
  | Jump to bigger model | After confirming retrieval/context OK | Hides root cause; burns time/cost |
  | Add few-shot | Format/style failures | Masks missing evidence |
  | Raise top-k | Suspected recall miss | Adds noise; may worsen extraction |
  | Rewrite prompt | Instruction conflict / refusal policy | Won’t fix absent chunks |
  | One-shot “fix everything” AI prompt | Never in interview | Unreviewable; signals loss of control |
  | Swap vector DB | Proven infra limit | Premature in 20-minute debug |
  | Silence while thrashing | Never | Interviewers score process visibility |

  The syllabus selects **localize layer before model swap**; minimize; golden lock. Never jump to “bigger model” first.

* **Failure Modes:**  
  - Silent thrashing or blind model swaps read as junior.  
  - Rewriting the system prompt twice and changing temperature without evidence.  
  - “Fixed” demos that regress before the next round because no golden lock.  
  - Treating a retrieval miss as a prompt problem (or the reverse).  
  - One-shot mega-prompts in AI-paired coding that nobody can review.  
  - Pasting unread AI diffs.  
  - Ignoring company **candidate AI-tool policy** in-loop.

* **Average vs. Strong Engineer:**  
  **Average / Common:** Rewrite system prompt twice; change temperature; claim fixed.  
  **Strong:** Layer hypothesis with evidence; one change; regression case.  
  **Senior / FDE:** Separates data bugs from prompt bugs; names severity; schedules offline soak. Capstone/product: Hamel-style error analysis on a handful of traces beats prompt roulette. Debugging interviews generally: narrate priorities; state what you will *not* investigate. Anthropic FDE postings list eval frameworks as production LLM experience; Palantir FDSE narratives emphasize debugging customer systems under ambiguity.

  `[NEEDS MORE RESEARCH]`: whether frontier-lab loops standardize “prompt debug” as a named round vs burying it in project deep-dives; how much LLM-as-judge debugging is expected live vs offline; whether using AI tools in-interview helps or hurts Anthropic values perception beyond “check each company’s candidate AI policy.”

* **Worked Example:**  
  **Planted bug (retrieval):** Deployment Copilot invents a refund policy. Candidate dumps retrieval: top chunks are shipping FAQs; refund PDF never ingested after a path filter bug. Fix = ingest path + golden query — **not** “be more careful” in the prompt.

  **Planted bug (tool):** Agent doubles charges. Trace shows timeout retry without idempotency key. Fix = key + status lookup (Week 21 pattern), not a longer prompt.

  Narrate the ladder on the board: expected vs actual → retrieval dump evidence → one change → golden lock → residual risk.

* **Apply It:**  
  1. Plant one retrieval failure and one tool/idempotency failure in a local Deployment Copilot fork.  
  2. Run the 20-minute drill with a peer or timer; speak every step.  
  3. Write expected vs actual before touching code or prompts.  
  4. Dump retrieved chunks / tool traces as evidence before hypothesizing.  
  5. Apply exactly one change; re-run the same case.  
  6. Add a golden / unit lock; name what you will *not* chase.  
  7. Save a timed transcript as the interview artifact.  
  8. Before any live AI-assisted round, read that company’s candidate AI-tool policy.

---

### FDE integration case study

* **Fundamentals:**  
  Forward Deployed / Applied AI Engineer work, per primary employers’ own words:

  - **Palantir FDSE:** embed with customer; configure platforms; data integration; access controls; production outages; feed field learnings back to product. Not slide consulting.  
  - **OpenAI FDE:** discovery, technical scoping, system design, build, production rollout with strategic customers; hybrid of delivery + platform feedback; significant travel.  
  - **Anthropic FDE (Applied AI):** build production apps on Claude inside customer systems; deliver MCP servers, sub-agents, skills; white-glove deploy; **evaluation frameworks**; codify repeatable patterns back to Product/Engineering; thrive in ambiguity.

  **Integration blockers** (SSO, VPC, messy schemas, undocumented APIs, data residency, change control, “who owns the gold dataset?”) are not interruptions—they **are** the engagement. Interview case studies should center unblocking a path to a **thin production slice**, not inventing a novel architecture in a vacuum.

  **Case skeleton (use every time):**

  | Beat | What you say |
  |------|----------------|
  | **Clarify stakes** | Who user, cost of wrong answer, deadline, compliance |
  | **Inventory constraints** | Data access, identity, network, owners, SLAs |
  | **Thin slice** | One job / one corpus or tool / one KPI |
  | **Unblock plan** | Adapter, synthetic/redacted data, contract test, escalation |
  | **Risk + monitor** | What fails open/closed; how you know Monday |
  | **Codify** | What becomes playbook / MCP / product feedback |

  **Classic blockers → FDE-shaped moves:**

  | Blocker | Monday move | Anti-pattern |
  |---------|-------------|--------------|
  | No prod data for 2 weeks | Redacted sample + synthetic goldens; contract on schema | Idle wait |
  | SSO / IdP delay | Dev IdP + documented prod cutover checklist | Shadow deploy without auth |
  | Undocumented API | Adapter over export/view + contract tests; escalate owner | Boil-the-ocean rewrite |
  | Dirty SQL / ERD | Semantic layer + allowlisted tools (Week 21) | Open text-to-SQL on raw warehouse |
  | Security review | Threat model + least privilege path + logging | “We’ll harden later” |
  | Model quality complaints | Error analysis on *their* traces | Blind model swap |
  | Scope creep | Written freeze + measurable pilot KPI | Infinite PoC |
  | Data residency | Region-pinned deploy; no exfil embeddings if required | “API in us-east is fine” |

  Palantir narratives emphasize rapid cycle with users and engineering rigor in the field — pipelines, access controls, workflow UX, production outage investigation. Visual metaphor for composed workflows: Foundry deskside demos (YouTube `bPGnvfyMuxE`).

  Secondary synthesis of multi-round FDE loops exists (anecdotal Medium six-round sketch; **not** official employer gospel) — use only as practice structure.

* **The Alternatives:**  

  | Response to blocker | FDE-shaped | Anti-pattern |
  | --- | --- | --- |
  | Missing API | Adapter + contract test; escalate owner | Wait for perfect platform |
  | Dirty SQL | Bounded views/ETL with idempotent jobs | Boil-the-ocean warehouse rewrite |
  | Security review | Threat model + least privilege path | Shadow IT deploy |
  | Model quality complaints | Error analysis on *their* traces | “Try GPT-whatever” |
  | Scope creep | Written freeze + measurable pilot KPI | Infinite PoC |
  | Push back hard | When safety / residency / ACL at risk | Performative disagreement on taste |
  | Absorb chaos | Short-term to ship slice | Permanent heroics without codifying |

  The syllabus selects **thin production slice + Monday unblock plan + codify back to playbook/MCP**. Greenfield architecture diagrams that ignore identity/network fail the round that *is* the job.

  `[NEEDS MORE RESEARCH]`: how much “push back on customer” vs “absorb chaos” labs want in 2026; whether MCP servers are now a default artifact expectation in Anthropic-style loops; how to discuss classified/gov constraints without leaking or fabricating; honest travel answers from public postings (research notes 25–50% ranges as an open calibration question).

* **Failure Modes:**  
  - Ideal architecture diagram; ignore identity/network/data access.  
  - “Wait for perfect API / prod data” with no Monday plan.  
  - Shadow deploy without auth while SSO is queued.  
  - Open text-to-SQL on a dirty warehouse.  
  - Blind model swap when the customer complains about quality.  
  - Infinite PoC with no written KPI freeze.  
  - Permanent heroics that never become a playbook or product feedback.  
  - Treating secondary Medium “six-round” sketches as official employer process.

* **Average vs. Strong Engineer:**  
  **Average / Common:** Ideal architecture diagram; ignore identity/network.  
  **Strong:** Constraint inventory; thin slice; written KPI; escalation path.  
  **Senior FDE:** Codifies adapter → reusable MCP/playbook; feeds product; handles outage. Reported FDE loops (secondary; cautious) often include a **customer scenario** round testing composure, clarifying questions, and prioritization. Anthropic manager/Head of FDE postings stress playbooks, MCP/agent packages, measurable time-to-value. Frontier postings explicitly reward production deployment in **customer environments**, MCP/agent packages, and eval frameworks.

* **Worked Example:**  
  **Interview prompt:** Healthcare customer wants a policy assistant. Prod PHI corpus blocked 3 weeks. Okta SSO in security queue. They have a CSV export of de-identified FAQs and a legacy SOAP “getClaimStatus” used by one internal app.

  **Strong Monday plan for a Deployment Copilot–shaped engagement:**

  1. Freeze pilot: FAQ assistant only; no PHI; citation required; abstain on miss.  
  2. Ingest CSV → hybrid index; golden set from 30 labeled FAQs.  
  3. SOAP adapter behind one read-only tool with timeout + circuit breaker; no writes.  
  4. Dev auth stub; SSO cutover checklist owned with security.  
  5. Eval harness + weekly taxonomy review with champion user.  
  6. Write engagement note: what becomes MCP server template for next hospital.

* **Apply It:**  
  1. Pick one real Week 12/21 blocker from your build (undocumented API, dirty SQL, or missing data).  
  2. Rehearse the case skeleton aloud in ≤20 minutes.  
  3. Write a Monday plan with thin slice, KPI, and escalation owner.  
  4. Name what fails open vs closed and how you monitor.  
  5. End with one sentence on what becomes playbook / MCP / product feedback.  
  6. Practice the healthcare CSV+SOAP scenario until the beats are automatic.  
  7. Keep secondary “six-round” sketches as pacing practice only — cite primary Palantir / OpenAI / Anthropic language for employer framing.

---

### Narrating tradeoffs aloud

* **Fundamentals:**  
  Interview signal is rarely the choice itself; it is **naming the axes, picking for stated constraints, and saying what you monitor**. Silent diagrams without tradeoffs read as memorized. Aloud tradeoffs read as design ownership—and match how FDE conversations with customer architects actually go.

  **Core AI axes (memorize the monitor column):**

  | Axis | If you optimize… | You often pay… | Monitor |
  | --- | --- | --- | --- |
  | **Recall vs precision** (retrieval) | Higher recall@k / more chunks | Noise, lost-in-middle, cost, grounding errors | recall@k, precision@k, faithfulness |
  | **Latency vs quality** | Rerank + bigger model + agent loops | p95, $ | stage timings, abandonment |
  | **Build vs buy** | Custom index/agents/evals | Ops burden | time-to-value, vendor lock, margins |
  | **Freshness vs stability** | Aggressive re-index | Flickering answers, cost | time-to-searchable, churn |
  | **Autonomy vs control** | More tools/agent steps | Irreproducibility, safety surface | trajectory evals, human gates |
  | **Long context vs RAG** | Stuff / cache large KB | $ and attention limits | Anthropic guidance on when RAG still wins |

  ByteByteGo on Agentic RAG: loops are not free—latency, cost, debuggability, evaluator paradox. Anthropic on rerank: better retrieval vs added latency/cost—tune candidate counts. Huyen: start simple; add components when failure modes demand.

  **One-breath templates (fill constraints live):**

  1. **Hybrid + rerank:** “I’d take hybrid+rerank because exact IDs matter; I’ll spend ~150–300ms of a 1.5–2s budget on rerank and cut model size / context to compensate.”  
  2. **Build vs buy:** “For FAQ traffic I’d buy managed search + API model; for data-plane actions inside the VPC I’d build the tool/MCP layer ourselves.”  
  3. **Precision-first pilot:** “Pilot metric is precision-oriented with abstain; after trust, we raise recall targets.”  
  4. **Agentic branch:** “One-shot RAG for FAQ; agentic loop only for multi-hop policy — accept 3–10× latency on that slice.”  
  5. **Long context:** “If the working set fits ~200k with caching and changes slowly, skip RAG; past that, retrieval is the product.”  
  6. **Eval harness:** “Buy Langfuse/Phoenix for traces early; own golden-set assertions and taxonomy — judges only for subjective residuals.”

  **Budget tables beat vibes.** Strong RAG interview answers allocate a **latency budget** across embed/retrieve/rerank/TTFT and a **cost budget** dominated by context tokens. Weak answers only say “we’ll use Pinecone and GPT-4.” Public rubrics explicitly score naming cost + latency. Perplexity-style public architecture posts (ByteByteGo) emphasize hybrid retrieval + **model routing** as an explicit quality/cost control — good interview language for “not every query needs the biggest model.”

* **The Alternatives:**  

  | Narration style | Strength | Weakness |
  | --- | --- | --- |
  | **Axes + pick + monitor** | Hire signal; FDE-shaped | Needs constraints pinned first |
  | **Vendor name-drop only** | Fast | No judgment shown |
  | **Endless option lists** | Looks broad | Never commits; burns clock |
  | **Fake precision numbers** | Sounds senior until drilled | Credibility collapse on follow-up |
  | **Approximate but labeled** (“order-of”) | Honest; usually enough | Say assumptions aloud |

  The syllabus selects **axes + pick + monitor** with approximate, labeled assumptions. Practice templates until automatic; rotate recall/precision vs latency/quality each mock.

* **Failure Modes:**  
  - Silent diagrams without tradeoffs → assumed memorized blog.  
  - Vendor name-drops with no judgment.  
  - Endless option lists that never commit.  
  - Fake precision numbers that collapse on follow-up.  
  - Empty numbers → tradeoff talk sounds theatrical.  
  - Cannot defend Week 22 scope cuts (“why no second agent?”).  
  - Single vanity metric with “we’ll optimize later.”

* **Average vs. Strong Engineer:**  
  **Average / Common:** “We’ll optimize later”; single metric vanity; vendor name-drop.  
  **Strong:** Stage latency table; $/1k; abstain policy; rejected alternative.  
  **Senior:** Ties tradeoff to wrong-answer cost and tenant risk; schedules revisit when metrics flip. Mock videos that model tradeoff talk under scale: semantic search Ep. 45 (`MUs3JFkevak`); Chip Huyen systems design principles (`c_AUuTuPA5k`).

* **Worked Example:**  
  **Interviewer:** “Why not agentic RAG for everything?”

  **Answer shape:** “Default one-shot hybrid because 80% of traffic is FAQ/ID. Agentic loop for multi-doc policy only — ByteByteGo notes loops multiply latency/cost and hurt debuggability. I’ll route on a classifier, cap iterations, and eval the agent slice separately.”

  **Interviewer:** “Why rerank?”

  **Answer shape:** “Anthropic measured large failure reductions stacking hybrid contextual retrieval with rerank. I’ll limit candidates so rerank fits ~200ms of a 2s p95 and watch faithfulness vs p95 on a dashboard.”

  For Deployment Copilot after Week 22: defend cutting the second agent with the autonomy-vs-control axis; defend hybrid with the ID-query recall story; defend rerank-k=12 with the latency budget from STAR 3.

* **Apply It:**  
  1. Memorize the six axes table including the monitor column.  
  2. Fill each of the six one-breath templates with Deployment Copilot constraints.  
  3. Write a stage latency budget and a $/1k cost line for your frozen slice.  
  4. Rehearse “why not agentic for everything?” and “why rerank?” until automatic.  
  5. Label every approximate number (“order-of,” “assumption”) aloud.  
  6. Practice rejecting one alternative per whiteboard (dense-only, post-filter ACL, always-answer).  
  7. Keep a one-pager of tradeoff one-liners as an interview artifact.

  `[NEEDS MORE RESEARCH]`: whether candidates should lead with cost numbers even when approximate as a universal default; when “abstain” is the correct precision move vs a product failure in a given employer’s product language; how explicit vendor-lock arguments should be in lab interviews beyond the build-vs-buy template above.

---

### STAR technical case studies

* **Fundamentals:**  
  STAR = **Situation, Task, Action, Result** (+ **Learning** for senior). For AI Engineer / FDE, stories must be **technically drillable**: metrics, alternatives rejected, your personal actions, failure modes.

  Amazon-oriented public coaching (useful beyond Amazon) stresses:

  - Action ≈ majority of airtime; say **“I”** not “we.”  
  - Quantify: latency, error rate, cost, time-to-value, eval pass rate.  
  - Survive 2–3 follow-up depths (logs, queries, tradeoffs).  
  - Keep a bank of ~8–10 stories mapped to themes: incident, ambiguity, stakeholder conflict, tech debt, customer unblock, quality flywheel.

  **Capstone → STAR extraction recipe:**

  1. Pick one **eval-driven fix** from Week 22 (or earlier week).  
  2. Write STAR with **before/after metric**.  
  3. Name the alternative you did **not** take (e.g., “didn’t fine-tune; fixed chunk boundaries”).  
  4. List **3 follow-up bullets** (how measured, what still fails, ops cost).  
  5. Dual-end: one Applied AI punchline (harness/latency/architecture) + one FDE punchline (discovery/constraint/rollout/codify).

  **Own-build bank (index)** — curriculum-shaped templates; replace placeholders with your real numbers, repos, and trace IDs:

  | # | Title | Theme | Primary metric shape |
  |---|-------|-------|----------------------|
  | 1 | Chunk boundaries beat fine-tuning | Quality flywheel | Faithfulness % |
  | 2 | Hybrid BM25 for exact error codes | Retrieval | recall@k on ID slice |
  | 3 | Rerank inside a 2s budget | Latency/cost | p95, $/1k |
  | 4 | Filter ACL before rank | Security / tenancy | Leak suite pass |
  | 5 | Citation off-by-one from taxonomy | Evals | Fake-citation count |
  | 6 | Idempotent ticket create | Side effects | Duplicate rate |
  | 7 | MCP adapter on undocumented API | Customer unblock | Time-to-pilot |
  | 8 | Semantic layer before text-to-SQL | Messy integration | SQL error rate |
  | 9 | Scope freeze over feature sprawl | Ambiguity / focus | Demo stability |
  | 10 | Semantic cache + routing (optional) | Cost | $/1k, hit rate |

  **One-page story index fields** per card: Title; Metric (before → after); Systems touched; Failure mode; Alternative rejected; 3 follow-up bullets; Applied ending / FDE ending.

  **Timing:** Aim **2–3 minutes** before pause for questions. If uninterrupted past 4 minutes, you are over-narrating Situation. Cut setup; expand Action + Result.

  Chip Huyen interview materials emphasize systems thinking and portfolio signal over trivia. Hamel-style error analysis is itself a story engine: taxonomy count → fix → regression. Week 24 resume language depends on this bank — extract evidence **here**, polish wording later.

* **The Alternatives:**  

  | Story type | Good for | Risk |
  | --- | --- | --- |
  | Outage / rollback | Ownership, incident muscle | Don’t blame teammates |
  | Eval taxonomy → fix | Applied AI Engineer signal | Need real numbers |
  | Customer integration unblock | FDE signal | Don’t violate NDAs; anonymize |
  | Build vs buy decision | Judgment | Avoid fanboy vendor tales |
  | Failed experiment | Learning / humility | Must show updated process |
  | Pure interpersonal conflict | Classic LP rounds | Weak in AI labs if no technical consequence |

  | Packaging choice | Pros | Cons |
  |------------------|------|------|
  | Own-build only | Drillable | Thin if metrics never recorded |
  | Invented metrics | Smooth | Ethical + credibility risk — don’t |
  | Anonymized customer | FDE-safe | Still need technical depth |
  | Dual-track endings | Apply broadly | Rehearse both or stumble |

  | Interview prep strategy | Gain | Risk |
  |-------------------------|------|------|
  | **Own-build STAR bank** | Drillable; authentic | Needs real metrics written down now |
  | **Generic FAANG behavioral pack** | Volume | Fails AI/FDE follow-ups on retrieval/evals |
  | **Whiteboard memorization only** | Fast diagrams | Silent on ACL/deletes/evals → reject |
  | **Live timed mocks (YouTube + peer)** | Pacing + narration | Weak if no rubric (pin numbers, pre-filter ACL, cost) |
  | **Model-swap as default debug** | Feels decisive | Hides root cause; junior signal |

  The syllabus selects **own-build STAR bank** with dual-track endings. Anthropic values rounds (public candidate reports) may punish pure STAR “team conflict” theater if it ignores model failure modes / safety—**pair technical consequence** with interpersonal stories.

* **Failure Modes:**  
  - Strong builds stay invisible without STAR packaging.  
  - Empty STAR (no metrics/tradeoffs) backfires under follow-up.  
  - “We built a chatbot with LangChain” with no numbers.  
  - Invented metrics — ethical and credibility risk.  
  - Over-narrating Situation past 4 minutes.  
  - “We” language that hides personal action.  
  - Pure interpersonal conflict with no technical consequence in AI lab loops.  
  - Dual-track endings unrehearsed → stumble when the interviewer is FDE-shaped vs Applied AI.

* **Average vs. Strong Engineer:**  
  **Average / Common:** “We built a chatbot with LangChain”; no numbers; generic FAANG pack.  
  **Strong:** 8–10 cards; I-language; metric; rejected alternative; follow-ups.  
  **Senior / FDE:** Dual endings; safety/ACL story; codify-back-to-product story; incident with rollback. Map stories to employer language from Palantir FDSE, Anthropic FDE, and OpenAI FDE primary postings.

  `[NEEDS MORE RESEARCH]`: how “production” a personal project must be to count in frontier-lab loops; whether safety/values stories should be a separate bank from technical STAR; optimal story count before metric staleness (research asks; does not prescribe a hard max beyond ~8–10).

* **Worked Example:**  
  Curriculum-shaped bank (replace with your real numbers). Nine primary + one optional:

  **STAR 1 — Chunk boundaries beat fine-tuning (Week 6 → 22):** Capstone KB answers truncated mid-policy; golden faithfulness ~58%. Task: raise grounded pass rate without fine-tuning. Action: open-code 40 traces; axial-code `chunk_boundary_split_section`; retune chunk size/overlap + section-aware split; contextual prefixes; promote failing queries to golden. Result: faithfulness 58%→81%; p95 +120ms (accepted); rejected fine-tune. Follow-ups: chunk size? how measured? what still fails? Track: Applied AI.

  **STAR 2 — Hybrid BM25 for exact error codes (Week 7):** Dense-only miss on `TS-999`-style IDs. Action: BM25 + dense with RRF; metadata boost on `error_code`; separate ID eval slice. Result: ID-query recall@5 41%→93%; FAQ NDCG flat within 2 pts. Track: Applied AI — cite Anthropic hybrid failure reductions.

  **STAR 3 — Rerank inside a 2s budget (Week 8 / 20):** Cross-encoder on top-50 blew p95 past 2.8s. Action: budget stages; cut rerank candidates 50→12; smaller generator on cache hit. Result: p95 2.8s→1.7s; faithfulness −1.5 pts; $/1k −18%. Track: Applied AI (latency/cost).

  **STAR 4 — Filter ACL before rank (Week 9 / 19):** Post-filter ACL → empty context → hallucinations. Action: move tenant/ACL into retrieval query; red-team goldens. Result: leak suite 0/50; empty-retrieve abstain rate up (correct). Track: FDE / enterprise.

  **STAR 5 — Eval taxonomy → citation off-by-one (Week 10 / 16 / 22):** Fluent demo; citations pointing to wrong chunk IDs. Action: citation aligner assert; CI gate. Result: fake-citation class 10/40 → 0/40. Track: Applied AI (evals).

  **STAR 6 — Tool schema + idempotent ticket create (Week 11 / 14 / 21):** Agent retried `create_ticket` after timeout → duplicates. Action: JSON-schema validation; idempotency key `(tenant, run_id, step, object_id)`; status lookup before retry. Result: duplicates 7/week → 0 in soak. Track: FDE.

  **STAR 7 — MCP adapter when customer API undocumented (Week 12 / 21):** Brittle SOAP export; no OpenAPI. Action: bounded MCP/tool adapter over curated view + contract tests; quarantine malformed rows; written pilot KPI freeze. Result: pilot live in 5 days; 3 tools only. Track: FDE.

  **STAR 8 — Semantic layer before text-to-SQL (Week 21):** Naive text-to-SQL hallucinated joins. Action: freeze semantic layer (3 metrics + join graph); allowlisted views; `get_invoice(id)` for money; RAG over data dictionary first. Result: executed-SQL error rate 34%→6%; zero writes by construction. Track: FDE.

  **STAR 9 — Scope freeze over feature sprawl (Week 22):** Chat + second agent + admin UI stubs; demo flaked. Action: demo contract; kill second agent; triage top-5 eval bugs; script success + abstain + tool-error. Result: clean-machine happy path; 5-min walkthrough stable across 10 rehearsals. Track: Both.

  **STAR 10 (optional) — Semantic cache + routing (Week 20):** Repeat FAQ burned $. Action: embedding-similarity cache with tenant+ACL key; TTL tied to freshness SLA; route easy FAQ to smaller model. Result: $/1k −32%; staleness incidents 0 with TTL &lt; delete SLA. Track: Applied AI (cost).

  **Before packaging:** Capstone README says “improved retrieval.”  
  **After STAR 2:** “Dense-only miss on error codes; I added BM25+RRF and an ID eval slice; recall@5 41%→93%; rejected sparse-only because FAQ NDCG would fall; follow-up-ready on fusion weights.”

* **Apply It:**  
  1. Extract 8–10 stories from *your* Weeks 6–22 builds using the index titles as prompts.  
  2. For each card: before→after metric, systems touched, failure mode, alternative rejected, 3 follow-ups, dual endings.  
  3. Rehearse each story in 2–3 minutes with I-language; Action majority.  
  4. Drill 2 follow-ups per story (how measured, what still fails, ops cost).  
  5. Rehearse Applied AI ending and FDE ending separately for at least STARs 4, 7, 8, 9.  
  6. Never invent metrics — if a number is missing, re-run the eval or mark the card incomplete.  
  7. Ship the STAR index (title / metric / systems / 3 follow-ups) as the interview artifact; leave resume wording for Week 24.

---

## Week 23 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Whiteboard:** Run the 45-minute 10M-doc drill; pin requirements; force hybrid + ACL pre-filter + deletes + rerank budget + abstain + evals.  
2. **Annotate:** Keep the annotated whiteboard as an artifact.  
3. **Prompt-debug:** Run one 20-minute planted-failure ladder; save the transcript.  
4. **FDE case:** Rehearse one unblock Monday plan (no prod data / SSO / undocumented API).  
5. **Tradeoffs:** Memorize axes + six one-breath templates with latency/$ budgets.  
6. **STAR bank:** Fill 8–10 cards from own build; dual endings; 2–3 follow-up depths.  
7. **Interview artifact:** Annotated 10M whiteboard + timed prompt-debug transcript + FDE unblock case + STAR index + tradeoff one-liners.

When those steps are true, Week 23 is done in the syllabus sense: Week 22 polish is packaged for whiteboard, timed debug, FDE scenarios, aloud tradeoffs, and drillable STAR stories.

---

## Looking ahead

Week 24 is **portfolio positioning**. After this week’s 10M whiteboard, timed prompt-debug, FDE unblock case, aloud tradeoffs, and STAR bank, the typical remaining failure is hire-readable packaging: a screener cannot find your signal in under five minutes on a resume or portfolio page. Next week you **make evidence hire-readable**, not new interview drills: **mirror one live posting** into resume language with STAR-backed bullets; **ship a portfolio case under 5 minutes** (architecture matching code, three metrics, failure→fix, repro); **write dual talk tracks** for the same flagship — Applied AI Engineer (evals/latency/architecture) vs FDE (discovery/constraint/rollout/codify); freeze resume header + LinkedIn headline for the track you apply to this week. Do **not** start Week 24 by inventing metrics or reopening the Week 22 freeze — feed locked STAR evidence into resume and portfolio surfaces. Whiteboard and debug rehearsal stays available as maintenance; the deep work shifts to packaging for screens.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-6/week-23-system-design-interview/` (`00`–`05`, README; source map consulted for URL provenance only).  
- `[NEEDS MORE RESEARCH]` markers appear where research Open Questions leave a claim ungrounded: pgvector rejection corpus-size / GraphRAG expectation in 2026 loops; whether prompt-debug is a named round vs deep-dive (and live judge debugging / Anthropic AI-tool perception); FDE push-back vs absorb-chaos balance, MCP-as-default artifact, gov/classified discussion, travel % calibration; cost-number lead defaults / abstain-as-product-failure / vendor-lock explicitness in lab interviews; personal-project “production” bar, separate safety STAR bank, optimal story count before metric staleness. Those open questions were **not** resolved with invented answers.  
- Outside URLs from research are cited inline where the notes already named them; operational detail was inlined from the notes.  
- Editorial pass: Prerequisites Recap bridges Week 22 (scope freeze, eval-driven fixes, 5-min demo narrative); Looking ahead bridges Week 24 (resume language, portfolio under 5 min, dual-track AI Engineer vs FDE); no new technical claims beyond research.  
- Week 24 resume / portfolio language is explicitly deferred — extract STAR evidence here, polish wording later.
