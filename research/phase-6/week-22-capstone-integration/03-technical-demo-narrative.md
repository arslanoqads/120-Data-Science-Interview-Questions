# 03 — Technical demo narrative structure (architecture walkthrough interviewers trust)

> Week 22 — Capstone integration  
> Research notes (raw). Meta-concept: demo as claim → evidence → failure control, not a feature tour.

---

## Fundamentals

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

Interviewers trust demos that show **control under failure**, not peak vibes. Chip Huyen’s ML systems design interview framing: open-ended; no single correct answer; signal is structured iteration across project setup → data → modeling → serving ([ML Systems Design TOC](https://huyenchip.com/machine-learning-systems-design/toc.html); [GitHub](https://github.com/chiphuyen/machine-learning-systems-design)).

### Five-minute timing (default hybrid)

Best hybrid for dual-track (AI Engineer / FDE) prep:

| Clock | Beat | Anti-pattern |
|-------|------|--------------|
| 0:00–0:45 | User stakes | Starting in a boxes diagram |
| 0:45–1:15 | Requirements freeze | Skipping latency/ACL/refusal |
| 1:15–2:30 | Architecture (online + offline) | Vapor boxes not in code |
| 2:30–3:30 | Live success + citations/trace | Chat-only with no hood open |
| 3:30–4:30 | Live refusal or tool failure | Hiding failures; apologizing without structure |
| 4:30–5:00 | Metrics, tradeoffs, non-goals | Feature roadmap dump |

Recorded backup + live primary is the practical default for take-homes that require a video walkthrough (public reports of OpenAI-style FDE loops emphasize recorded defence of decisions). Live-only can signal ops confidence but needs a rollback story.

### What “opening the hood” means

During the success path, show at least one of:

- Retrieved chunks with scores / filters.  
- Citation highlights aligned to answer spans.  
- Tool call JSON (name, args, structured error on failure path).  
- Eval command or golden-set row that covers this query class.

Hamel’s product-eval ethos applies to demos: you should be able to debug quickly because traces, assertions, and navigation exist ([Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)). A demo that cannot show a trace when asked “where did that citation come from?” fails the trust test.

### Career / interview signal

Chip Huyen’s Full Stack Deep Learning talk on ML interviews covers role types, process noise, and portfolio signals — thoughtful public work and clear explanation beat credential theater ([YouTube `pli1K75PSa8`](https://www.youtube.com/watch?v=pli1K75PSa8); free book: [ml-interviews-book](https://huyenchip.com/ml-interviews-book/)). Stanford MLSys: production ML is iterative systems design, not a single model choice ([YouTube `c_AUuTuPA5k`](https://www.youtube.com/watch?v=c_AUuTuPA5k); Databricks cut: [YouTube `g08qBcdk3Ss`](https://www.youtube.com/watch?v=g08qBcdk3Ss)).

FDE loops (Palantir-origin pattern) weight **customer scenario / ambiguity handling** alongside coding. Demo narrative should include a discovery → constraint → ship moment. Palantir FDSE day-in-life: impact under time pressure, ACL, pipelines, outages ([blog](https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1)). Foundry deskside videos model a composed workflow demo rather than a slide deck ([YouTube `bPGnvfyMuxE`](https://www.youtube.com/watch?v=bPGnvfyMuxE)).

RAG interview guides repeatedly score: requirements clarification, ACL-before-rank, latency budget allocation, eval gate, guardrails—**without being prompted** (e.g. [technoscripts RAG layers](https://technoscripts.com/python-rag-system-design/); [sde2ai RAG rubric](https://sde2ai.com/practice/rag)).

### Failure demos that increase trust

| Failure demo | What it proves | Narration cue |
|--------------|----------------|---------------|
| **Abstain / corpus miss** | Refusal policy | “No grounded source — I will not invent” |
| **Bad retrieval labeled** | Observability | “Top chunk is off-topic; we fall back / ask clarify” |
| **Tool timeout / schema error** | Integration maturity (Week 21) | Structured `TOOL_TIMEOUT`; no blind POST retry |
| **ACL deny** | Enterprise readiness | Empty retrieval for other-tenant doc; no leak in prompt |

Do not demo a raw crash. Demo **controlled** degradation with a sentence on the fix already shipped from the taxonomy (file [02](02-eval-log-driven-bug-fixes.md)).

### STAR bridge (one story from a real fix)

Extract one story before the interview:

- **Situation:** golden-set / trace showed failure mode X at rate Y.  
- **Task:** make demo-safe before freeze date.  
- **Action:** layer fix (e.g. tenant filter before rank) + regression case.  
- **Result:** rate Y → Y′; still deferred Z with reason.

That single story answers “how do you know it works?” better than a model-name drop.

---

## Alternatives & Tradeoffs

| Narrative style | Pros | Cons |
| --- | --- | --- |
| **Architecture-first** (boxes then demo) | Signals systems maturity | Can bore; delay user value |
| **User-journey-first** (show chat, reverse-engineer) | Sticky | Looks like a wrapper unless you open the hood |
| **Eval-first** (show failing cases → fix) | Extremely strong for Applied AI | Needs prepared traces; risk of looking broken if mishandled |
| **Slide-only** | Safe when live infra flakes | Weak for FDE loops that expect shipping instincts |
| **Hybrid 5-min** (stakes → arch → live success+fail → metrics) | Best dual-track default | Requires rehearsal; timing discipline |

---

## Necessity

Without narrative structure, interviewers fill gaps with worst assumptions (prompt-only toy, no evals, no production thinking). With structure, the same codebase reads as an AI Engineer / FDE artifact.

Without a rehearsed failure path, the first unexpected abstain looks like incompetence instead of policy. Without metrics—even approximate—cost/latency probes become hand-waving.

Huyen: production success is systems iteration under uncertainty, not demo-day vibes ([MLSys](https://www.youtube.com/watch?v=c_AUuTuPA5k); [GenAI platform](https://huyenchip.com/2024/07/25/genai-platform.html)).

---

## Industry Practice

| Bar | Practice |
|-----|----------|
| **Common** | Feature tour of chat UI; hope the model behaves; no backup recording |
| **Strong** | Timed script; success + refusal; diagram matches code; metrics slide with quality + latency + cost proxy |
| **Senior / FDE-shaped** | Opens with customer stakes and constraints; shows integration seam; narrates a real eval-driven fix; non-goals are explicit; ready for values/safety probes on “just ship it” |

Public candidate reports of OpenAI/Anthropic-style loops emphasize production-shaped system design and project deep-dives more than URL-shortener classics; Anthropic values rounds punish careless “just ship it” stories. OpenAI FDE postings emphasize owning end-to-end customer deployment ([OpenAI FDE](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/)).

---

## Concrete Scenario (URL)

**Eight-layer RAG interview framing** (corpus, ingest, retrieval, generation, evals, observability, cost, guardrails) with explicit hire signals: https://technoscripts.com/python-rag-system-design/

**Chip Huyen systems + interview corpus:**

- https://huyenchip.com/machine-learning-systems-design/toc.html  
- https://github.com/chiphuyen/machine-learning-systems-design  
- https://huyenchip.com/ml-interviews-book/  
- https://github.com/chiphuyen/ml-interviews-book  
- YouTube ML interviews: https://www.youtube.com/watch?v=pli1K75PSa8  
- YouTube MLSys: https://www.youtube.com/watch?v=c_AUuTuPA5k  

**Composed product demo metaphor:** Palantir Developer Deskside walkthrough — https://www.youtube.com/watch?v=bPGnvfyMuxE  

**Eval-backed confidence in narrative:** Hamel/Shreya on why looking at errors precedes metrics — https://www.youtube.com/watch?v=BsWxPI9UM4c  

---

## Open Questions

- Should capstone demos default to recorded backup + live primary, or live-only to signal ops confidence?  
- How explicit should cost numbers be when they are estimates?  
- For FDE interviews, how much customer-stakeholder fiction is acceptable in a personal project demo?  
- Is an eval-first opening (show a fixed failure) too risky for a first impression?

---

## Sources

- Chip Huyen, ML Systems Design: https://huyenchip.com/machine-learning-systems-design/toc.html  
- Chip Huyen, ML Interviews Book: https://huyenchip.com/ml-interviews-book/  
- Chip Huyen, GenAI platform: https://huyenchip.com/2024/07/25/genai-platform.html  
- Chip Huyen, ML Interviews (YouTube): https://www.youtube.com/watch?v=pli1K75PSa8  
- Chip Huyen, Stanford MLSys (YouTube): https://www.youtube.com/watch?v=c_AUuTuPA5k  
- Chip Huyen, Databricks ML systems design (YouTube): https://www.youtube.com/watch?v=g08qBcdk3Ss  
- RAG system design interview layers: https://technoscripts.com/python-rag-system-design/  
- SDE→AI RAG practice rubric: https://sde2ai.com/practice/rag  
- Palantir FDSE day-in-life: https://blog.palantir.com/a-day-in-the-life-of-a-palantir-forward-deployed-software-engineer-45ef2de257b1  
- Palantir Developer Deskside (YouTube): https://www.youtube.com/watch?v=bPGnvfyMuxE  
- OpenAI FDE role framing: https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/  
- Hamel Husain, Your AI Product Needs Evals: https://hamel.dev/blog/posts/evals/  
- Hamel / Shreya, Lenny’s Podcast (YouTube): https://www.youtube.com/watch?v=BsWxPI9UM4c  
