# 00 — Week overview: freeze scope; top 5 eval bugs; 5-min walkthrough

> Week 22 — Capstone integration  
> Research notes (raw). Phase 6 week after legacy/messy integration (Week 21). Next: system-design interview drills (Week 23). Do not start STAR case-study packs or resume language from this corpus.

This file is the **design document** for the capstone polish week: lock a **demoable vertical slice**, turn eval logs into a **top-5 bug queue**, and rehearse a **5-minute walkthrough** that survives adversarial questions. Concept files 01–03 are the depth; this file is the stitched path.

---

## Fundamentals

Weeks 6–21 already shipped ingestion, retrieval, agents, evals, deploy, auth, cost, and messy integration. Week 22 adds **no new subsystem**. Capstone AI products fail less from missing models and more from **unbounded surface area**: extra tools, extra agents, extra UIs, extra corpora that never get hardened.

Three coupled deliverables:

1. **Scope freeze** — written contract for the demoable product (file [01](01-systems-integration-scope-freeze.md)).  
2. **Eval → fix queue** — taxonomy with counts; top bugs fixed or explicitly deferred (file [02](02-eval-log-driven-bug-fixes.md)).  
3. **Demo narrative** — claim → architecture → evidence → failure → next bet (file [03](03-technical-demo-narrative.md)).

### Freeze scope (what “done” means this week)

Lock four fields before touching prompts or models:

| Freeze field | Example for a dual-track capstone |
|--------------|-----------------------------------|
| **User job** | “Support analyst answers policy questions with citations from the internal KB + one SQL tool” |
| **Corpus / tools in scope** | Frozen PDF/HTML dump + `get_invoice(id)`; no web browse; no second agent |
| **Success metrics** | Citation faithfulness on golden set ≥ X; recall@5 ≥ Y; p95 &lt; Z ms; $/1k queries logged |
| **Known non-goals** | Multi-tenant admin UI, fine-tune, multi-agent debate, billing, mobile |

Chip Huyen’s GenAI platform framing is the **integration checklist**, not a feature wishlist: start from model API, add context (RAG/tools), guardrails, router/cache, then **logging/evals** — add components only when failure modes demand them ([Building a Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html)). Capstone polish = walk that stack end-to-end for **one** vertical slice until it is demo-safe.

Palantir FDSE narrative is the product metaphor: FDSEs enable **many capabilities for one customer** by composing an existing platform, not inventing a new platform per demo ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)). Translation: compose RAG + eval harness + one agent path; refuse greenfield side quests.

### Top 5 eval bugs (capstone work queue)

