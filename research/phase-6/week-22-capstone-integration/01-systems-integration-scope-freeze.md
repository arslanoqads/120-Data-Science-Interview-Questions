# 01 — Systems integration / freezing scope for demoable AI products

> Week 22 — Capstone integration  
> Research notes (raw). Meta-concept: scope discipline, not a new model capability.

---

## Fundamentals

**Freezing scope** means deliberately locking (1) **user job**, (2) **corpus / tools in scope**, (3) **success metrics**, and (4) **known non-goals** so remaining engineering time goes to integration reliability—auth, ingestion freshness, retrieval quality, latency budget, fallbacks, and observability.

A capstone AI product fails less from missing models and more from **unbounded surface area**. Extra agents, extra UIs, and extra data sources that never get hardened create brittle live demos. Interviewers probe any weak surface.

### The GenAI platform as an integration checklist

Chip Huyen’s [Building a Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html) describes how production GenAI stacks grow **progressively**:

1. Query → model API → response (simplest).  
2. **Enhance context** — external data / tools (RAG, retrieval, function calls).  
3. **Guardrails** — input/output safety, policy.  
4. **Router / gateway** — multi-model, security, complex pipelines.  
5. **Cache** — latency and cost.  
6. **Complex logic / write actions** — agents, side effects.  
7. **Observability** — logging, tracing, evals.

