# Week 23 — System Design Interview (Raw Source Material)

> Meta-concepts for interview performance: RAG-at-scale design frameworks, prompt debugging under time pressure, FDE integration cases, aloud tradeoffs, STAR production stories. Legal public sources only.

---

## Concept 1 — AI System Design Interview Frameworks (Retrieval for ~10M Docs, Mixed Query Types)

### Fundamentals

Classic FAANG “URL shortener” muscle does not transfer cleanly. AI Engineer / FDE system design interviews typically probe **RAG / agent platforms**: corpus scale, mixed query types (keyword ID lookup, semantic FAQ, multi-hop, analytics), freshness, ACL, latency, cost, and evals.

A reusable whiteboard spine (compose from Huyen + Anthropic + ByteByteGo + common RAG interview rubrics):

1. **Clarify numbers**: docs N, chunks/doc, QPS, p95 latency, freshness SLA, wrong-answer cost, tenants.
2. **Split offline vs online**.
3. **Ingest**: parse → chunk (± contextualize) → embed + sparse index → versioned upsert; tombstones for deletes; delta index + compaction at 10M scale.
4. **Query understanding**: classify / rewrite / route (doc RAG vs SQL vs web vs abstain).
5. **Retrieve**: metadata/ACL **pre-filter** → hybrid dense+BM25 → fuse (e.g. RRF) → cross-encoder rerank → context pack + cite.
6. **Generate**: grounded prompt; refusal on low confidence; optional faithfulness check.
7. **Wrap**: semantic cache, tracing, golden-set eval gate, cost dashboards, guardrails.

**10M documents** is the canonical stress question because prototype shortcuts break: full re-embed, single unsharded index, post-filter ACL, dense-only retrieval, no deletion SLA.

**Mixed query types** force routing: exact error codes → BM25 wins (Anthropic TS-999 example); paraphrase FAQ → dense; “policy for contractors remote work” → multi-source / agentic loop; “top 10 SKUs by margin” → structured store, not vectors.

### Alternatives & Tradeoffs

| Decision | Option A | Option B | Say aloud |
| --- | --- | --- | --- |
| Index | pgvector / one DB | Dedicated vector DB + search engine | Ops simplicity vs scale/perf isolation; threshold often debated ~tens of millions vectors |
| Retrieval | Dense-only | Hybrid + rerank | Anthropic: hybrid contextual retrieval −49% failures; +rerank −67% vs baseline failure rate |
| Context | Stuff long context | RAG | Anthropic: ≲200k tokens may skip RAG with caching; else retrieval |
| Query path | One-shot RAG | Agentic RAG loop | ByteByteGo: loops fix ambiguity/scattered evidence; cost latency 3–10×; harder to test |
| Sharding | By doc count | By tenant/region/source/time | Shard on query + ACL patterns, not vanity counts |
| Freshness | Batch nightly | CDC / incremental upsert | “Time to searchable” becomes a first-class SLA at 10M |

### Necessity

Candidates who only draw “embed → vector DB → LLM” fail follow-ups on ACL, deletes, hybrid exact match, rerank budget, and evals. Frameworks exist to force those topics into the first 10 minutes.

### Industry Practice

- **Huyen GenAI platform:** production retrieval = hybrid; ANN tradeoffs; caching; progressive complexity.
- **Anthropic Contextual Retrieval:** Contextual Embeddings + Contextual BM25; rerank; measured recall failure reductions.
- **ByteByteGo:** RAG stack diagrams; Perplexity case (hybrid retrieval + model routing); Agentic RAG as optional control loop.
- **Interview rubrics:** pin requirements; filter ACL before rank; allocate latency budget; gate deploys on evals.

### Concrete Scenario (URL)

Anthropic measured stacking hybrid + contextualization + rerank:

- https://www.anthropic.com/news/contextual-retrieval  

Huyen platform architecture essay:

- https://huyenchip.com/2024/07/25/genai-platform.html  

ByteByteGo RAG / Perplexity / Agentic RAG:

- https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data  
- https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google  
- https://blog.bytebytego.com/p/how-agentic-rag-works  

Public “10M docs” design discussions (treat as interview practice notes, not vendor gospel):

- https://www.banandre.com/blog/rag-at-scale-system-design-10-million-documents  
- https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  

Chip Huyen open-ended ML systems design questions:

- https://huyenchip.com/machine-learning-systems-design/toc.html  

### Open Questions

- At what corpus size do interviewers expect you to reject pure Postgres-pgvector?
- Is GraphRAG expected in 2026 loops or still a “nice if asked” branch?
- How much GPU/inference serving design bleeds into Applied AI Engineer vs platform SWE interviews?

