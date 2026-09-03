# Week 22 — Capstone Integration (Raw Source Material)

> Syllabus says “concepts: none new” — these are **meta-concepts**: integration polish, eval→fix prioritization, and demo narrative that interviewers trust. Legal public sources only. Not textbook prose.

---

## Concept 1 — Systems Integration / Freezing Scope for Demoable AI Products

### Fundamentals

A capstone AI product fails less from missing models and more from **unbounded surface area**: extra tools, extra agents, extra UIs, extra data sources that never get hardened. “Freeze scope” means deliberately locking (1) **user job**, (2) **corpus / tools in scope**, (3) **success metrics**, and (4) **known non-goals** so the remaining engineering time goes to integration reliability—auth, ingestion freshness, retrieval quality, latency budget, fallbacks, and observability.

Chip Huyen’s GenAI platform framing is the integration checklist, not a feature wishlist: model API → guardrails → context construction (RAG/tools) → caching/routing → logging/evals. Capstone polish is walking that stack end-to-end for **one** vertical slice until it is demo-safe under adversarial questions.

Palantir’s FDSE narrative is the product metaphor for scope discipline: FDSEs enable **many capabilities for one customer** by composing an existing platform, not inventing a new platform per demo. Translation for a capstone: compose what you already built (RAG + eval harness + one agent path); refuse greenfield side quests in the last stretch.

### Alternatives & Tradeoffs

| Scope strategy | What you gain | What you lose / risk |
| --- | --- | --- |
| **Vertical slice freeze** (one persona, one workflow, one corpus) | Demo coherence; measurable eval set; clear architecture story | Looks “small” unless metrics + failure narrative are strong |
| **Horizontal feature sprawl** (chat + agents + multi-tenant + dashboard) | Impressive slideware | Brittle live demo; interviewer probes any weak surface |
| **Platform-first** (generic “AI OS”) | Resume keywords | No believable user outcome; hard to STAR later |
| **Customer-shaped cut** (freeze around one messy integration: SQL + docs + ACL) | FDE-signal authenticity | Higher integration cost; must timebox ruthlessly |

Tradeoff rule of thumb for demos: **latency and refusal behavior beat** another model swap. Long-context-only vs RAG is itself a scope decision (Anthropic: KB ≲ ~200k tokens can skip RAG; beyond that, retrieval is the product).

### Necessity

Without a freeze:

- Eval logs never stabilize (corpus keeps changing → golden set invalid).
- Demo narrative fragments (“and also we have an agent that…”).
- Integration bugs (partial ETL, stale index, ACL leaks) surface live because they were deferred as “infra.”

Palantir FDSE write-ups repeatedly center **focus** as the hard skill: infinite customer problems; pick the highest-value next increment and ship it under time pressure.

### Industry Practice

- **Common:** freeze UI copy and model ID; keep hacking prompts until the day before.
- **Strong:** freeze a written **demo contract**—happy path script, 3 failure demos (abstain, bad retrieval, tool error), rollback plan, and a “out of scope” slide.
- **Senior / FDE-shaped:** freeze around the **integration seam** (legacy DB + document store + identity), because that is what OpenAI/Anthropic FDE postings describe as the job: discovery → scoping → system design → build → production rollout inside customer systems.

OpenAI FDE postings emphasize owning end-to-end deployment with strategic customers (travel up to ~50%). Anthropic Applied AI / FDE postings emphasize shipping production apps, MCP servers, agents, and eval frameworks **in customer environments**—scope is “transformational adoption,” not feature count.

### Concrete Scenario (URL)

Palantir’s public “Day in the Life” FDSE piece: COVID response solutions that had to be **operational within days**; technical challenges listed are pipeline scale, access controls, workflow UX, and production outage investigation—not “add another model.”

- https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1

Huyen’s progressive GenAI architecture (start simple, add components only when failure modes demand them):

- https://huyenchip.com/2024/07/25/genai-platform.html

Anthropic on when *not* to build RAG (small KB + prompt caching) vs when retrieval becomes necessary:

- https://www.anthropic.com/news/contextual-retrieval

### Open Questions

- For interview demos, is a single-tenant vertical slice stronger than a multi-tenant stub that proves ACL filtering?
- How much “productization” (billing, admin UI) is net-positive vs noise for Applied AI Engineer vs FDE loops?
- When does agentic orchestration belong in the frozen demo vs stay as a roadmap slide?