Capstone polish is **not** implementing every box from scratch in Week 22. It is walking the stack you already built for **one vertical slice** until each hop is demo-safe under adversarial questions. Huyen’s earlier [LLM applications for production](https://huyenchip.com/2023/04/11/llm-engineering.html) punchline still applies: easy to make something cool; hard to make something production-ready.

Add components only when **failure modes demand them**. That is the freeze discipline: if long-context + prompt caching covers a ≤~200k-token KB, Anthropic argues you may skip RAG; beyond that, retrieval *is* the product ([Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)). Choosing “no RAG” or “hybrid RAG” is a scope decision, not a resume checkbox.

### FDSE composition metaphor

Palantir’s public FDSE piece: a Forward Deployed Software Engineer enables **many capabilities for one customer** by configuring/composing an existing platform (Foundry/Gotham), not inventing a new platform per engagement ([Day in the Life](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)). Contrast with a “Dev” who builds one capability for many customers.

Capstone translation:

| FDSE instinct | Capstone move |
|---------------|---------------|
| Compose platform features | Compose your Weeks 6–21 modules (ingest, retrieve, agent, eval, deploy, auth) |
| Operational in days | Demo contract + hardened happy path, not a new architecture |
| Focus is the hard skill | Written non-goals; kill side quests |
| Technical challenges listed | Pipelines, ACL, workflow UX, outage investigation — not “another model” |

Public Foundry deskside demos show the same composition story visually: ingest → model/ontology → interactive workflow in one sitting ([YouTube `bPGnvfyMuxE`](https://www.youtube.com/watch?v=bPGnvfyMuxE)).

### What a written demo contract contains

Strong teams freeze more than a model ID:

1. **Happy-path script** (exact query, expected citation / tool).  
2. **Three failure demos** — abstain (corpus miss), bad retrieval recovered or labeled, tool error / timeout with structured message.  
3. **Rollback plan** — pin model + prompt version; known-good index snapshot.  
4. **Out-of-scope slide** — one line each for agent loop v2, multi-tenant, fine-tune.  
5. **Clean-machine / deploy URL check** — someone else can run README steps.

OpenAI and Anthropic public FDE postings describe the job as discovery → scoping → system design → build → production rollout **inside customer systems**. Scope is transformational adoption and reliability, not feature count ([OpenAI FDE SF](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/); [Anthropic FDE](https://job-boards.greenhouse.io/anthropic/jobs/5391016008)).

### Freeze vs progressive enhancement

Huyen’s ML systems design teaching frames projects as **iterative**: project setup → data → modeling → serving → business feedback ([ML Systems Design TOC](https://huyenchip.com/machine-learning-systems-design/toc.html); Stanford MLSys talk [YouTube `c_AUuTuPA5k`](https://www.youtube.com/watch?v=c_AUuTuPA5k)). Freeze does **not** mean stop iterating. It means iterate **inside** a locked user job and corpus so evals remain valid.

---

## Alternatives & Tradeoffs

| Scope strategy | What you gain | What you lose / risk |
| --- | --- | --- |
| **Vertical slice freeze** (one persona, one workflow, one corpus) | Demo coherence; measurable eval set; clear architecture story | Looks “small” unless metrics + failure narrative are strong |
| **Horizontal feature sprawl** (chat + agents + multi-tenant + dashboard) | Impressive slideware | Brittle live demo; interviewer probes any weak surface |
| **Platform-first** (generic “AI OS”) | Resume keywords | No believable user outcome; hard to STAR later |
| **Customer-shaped cut** (freeze around one messy integration: SQL + docs + ACL) | FDE-signal authenticity | Higher integration cost; must timebox ruthlessly |
| **Long-context only** (no RAG) | Simpler ops for small KB | Cost/latency walls; loses retrieval as a product story |
| **Agent-default** (loops on every query) | Looks advanced | Latency, cost, nondeterminism; ByteByteGo-class agentic RAG is not the default path |

Tradeoff rule of thumb for demos: **latency and refusal behavior beat** another model swap.

---

## Necessity

Without a freeze:

- **Eval logs never stabilize** — corpus/tool changes invalidate the golden set (Hamel: evals need representative, stable-enough data).  
- **Demo narrative fragments** — “and also we have an agent that…” invites probes into unfinished surfaces.  
- **Integration bugs surface live** — partial ETL, stale index, ACL leaks deferred as “infra.”  
- **Focus collapses** — Palantir FDSE: near-infinite problems; directing focus is the hard part of the role.

Skipping the written non-goals list is how Week 22 becomes an accidental Week 11–15 rewrite.

---

## Industry Practice

| Bar | Practice |
|-----|----------|
| **Common** | Freeze UI copy and model ID; keep hacking prompts until the day before; README promises multi-agent + multi-tenant “soon” |
| **Strong** | Written demo contract; pinned prompt/model/index versions; success + 3 failure demos rehearsed; architecture diagram matches code |
| **Senior / FDE-shaped** | Freeze around the **integration seam** (legacy DB + document store + identity) because that matches OpenAI/Anthropic FDE postings: ship in customer environments with evals, guardrails, and production rollout |

Chip Huyen interview guidance: interviewers look for structured thinking across the ML lifecycle, not a single “correct” architecture ([ML Interviews book](https://huyenchip.com/ml-interviews-book/); [YouTube `pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8)). A frozen slice with honest tradeoffs beats an unbounded architecture diagram.

---

## Concrete Scenario (URL)

**Palantir FDSE, COVID response.** Meaningful solutions had to be **operational within days**. Technical challenges Brian lists: terabyte-scale pipelines, access-control configuration under regulatory constraints, workflow UX for non-technical users on high-noise data, production outage investigation with cross-team coordination — explicitly not “swap the model” ([blog](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)).

**Huyen progressive GenAI architecture.** Start with query→model; add retrieval/tools when the model lacks facts; add guardrails when abuse/safety appears; add cache when latency/cost hurt; add write-actions when read-only is insufficient; instrument throughout ([GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html)).

**Anthropic RAG vs not.** Small knowledge bases can use long context + prompt caching; contextual retrieval / classical RAG becomes necessary as corpora grow ([Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)).

---

## Open Questions

- For interview demos, is a single-tenant vertical slice stronger than a multi-tenant stub that proves ACL filtering?  
- How much “productization” (billing, admin UI) is net-positive vs noise for Applied AI Engineer vs FDE loops?  
- When does agentic orchestration belong in the frozen demo vs stay as a roadmap slide?  
- Should the freeze date be absolute (no corpus adds) or allow golden-set expansion only?

---

## Sources

- Chip Huyen, Building a Generative AI Platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Chip Huyen, Building LLM applications for production: https://huyenchip.com/2023/04/11/llm-engineering.html  
- Chip Huyen, ML Systems Design: https://huyenchip.com/machine-learning-systems-design/toc.html  
- Chip Huyen, ML Interviews Book: https://huyenchip.com/ml-interviews-book/  
- Chip Huyen, Stanford MLSys (YouTube): https://www.youtube.com/watch?v=c_AUuTuPA5k  
- Chip Huyen, ML Interviews FSDL (YouTube): https://www.youtube.com/watch?v=pli1K75PSa8  
- Palantir, Day in the Life of an FDSE: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- Palantir Developer Deskside (YouTube): https://www.youtube.com/watch?v=bPGnvfyMuxE  
- OpenAI FDE (SF) posting: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- Anthropic FDE (Greenhouse): https://job-boards.greenhouse.io/anthropic/jobs/5391016008  
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval  
- ByteByteGo, How Agentic RAG Works: https://blog.bytebytego.com/p/how-agentic-rag-works  