### Sources

- Chip Huyen GenAI platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval  
- ByteByteGo RAG: https://blog.bytebytego.com/p/how-rag-enables-ai-for-your-data  
- ByteByteGo Perplexity: https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google  
- ByteByteGo Agentic RAG: https://blog.bytebytego.com/p/how-agentic-rag-works  
- RAG interview 8-layer guide: https://technoscripts.com/python-rag-system-design/  
- Enterprise RAG HLD case: https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  

---

## Concept 2 — Prompt Debugging Under Time Pressure

### Fundamentals

Two interview settings share the same skill:

1. **Prompt/system debug round:** broken RAG/agent; find why outputs fail.
2. **AI-assisted coding round:** you must prompt a model to ship code while narrating.

Under time pressure, strong candidates run a **diagnostic ladder**, not vibes:

1. **Reproduce** with a fixed failing input; write expected vs actual.
2. **Localize layer**: retrieval miss vs ranking vs grounding vs tool schema vs prompt contradiction vs evaluator bug (reuse RAG failure taxonomy).
3. **Minimize**: strip tools/context until behavior flips.
4. **Hypothesize aloud** one change; apply; re-run same case.
5. **Lock regression**: add unit/golden case before moving on.

For AI-paired coding interviews, public guidance converges: small verified prompts > mega-prompt; specify stack/files/constraints/tests; never paste unread diffs; reset context when drift accumulates.

### Alternatives & Tradeoffs

| Move | When good | When bad |
| --- | --- | --- |
| Jump to bigger model | After confirming retrieval/context OK | Hides root cause; burns time/cost |
| Add few-shot | Format/style failures | Masks missing evidence |
| Raise top-k | Suspected recall miss | Adds noise; may worsen extraction |
| Rewrite prompt | Instruction conflict / refusal policy | Won’t fix absent chunks |
| One-shot “fix everything” AI prompt | Never in interview | Unreviewable; signals loss of control |

### Necessity

Interviewers score **process visibility**. Silent thrashing or blind model swaps read as junior. Structured localization reads as production ownership—especially for FDE, where debugging customer systems under ambiguity is the job.

### Industry Practice

- Capstone/product: Hamel-style error analysis on a handful of traces beats prompt roulette.
- Meta-style AI coding rounds (public writeups): Understand → Strategy → Code → Verify timeboxes; verify every AI edit.
- Debugging interviews generally: narrate priorities; state what you will *not* investigate.

### Concrete Scenario (URL)

Prompting tactics under timed AI-assisted rounds:

- https://dsa.handbook.academy/curriculum/interview-framework/meta-ai-round-prompting/  
- https://www.techinterview.org/post/3233474912/prompt-engineering-during-coding-interview/  
- https://interviewera.com/blog/ai-prompt-engineering-interview  

Real-time debugging interview expectations:

- https://interviewnode.com/post/real-time-debugging-interviews-what-companies-expect-and-how-to-practice  

Huyen production LLM theme (control flow / evals over prompt magic) — essay commonly cited as `Building LLM Applications for Production` (2023):

- https://huyenchip.com/2023/04/11/llm-engineering.html  

### Open Questions

- Will frontier-lab loops standardize “prompt debug” as a named round or keep it inside project deep-dives?
- How much LLM-as-judge debugging is expected live vs offline?
- Does using AI tools in the interview help or hurt Anthropic values perception? (Check each company’s candidate AI policy.)

### Sources

- Meta AI-round prompting tactics: https://dsa.handbook.academy/curriculum/interview-framework/meta-ai-round-prompting/  
- Prompt engineering during coding interviews: https://www.techinterview.org/post/3233474912/prompt-engineering-during-coding-interview/  
- InterviewEra prompt engineering interview: https://interviewera.com/blog/ai-prompt-engineering-interview  
- Hamel evals / error analysis: https://hamel.dev/blog/posts/evals/  
- Chip Huyen LLM engineering essay: https://huyenchip.com/2023/04/11/llm-engineering.html  

---

## Concept 3 — FDE Case Study: Integration Blockers Become the Job

### Fundamentals

Forward Deployed / Applied AI Engineer work, per primary employers’ own words:

- **Palantir FDSE:** embed with customer; configure platforms; data integration; access controls; production outages; feed field learnings back to product. Not slide consulting.
- **OpenAI FDE:** discovery, technical scoping, system design, build, production rollout with strategic customers; hybrid of delivery + platform feedback; significant travel.
- **Anthropic FDE (Applied AI):** build production apps on Claude inside customer systems; deliver MCP servers, sub-agents, skills; white-glove deploy; codify repeatable patterns back to Product/Engineering; thrive in ambiguity.