### Sources

- Chip Huyen, Building a Generative AI Platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Palantir, Day in the Life of an FDSE: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- OpenAI FDE (SF) posting: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- Anthropic FDE (Greenhouse): https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval  
- ByteByteGo, How Agentic RAG Works (when loops are *not* default): https://blog.bytebytego.com/p/how-agentic-rag-works  

---

## Concept 2 — Turning Eval Logs into Prioritized Bug Fixes

### Fundamentals

Eval logs are not a dashboard vanity metric; they are a **work queue**. Hamel Husain’s error-analysis loop is the meta-skill for capstone weeks:

1. Sample traces (start ~20–50; often first failure in a trace).
2. Open-ended notes (“journaling”) by a domain-aware reviewer.
3. Axial coding → **failure taxonomy** with counts.
4. Write evals *for observed modes* (code assertions vs LLM-judge).
5. Fix highest-frequency / highest-severity classes first; regenerate/expand golden set; repeat.

Priority is usually **frequency × user severity × fix leverage**, not “average score went up 2%.” Many issues found in error analysis are ordinary bugs (bad chunk metadata, wrong tool schema, prompt contradiction)—fix immediately; only persistent subjective failures need judge infrastructure.

### Alternatives & Tradeoffs

| Prioritization heuristic | Strength | Weakness |
| --- | --- | --- |
| **Count-ranked taxonomy** | Forces focus; demos “data-driven iteration” | Can undervalue rare catastrophic failures (ACL leak, unsafe action) |
| **Severity / blast-radius first** | Matches production / FDE instincts | Needs explicit severity rubric or you thrash |
| **Metric chasing** (generic coherence/fluency) | Easy tooling | Misaligned with product; Hamel warns against platform default metrics |
| **Only automated judges** | Scales | Without human error analysis, you optimize the wrong thing |
| **Only vibe checks** | Fast early | No regression gate; demo flips flop |

Binary pass/fail + critique text often beats 1–5 Likert for iteration speed (Hamel).

### Necessity

Skipping error analysis → writing generic evals → “improving” the wrong layer (swap LLM when retrieval recall is the bug). Capstone without a prioritized fix list looks like random prompt thrash in demos and interviews.

### Industry Practice

- **Common:** Langfuse/Phoenix traces exist; nobody triages them weekly.
- **Strong:** spreadsheet or tagged traces → top-3 failure modes on the README; each mode has ≥1 regression test; CI blocks prompt/retrieval changes that regress the golden set.
- **FDE/Applied AI signal:** Anthropic FDE posting explicitly lists **evaluation frameworks** alongside prompt engineering, agents, and production deployment as required production LLM experience.

### Concrete Scenario (URL)

Hamel’s canonical evals essay + FAQ on why error analysis comes before tests; office-hours note on analyzing real conversations before Azure-style generic metrics:

- https://hamel.dev/blog/posts/evals/  
- https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- https://hamel.dev/notes/llm/officehours/erroranalysis.html  
- FAQ hub: https://hamel.dev/blog/posts/evals-faq/

### Open Questions

- What severity weight should safety / ACL failures get relative to answer quality in a hiring demo?
- When is synthetic expansion of failure modes safe vs distribution-shift theater?
- How do you present “we fixed 3 of 7 taxonomy buckets” without sounding unfinished?

### Sources

- Hamel Husain, Your AI Product Needs Evals: https://hamel.dev/blog/posts/evals/  
- Hamel, Error analysis FAQ: https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- Hamel, Evals FAQ index: https://hamel.dev/blog/posts/evals-faq/  
- Anthropic FDE responsibilities (evals called out): https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Chip Huyen GenAI platform (logging/eval as platform layer): https://huyenchip.com/2024/07/25/genai-platform.html  

---

## Concept 3 — Technical Demo Narrative Structure (Architecture Walkthrough Interviewers Trust)

### Fundamentals

A trusted AI demo is not a feature tour. It is a **claim → architecture → evidence → failure → next bet** narrative that an interviewer can stress-test.

Working structure used across ML systems design teaching (Chip Huyen) and RAG interview rubrics:

1. **User & stakes** (30–60s): who, what decision/action, cost of being wrong.
2. **Requirements freeze**: latency budget, corpus size, freshness, refusal policy, ACL.
3. **Request path**: query → (route) → retrieve/hybrid → rerank → generate → cite/guardrail.
4. **Offline path**: ingest → chunk/context → embed/index → eval gate.
5. **Live proof**: happy path with citations; then intentional failure (abstain / tool error).
6. **Metrics**: recall@k / faithfulness / p95 latency / $/1k queries — even approximate.
7. **Tradeoffs said aloud**: what you cut to hit the demo contract.
8. **Roadmap as non-goals**: agent loop, multi-tenant, fine-tune — only if asked.

Interviewers trust demos that show **control under failure**, not peak vibes. Chip Huyen’s ML systems design interview framing: open-ended; no single correct answer; signal is structured iteration across project setup → data → modeling → serving.

### Alternatives & Tradeoffs

| Narrative style | Pros | Cons |
| --- | --- | --- |
| **Architecture-first** (boxes then demo) | Signals systems maturity | Can bore; delay user value |
| **User-journey-first** (show chat, reverse-engineer) | Sticky | Looks like a wrapper unless you open the hood |
| **Eval-first** (show failing cases → fix) | Extremely strong for Applied AI | Needs prepared traces; risk of looking broken if mishandled |
| **Slide-only** | Safe when live infra flakes | Weak for FDE loops that expect shipping instincts |

Best hybrid for dual-track prep: **60s user stakes → 90s architecture → 2–3 min live (success + refusal) → 60s metrics/tradeoffs.**

### Necessity

Without narrative structure, interviewers fill gaps with worst assumptions (prompt-only toy, no evals, no production thinking). With structure, the same codebase reads as an AI Engineer / FDE artifact.

### Industry Practice

- RAG interview guides repeatedly score: requirements clarification, ACL-before-rank, latency budget allocation, eval gate, guardrails—**without being prompted**.
- OpenAI/Anthropic SWE loops (public candidate reports) emphasize production-shaped system design and project deep-dives more than URL shortener classics; values/safety rounds at Anthropic punish careless “just ship it” stories.
- FDE loops (Palantir-origin pattern) weight **customer scenario / ambiguity handling** alongside coding—demo narrative should include a discovery → constraint → ship moment.

### Concrete Scenario (URL)

Eight-layer RAG interview framing (corpus, ingest, retrieval, generation, evals, observability, cost, guardrails) with explicit hire signals:

- https://technoscripts.com/python-rag-system-design/

Chip Huyen ML systems design TOC / interview exercise framing:

- https://huyenchip.com/machine-learning-systems-design/toc.html  
- https://github.com/chiphuyen/machine-learning-systems-design  

Huyen free ML interviews book (role signals, what interviewers look for):

- https://huyenchip.com/ml-interviews-book/  
- https://github.com/chiphuyen/ml-interviews-book  

### Open Questions

- Should capstone demos default to recorded backup + live primary, or live-only to signal ops confidence?
- How explicit should cost numbers be when they are estimates?
- For FDE interviews, how much customer-stakeholder fiction is acceptable in a personal project demo?

### Sources

- Chip Huyen, ML Systems Design: https://huyenchip.com/machine-learning-systems-design/toc.html  
- Chip Huyen, ML Interviews Book: https://huyenchip.com/ml-interviews-book/  
- Chip Huyen, GenAI platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- RAG system design interview layers: https://technoscripts.com/python-rag-system-design/  
- SDE→AI RAG practice rubric: https://sde2ai.com/practice/rag  
- Palantir FDSE day-in-life (impact under time pressure): https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- OpenAI FDE role framing: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  

---

## Week 22 Meta-Checklist (Capstone Polish)

Use as a research-derived punch list, not new technical concepts:

| Gate | Pass criterion |
| --- | --- |
| Scope freeze | One primary user job + written non-goals |
| Integration | Happy path works on clean machine / deploy URL |
| Eval triage | Taxonomy with counts; top bugs fixed or explicitly deferred with reason |
| Regression | Golden set in CI or scripted eval command in README |
| Demo script | Success + refusal + one integration failure narrated |
| Architecture | Diagram matching actual code paths (no vapor boxes) |
| Metrics | At least quality + latency + cost proxy |
| Interview bridge | One STAR-ready story extracted from a real fix |