These are the failure classes that dominate RAG/agent capstones after Weeks 9–17 taxonomies. Rank with Hamel’s instinct: **frequency × user severity × fix leverage** — not “average score +2%” ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/); [Field Guide](https://hamel.dev/blog/posts/field-guide/)).

| Rank | Failure class | Typical root cause | Fix leverage | Demo impact if unfixed |
|------|---------------|--------------------|--------------|------------------------|
| **1** | **Wrong / empty retrieval** | Bad chunk metadata, filter bugs, stale index, hybrid weight off | High — ordinary engineering | Happy path cites irrelevant docs; interviewer stops trusting the stack |
| **2** | **Ungrounded / fake citations** | Generator invents quotes; citation mapper off-by-one; no faithfulness check | High — assert + prompt + post-check | Looks like a wrapper that lies under pressure |
| **3** | **Tool schema / selection bugs** | Wrong args, missing required fields, retries of non-idempotent writes | High — schema + validation | Live tool path flakes; duplicate side effects (Week 21) |
| **4** | **Refusal / abstain failures** | Answers when corpus miss; or over-refuses easy questions | Medium — prompt + retrieval threshold + eval cases | Cannot demo control; either hallucinates or looks broken |
| **5** | **ACL / tenancy / PII leak** | Filter applied after rank; prompt injects other-tenant context | Severity-max even if rare | Catastrophic in FDE / enterprise loops; deferring is not optional |

**How to use the table:** open-code 20–50 traces (Hamel minimum after significant changes); axial-code into *your* names (`invoice_tool_arg_missing`, not generic `hallucination`); count; map into these five buckets if they fit; fix 1→3 immediately; treat #5 as severity override; write ≥1 regression case per fixed mode ([error-analysis FAQ](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html); Lenny’s Podcast [YouTube `BsWxPI9UM4c`](https://www.youtube.com/watch?v=BsWxPI9UM4c)).

Many issues found in error analysis are **ordinary bugs** — fix them; only persistent subjective failures need judge infrastructure (Weeks 16–17).

### Five-minute walkthrough demo (script skeleton)

Target hybrid timing used across ML systems teaching and RAG interview rubrics:

| Segment | Time | What you say / show |
|---------|------|---------------------|
| **User & stakes** | 0:00–0:45 | Who, what decision, cost of being wrong |
| **Requirements freeze** | 0:45–1:15 | Latency budget, corpus size, freshness, refusal policy, ACL |
| **Architecture (request + offline)** | 1:15–2:30 | Query → retrieve/hybrid → rerank → generate → cite/guardrail; ingest → index → eval gate |
| **Live success** | 2:30–3:30 | Happy path with **visible citations** / tool trace |
| **Live failure** | 3:30–4:30 | Intentional abstain **or** tool error; narrate control |
| **Metrics + tradeoffs + non-goals** | 4:30–5:00 | recall/faithfulness/p95/$; what you cut; roadmap only if asked |

Interviewers trust demos that show **control under failure**, not peak vibes ([Chip Huyen ML interviews](https://www.youtube.com/watch?v=pli1K75PSa8); [ML systems design TOC](https://huyenchip.com/machine-learning-systems-design/toc.html)). Palantir Foundry deskside videos are the visual metaphor for a composed workflow demo — ingest → ontology/workflow → interactive action — not a feature tour ([Developer Deskside](https://www.youtube.com/watch?v=bPGnvfyMuxE)).

### End-to-end polish path

```
written demo contract (scope freeze)
        │
        ▼
eval sample → open code → taxonomy counts
        │
        ▼
fix top-5 classes (1–3 first; #5 severity override)
        │
        ▼
promote failures → golden / CI eval command
        │
        ▼
5-min script: success + refusal + one integration failure
        │
        ▼
architecture diagram matching code + metrics line + STAR from one fix
```

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| Scope freeze + demo contract | New retrieval theory (Weeks 6–8) — still **use** those indexes |
| Eval-log triage → bug queue | Judge calibration deep-dive (Week 17) — reuse existing judges |
| 5-min narrative + failure demos | System-design whiteboard packs (Week 23) |
| Integration polish on Weeks 18–21 seams | Resume / portfolio language (Week 24) |
| One STAR from a real fix | Full FDE case library |

---

## Alternatives & Tradeoffs

| Capstone strategy | Gain | Risk |
|-------------------|------|------|
| **Vertical slice freeze** | Demo coherence; stable golden set | Looks “small” unless metrics + failure narrative are strong |
| **Horizontal sprawl** (chat + agents + multi-tenant + dashboard) | Slideware impressiveness | Brittle live demo; every surface is attack surface |
| **Eval-first polish week** | Strong Applied AI signal | Needs prepared traces; mishandled failures look broken |
| **Model-swap week** | Easy to narrate | Usually wrong layer; Hamel: fix bugs found in analysis first |
| **Recorded-only demo** | Safe when infra flakes | Weak for FDE loops that expect shipping instincts |
| **Live-only, no backup** | Ops confidence signal | Single flake can tank the round |

Tradeoff rule: **latency and refusal behavior beat** another model swap. Long-context-only vs RAG is itself a scope decision (Anthropic: small KB + prompt caching can skip RAG; beyond that, retrieval is the product — [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)).

---

## Necessity

Without a freeze:

- Eval logs never stabilize (corpus keeps changing → golden set invalid).  
- Demo narrative fragments (“and also we have an agent that…”).  
- Integration bugs (partial ETL, stale index, ACL leaks) surface live because they were deferred as “infra.”

Without eval triage: random prompt thrash; wrong-layer “improvements”; nothing to say when asked “how do you know it works?”

Without narrative structure: interviewers fill gaps with worst assumptions (prompt-only toy, no evals, no production thinking).

Palantir FDSE write-ups center **focus** as the hard skill: infinite customer problems; pick the highest-value next increment and ship under time pressure.

---

## Industry Practice

| Bar | What it looks like |
|-----|--------------------|
| **Common** | Freeze UI copy and model ID; hack prompts until the day before; traces exist in Langfuse/Phoenix but nobody triages |
| **Strong** | Written **demo contract**; top-3/5 failure modes on README; each mode ≥1 regression test; success + refusal + tool-error rehearsed |
| **Senior / FDE-shaped** | Freeze around the **integration seam** (legacy DB + docs + identity); eval frameworks called out as production LLM experience ([Anthropic FDE posting](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)); OpenAI FDE owns end-to-end deployment with strategic customers |

OpenAI public FDE framing: own the full arc of deployment (travel up to ~50% in some postings). Anthropic Applied AI / FDE: ship production apps, MCP, agents, **eval frameworks** in customer environments — scope is transformational adoption, not feature count.

---

## Concrete Scenario (URL)

1. **Scope under time pressure.** Palantir FDSE COVID response: solutions **operational within days**; listed challenges are pipeline scale, access controls, workflow UX, production outage investigation — not “add another model” ([blog](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).  
2. **Progressive architecture.** Huyen starts simple and adds components when failure modes demand them ([GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html); [LLM apps for production](https://huyenchip.com/2023/04/11/llm-engineering.html)).  
3. **Eval → fix.** Nurture Boss / Field Guide pattern: bottom-up coding finds a few issues covering most failures; targeted tests move a mode from ~33% → ~95% success ([Field Guide](https://hamel.dev/blog/posts/field-guide/); Lenny’s [YouTube](https://www.youtube.com/watch?v=BsWxPI9UM4c)).  
4. **Composed product demo.** Palantir Developer Deskside: ingest public data → ontology → workshop app in one walkthrough ([YouTube `bPGnvfyMuxE`](https://www.youtube.com/watch?v=bPGnvfyMuxE)).

---

## Open Questions

- For interview demos, is a single-tenant vertical slice stronger than a multi-tenant stub that proves ACL filtering?  
- What severity weight should safety / ACL failures get relative to answer quality when only five minutes exist?  
- Should capstone demos default to recorded backup + live primary, or live-only to signal ops confidence?  
- How do you present “we fixed 3 of 7 taxonomy buckets” without sounding unfinished?  
- When does agentic orchestration belong in the frozen demo vs stay as a roadmap slide?

---

## Sources

- Chip Huyen, Building a Generative AI Platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Chip Huyen, Building LLM applications for production: https://huyenchip.com/2023/04/11/llm-engineering.html  
- Chip Huyen, ML Systems Design TOC: https://huyenchip.com/machine-learning-systems-design/toc.html  
- Chip Huyen, ML Interviews book (free): https://huyenchip.com/ml-interviews-book/  
- Hamel Husain, Your AI Product Needs Evals: https://hamel.dev/blog/posts/evals/  
- Hamel, Error analysis FAQ: https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html  
- Hamel, Field Guide: https://hamel.dev/blog/posts/field-guide/  
- Hamel / Shreya, Lenny’s Podcast (YouTube): https://www.youtube.com/watch?v=BsWxPI9UM4c  
- Palantir FDSE day-in-life: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- Palantir Developer Deskside (YouTube): https://www.youtube.com/watch?v=bPGnvfyMuxE  
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval  
- Anthropic FDE (Greenhouse): https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- OpenAI FDE (SF) posting: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- Chip Huyen ML interviews (YouTube): https://www.youtube.com/watch?v=pli1K75PSa8  
- Chip Huyen Stanford MLSys (YouTube): https://www.youtube.com/watch?v=c_AUuTuPA5k  