**Integration blockers** (SSO, VPC, messy schemas, undocumented APIs, data residency, change control, “who owns the gold dataset?”) are not interruptions—they **are** the engagement. Interview case studies should center unblocking a path to a thin production slice, not inventing a novel architecture in a vacuum.

### Alternatives & Tradeoffs

| Response to blocker | FDE-shaped | Anti-pattern |
| --- | --- | --- |
| Missing API | Adapter + contract test; escalate owner | Wait for perfect platform |
| Dirty SQL | Bounded views/ETL with idempotent jobs | Boil-the-ocean warehouse rewrite |
| Security review | Threat model + least privilege path | Shadow IT deploy |
| Model quality complaints | Error analysis on *their* traces | “Try GPT-whatever” |
| Scope creep | Written freeze + measurable pilot KPI | Infinite PoC |

### Necessity

Candidates who only talk greenfield RAG demos fail FDE scenarios that ask: “Customer won’t give prod data for two weeks—what do you do Monday?”

### Industry Practice

Reported FDE loops (secondary sources; treat cautiously) often include a **customer scenario** round testing composure, clarifying questions, and prioritization. Palantir alumni narratives emphasize rapid cycle with users and engineering rigor in the field.

Anthropic manager/Head of FDE postings stress playbooks, MCP/agent packages, measurable time-to-value—i.e., institutionalizing integration patterns.

### Concrete Scenario (URL)

Primary role definitions:

- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- https://job-boards.greenhouse.io/anthropic/jobs/5385634008  

Secondary synthesis of six-round FDE loops (anecdotal; not official):

- https://medium.com/@shivanathd/the-forward-deployed-engineer-interview-has-six-rounds-365df0544e2c  

### Open Questions

- How much “push back on customer” vs “absorb chaos” do labs want in 2026?
- Are MCP servers now a default artifact expectation in Anthropic-style loops?
- How to discuss classified/gov constraints without leaking or fabricating?

### Sources

- Palantir FDSE blog: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- OpenAI FDE SF: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- OpenAI FDE Gov: https://openai.com/careers/forward-deployed-engineer-gov-washington-dc/  
- Anthropic FDE: https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Anthropic FDE Manager: https://job-boards.greenhouse.io/anthropic/jobs/5385634008  

---

## Concept 4 — Narrating Tradeoffs Aloud (Recall vs Precision, Latency vs Quality, Build vs Buy)

### Fundamentals

Interview signal is rarely the choice itself; it is **naming the axes, picking for stated constraints, and saying what you monitor**. Core AI axes to practice saying in one breath each:

| Axis | If you optimize… | You often pay… | Monitor |
| --- | --- | --- | --- |
| **Recall vs precision** (retrieval) | Higher recall@k / more chunks | Noise, lost-in-middle, cost, grounding errors | recall@k, precision@k, faithfulness |
| **Latency vs quality** | Rerank + bigger model + agent loops | p95, $ | stage timings, abandonment |
| **Build vs buy** | Custom index/agents/evals | Ops burden | time-to-value, vendor lock, margins |
| **Freshness vs stability** | Aggressive re-index | Flickering answers, cost | time-to-searchable, churn |
| **Autonomy vs control** | More tools/agent steps | Irreproducibility, safety surface | trajectory evals, human gates |

ByteByteGo on Agentic RAG: loops are not free—latency, cost, debuggability, evaluator paradox. Anthropic on rerank: better retrieval vs added latency/cost—tune candidate counts. Huyen: start simple; add components when failure modes demand.

### Alternatives & Tradeoffs

Practice templates (fill constraints live):

- “I’d take hybrid+rerank because exact IDs matter; I’ll spend ~150–300ms of a 1.5s budget on rerank and cut model size to compensate.”
- “For FAQ traffic I’d buy managed search + API model; for data-plane actions inside the VPC I’d build the tool/MCP layer ourselves.”
- “Pilot metric is precision-oriented with abstain; after trust, we raise recall targets.”

### Necessity

Silent diagrams without tradeoffs read as memorized. Aloud tradeoffs read as design ownership—and match how FDE conversations with customer architects actually go.

### Industry Practice

Strong RAG interview answers allocate a **latency budget** across embed/retrieve/rerank/TTFT and a **cost budget** dominated by context tokens. Weak answers only say “we’ll use Pinecone and GPT-4.”

### Concrete Scenario (URL)

- Anthropic rerank latency/cost note: https://www.anthropic.com/news/contextual-retrieval  
- ByteByteGo Agentic RAG tradeoffs: https://blog.bytebytego.com/p/how-agentic-rag-works  
- Enterprise RAG “rerank budget” tradeoff writeup: https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  
- Huyen progressive platform complexity: https://huyenchip.com/2024/07/25/genai-platform.html  

### Open Questions

- Should candidates lead with cost numbers even when approximate?
- When is “abstain” the correct precision move vs a product failure?
- Build-vs-buy for eval harnesses: Langfuse/Phoenix vs in-house?

### Sources

- https://www.anthropic.com/news/contextual-retrieval  
- https://blog.bytebytego.com/p/how-agentic-rag-works  
- https://huyenchip.com/2024/07/25/genai-platform.html  
- https://hld.handbook.academy/curriculum/case-studies/enterprise-rag/  
- https://technoscripts.com/python-rag-system-design/  

---

## Concept 5 — STAR-Format Technical Case Studies from Production Builds

### Fundamentals

STAR = **Situation, Task, Action, Result** (+ **Learning** for senior). For AI Engineer / FDE, stories must be **technically drillable**: metrics, alternatives rejected, your personal actions, failure modes.

Amazon-oriented public coaching (useful beyond Amazon) stresses:

- Action ≈ majority of airtime; say “I” not “we.”
- Quantify: latency, error rate, cost, time-to-value, eval pass rate.
- Survive 2–3 follow-up depths (logs, queries, tradeoffs).
- Keep a bank of ~8–10 stories mapped to themes: incident, ambiguity, stakeholder conflict, tech debt, customer unblock, quality flywheel.

**Capstone → STAR extraction recipe:** pick one eval-driven fix from Week 22; write STAR with before/after metric and the alternative you did *not* take (e.g., “didn’t fine-tune; fixed chunk boundaries”).

### Alternatives & Tradeoffs

| Story type | Good for | Risk |
| --- | --- | --- |
| Outage / rollback | Ownership, incident muscle | Don’t blame teammates |
| Eval taxonomy → fix | Applied AI Engineer signal | Need real numbers |
| Customer integration unblock | FDE signal | Don’t violate NDAs; anonymize |
| Build vs buy decision | Judgment | Avoid fanboy vendor tales |
| Failed experiment | Learning / humility | Must show updated process |

Anthropic values rounds (public candidate reports) may punish pure STAR “team conflict” theater if it ignores model failure modes / safety—pair technical consequence with interpersonal stories.

### Necessity

Without STAR packaging, strong builds stay invisible. With empty STAR (no metrics/tradeoffs), packaging backfires under follow-up.

### Industry Practice

- Prepare dual endings: **Applied AI** emphasis on harnesses, latency/cost, architecture; **FDE** emphasis on discovery, constraint navigation, production rollout, pattern codification back to product.
- Keep a one-page story index: title, metric, systems touched, failure mode, 3 follow-up bullets.

### Concrete Scenario (URL)

STAR method explainers with engineering examples:

- https://prachub.com/resources/what-is-the-star-method-for-behavioral-interviews-with-faang-examples-2  
- https://leonstaff.com/blogs/amazon-leadership-principles-star-examples-engineers/  
- Amazon’s own interviewing guidance hub (behavioral / LP framing): https://www.amazon.jobs/content/en/how-we-hire/interviewing-at-amazon  

Map stories to employer language:

- Palantir FDSE: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- Anthropic FDE: https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- OpenAI FDE: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  

### Open Questions

- How “production” must a personal project be to count in frontier-lab loops?
- Should safety/values stories be separate from technical STAR bank?
- Optimal story length before interviewer interrupts (often ~2–3 minutes)?

### Sources

- https://prachub.com/resources/what-is-the-star-method-for-behavioral-interviews-with-faang-examples-2  
- https://leonstaff.com/blogs/amazon-leadership-principles-star-examples-engineers/  
- https://www.amazon.jobs/content/en/how-we-hire/interviewing-at-amazon  
- https://hamel.dev/blog/posts/evals/  
- Employer postings listed above  

---

## Drill Card — 45-Minute RAG Design (10M Docs)

Use as timed practice prompt:

> Design an enterprise assistant over 10M PDFs / HTML docs, 50 QPS peak, p95 ≤ 2s, multi-tenant ACL, mixed queries (IDs, semantic, multi-doc policy). Documents update continuously; deletes must stop being retrievable within 15 minutes.

Force yourself to hit: requirements → hybrid retrieve → ACL pre-filter → incremental index → rerank budget → abstain → eval metrics → cost → one agentic branch only if justified.
