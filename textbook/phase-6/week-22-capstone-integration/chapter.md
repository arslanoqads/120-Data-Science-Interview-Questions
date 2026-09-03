# Chapter 22 — Capstone integration

> **Phase 6 — Capstone and Interview Readiness**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-6/week-22-capstone-integration/`  
> **Syllabus Build:** Syllabus says “concepts: none new.” Treat that as **meta-work**: you already have Weeks 6–21 systems. This week you **stop building sideways** and make one vertical slice demo-safe. (1) **Freeze scope in writing.** One primary user job, one corpus + tool set, success metrics, and an explicit non-goals list. Walk Chip Huyen’s GenAI platform stack end-to-end for that slice: model API → guardrails → context (RAG/tools) → cache/route → logging/evals. (2) **Triage eval logs into a bug queue.** Sample 20–50 (then ~100) traces; open-code; axial-code a taxonomy with counts; rank **frequency × severity × leverage**; fix top classes; promote fixed failures into regression evals. (3) **Script a 5-minute walkthrough.** User stakes → requirements freeze → request + offline paths → live success with citations → intentional refusal/tool failure → metrics/tradeoffs → roadmap as non-goals. Record a backup; keep the live path primary. (4) **Ship the polish gates.** Happy path on a clean machine / deploy URL; golden-set command in README; architecture diagram that matches code; one STAR story from a real taxonomy fix.

---

## Chapter framing

Weeks 6–21 already shipped ingestion, retrieval, agents, evals, deploy, auth, cost, and messy integration. Week 22 adds **no new subsystem**. Capstone AI products fail less from missing models and more from **unbounded surface area**: extra tools, extra agents, extra UIs, extra corpora that never get hardened.

Three coupled deliverables:

1. **Scope freeze** — written contract for the demoable product.  
2. **Eval → fix queue** — taxonomy with counts; top bugs fixed or explicitly deferred.  
3. **Demo narrative** — claim → architecture → evidence → failure → next bet.

**Do not start Week 23 (system-design interview drills) from this chapter** — this week **freezes scope**, turns **eval logs into a prioritized bug queue**, and ships a **demo narrative** interviewers trust. New model capabilities are not the goal; integration polish is. STAR case-study packs and resume language belong in Week 24.

**End-to-end polish path**

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

**Default path (synthesis)**

1. **Freeze before you polish.** Unbounded surface area kills demos.  
2. **Compose what you built** (RAG + eval harness + one agent path); refuse greenfield side quests in the last stretch (FDSE: many capabilities for one customer by composing the platform).  
3. **Eval logs are a work queue**, not a vanity dashboard.  
4. **Fix ordinary bugs immediately** (chunk metadata, tool schema, prompt contradiction); reserve judges for subjective residuals (Weeks 16–17).  
5. **Demo narrative = claim → architecture → evidence → failure → next bet.**  
6. **Control under failure beats peak vibes.** Interviewers trust abstain + tool-error demos more than another model swap.

Interview artifact = **written demo contract** + **taxonomy table with top-5 fixes** + **5-min script (success + failure)** + **metrics line** (quality / p95 / $/1k).

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) after Weeks 18–21 — now frozen to one vertical slice, triaged against eval logs, and demo-ready.

---

### Systems integration / freezing scope for demoable AI products

* **Fundamentals:**  
  **Freezing scope** means deliberately locking (1) **user job**, (2) **corpus / tools in scope**, (3) **success metrics**, and (4) **known non-goals** so remaining engineering time goes to integration reliability—auth, ingestion freshness, retrieval quality, latency budget, fallbacks, and observability.

  Lock four fields before touching prompts or models:

  | Freeze field | Example for a dual-track capstone |
  |--------------|-----------------------------------|
  | **User job** | “Support analyst answers policy questions with citations from the internal KB + one SQL tool” |
  | **Corpus / tools in scope** | Frozen PDF/HTML dump + `get_invoice(id)`; no web browse; no second agent |
  | **Success metrics** | Citation faithfulness on golden set ≥ X; recall@5 ≥ Y; p95 &lt; Z ms; $/1k queries logged |
  | **Known non-goals** | Multi-tenant admin UI, fine-tune, multi-agent debate, billing, mobile |

  Chip Huyen’s GenAI platform framing is the **integration checklist**, not a feature wishlist. Production GenAI stacks grow **progressively**:

  1. Query → model API → response (simplest).  
  2. **Enhance context** — external data / tools (RAG, retrieval, function calls).  
  3. **Guardrails** — input/output safety, policy.  
  4. **Router / gateway** — multi-model, security, complex pipelines.  
  5. **Cache** — latency and cost.  
  6. **Complex logic / write actions** — agents, side effects.  
  7. **Observability** — logging, tracing, evals.

  Capstone polish is **not** implementing every box from scratch in Week 22. It is walking the stack you already built for **one vertical slice** until each hop is demo-safe under adversarial questions. Huyen’s earlier production punchline still applies: easy to make something cool; hard to make something production-ready. Add components only when **failure modes demand them**. Choosing “no RAG” or “hybrid RAG” is a scope decision: Anthropic notes that long-context + prompt caching can cover a small KB (on the order of ≤~200k tokens); beyond that, retrieval *is* the product.

  Palantir’s public FDSE piece is the product metaphor: a Forward Deployed Software Engineer enables **many capabilities for one customer** by configuring/composing an existing platform, not inventing a new platform per engagement. Contrast with a “Dev” who builds one capability for many customers.

  | FDSE instinct | Capstone move |
  |---------------|---------------|
  | Compose platform features | Compose your Weeks 6–21 modules (ingest, retrieve, agent, eval, deploy, auth) |
  | Operational in days | Demo contract + hardened happy path, not a new architecture |
  | Focus is the hard skill | Written non-goals; kill side quests |
  | Technical challenges listed | Pipelines, ACL, workflow UX, outage investigation — not “another model” |

  Strong teams freeze more than a model ID. A written **demo contract** contains:

  1. **Happy-path script** (exact query, expected citation / tool).  
  2. **Three failure demos** — abstain (corpus miss), bad retrieval recovered or labeled, tool error / timeout with structured message.  
  3. **Rollback plan** — pin model + prompt version; known-good index snapshot.  
  4. **Out-of-scope slide** — one line each for agent loop v2, multi-tenant, fine-tune.  
  5. **Clean-machine / deploy URL check** — someone else can run README steps.

  OpenAI and Anthropic public FDE postings describe the job as discovery → scoping → system design → build → production rollout **inside customer systems**. Scope is transformational adoption and reliability, not feature count.

  Freeze does **not** mean stop iterating. Huyen’s ML systems design teaching frames projects as iterative: project setup → data → modeling → serving → business feedback. Freeze means iterate **inside** a locked user job and corpus so evals remain valid.

* **The Alternatives:**  

  | Scope strategy | What you gain | What you lose / risk |
  |----------------|---------------|----------------------|
  | **Vertical slice freeze** (one persona, one workflow, one corpus) | Demo coherence; measurable eval set; clear architecture story | Looks “small” unless metrics + failure narrative are strong |
  | **Horizontal feature sprawl** (chat + agents + multi-tenant + dashboard) | Impressive slideware | Brittle live demo; interviewer probes any weak surface |
  | **Platform-first** (generic “AI OS”) | Resume keywords | No believable user outcome; hard to STAR later |
  | **Customer-shaped cut** (freeze around one messy integration: SQL + docs + ACL) | FDE-signal authenticity | Higher integration cost; must timebox ruthlessly |
  | **Long-context only** (no RAG) | Simpler ops for small KB | Cost/latency walls; loses retrieval as a product story |
  | **Agent-default** (loops on every query) | Looks advanced | Latency, cost, nondeterminism; agentic RAG is not the default path |
  | **Model-swap week** | Easy to narrate | Usually wrong layer; fix bugs found in analysis first |
  | **Recorded-only demo** | Safe when infra flakes | Weak for FDE loops that expect shipping instincts |
  | **Live-only, no backup** | Ops confidence signal | Single flake can tank the round |

  Tradeoff rule of thumb for demos: **latency and refusal behavior beat** another model swap. Long-context-only vs RAG is itself a scope decision. The syllabus selects **vertical-slice freeze + compose existing modules** because Week 22’s build is polish on a demoable contract, not a new architecture.

* **Failure Modes:**  
  - Eval logs never stabilize — corpus/tool changes invalidate the golden set.  
  - Demo narrative fragments (“and also we have an agent that…”) invite probes into unfinished surfaces.  
  - Integration bugs (partial ETL, stale index, ACL leaks) surface live because they were deferred as “infra.”  
  - Focus collapses — near-infinite problems; without written non-goals, Week 22 becomes an accidental Weeks 11–15 rewrite.  
  - Horizontal sprawl makes every surface an attack surface in a live demo.  
  - Skipping the clean-machine / deploy URL check means the happy path only works on the author’s laptop.

* **Average vs. Strong Engineer:**  
  **Average:** freeze UI copy and model ID; keep hacking prompts until the day before; README promises multi-agent + multi-tenant “soon.”  
  **Strong:** written demo contract; pinned prompt/model/index versions; success + three failure demos rehearsed; architecture diagram matches code.  
  **Senior / FDE-shaped:** freeze around the **integration seam** (legacy DB + document store + identity) because that matches OpenAI/Anthropic FDE postings: ship in customer environments with evals, guardrails, and production rollout. Interviewers look for structured thinking across the ML lifecycle, not a single “correct” architecture — a frozen slice with honest tradeoffs beats an unbounded architecture diagram.

* **Worked Example:**  
  Deployment Copilot after Week 21 can touch messy SQL, docs RAG, and a write path. For Week 22 you freeze:

  | Field | Locked choice |
  |-------|---------------|
  | User job | Support analyst answers deployment-policy questions with citations + `get_invoice(id)` |
  | Corpus / tools | Frozen internal KB dump + one parameterized invoice tool; no web browse; no second agent |
  | Success metrics | Faithfulness on golden set; recall@5; p95 latency; $/1k queries logged |
  | Non-goals | Multi-tenant admin UI, fine-tune, multi-agent debate, billing, mobile |

  You walk Huyen’s stack for that slice only: model API → context (RAG + `get_invoice`) → guardrails (refusal on corpus miss) → cache/route if already present → logging/evals. You do **not** add agent-loop v2. The Palantir FDSE COVID-response pattern is the metaphor: solutions operational under time pressure; listed challenges are pipelines, ACL, workflow UX, and outage investigation — not “swap the model.” Public Foundry deskside demos show the same composition story visually: ingest → ontology/workflow → interactive action in one sitting.

* **Apply It:**  
  1. Write the four freeze fields (user job, corpus/tools, success metrics, non-goals) before any prompt or model change.  
  2. Map Deployment Copilot’s existing modules onto Huyen’s progressive stack; mark each hop demo-safe or out of slice.  
  3. Draft the demo contract: happy-path query, three failure demos, rollback pins (model/prompt/index), out-of-scope lines.  
  4. Verify clean-machine or deploy-URL README steps succeed for someone other than you.  
  5. Kill side quests that are not the frozen user job; put them on the non-goals slide.  
  6. Decide RAG vs long-context-only as an explicit scope choice for *this* corpus size—not a resume checkbox.

---

### Eval-log-driven bug fixes (taxonomy → frequency × severity × leverage)

* **Fundamentals:**  
  Eval logs are not a dashboard vanity metric; they are a **work queue**. Hamel Husain’s error-analysis loop is the meta-skill for the polish week:

  1. **Sample traces** — start ~20–50 after significant changes; working pool often ~100 diverse; prefer noting the **first** failure in a trace (upstream cascades).  
  2. **Open-ended notes (“journaling”)** by a domain-aware reviewer (benevolent dictator).  
  3. **Axial coding** → **failure taxonomy** with counts.  
  4. **Write evals for observed modes** — code assertions vs LLM-judge (only for subjective residuals).  
  5. **Fix highest-frequency / highest-severity classes first**; regenerate/expand golden set; repeat.

  Priority is usually **frequency × user severity × fix leverage**, not “average score went up 2%.” Many issues found in error analysis are ordinary bugs (bad chunk metadata, wrong tool schema, prompt contradiction)—**fix immediately**; only persistent subjective failures need judge infrastructure (Weeks 16–17). Hamel consulting heuristic: **60–80%** of eval time looking at data. Binary **pass/fail + critique text** often beats 1–5 Likert for iteration speed. A ~70% pass rate on a stressful set can be healthier than 100% on easy vibes.

  Capstone top-5 failure classes that dominate RAG/agent products after Weeks 9–17 taxonomies (reuse unless *your* counts disagree):

  | Rank | Failure class | Typical root cause | Fix leverage | Demo impact if unfixed |
  |------|---------------|--------------------|--------------|------------------------|
  | **1** | **Wrong / empty retrieval** | Bad chunk metadata, filter bugs, stale index, hybrid weight off | High — ordinary engineering | Happy path cites irrelevant docs; interviewer stops trusting the stack |
  | **2** | **Ungrounded / fake citations** | Generator invents quotes; citation mapper off-by-one; no faithfulness check | High — assert + prompt + post-check | Looks like a wrapper that lies under pressure |
  | **3** | **Tool schema / selection bugs** | Wrong args, missing required fields, retries of non-idempotent writes | High — schema + validation | Live tool path flakes; duplicate side effects (Week 21) |
  | **4** | **Refusal / abstain failures** | Answers when corpus miss; or over-refuses easy questions | Medium — prompt + retrieval threshold + eval cases | Cannot demo control; either hallucinates or looks broken |
  | **5** | **ACL / tenancy / PII leak** | Filter applied after rank; prompt injects other-tenant context | Severity-max even if rare | Catastrophic in FDE / enterprise loops; deferring is not optional |

  **How to use the table:** open-code 20–50 traces; axial-code into *your* names (`invoice_tool_arg_missing`, not generic `hallucination`); count; map into these five buckets if they fit; fix 1→3 immediately; treat #5 as severity override; write ≥1 regression case per fixed mode. People get lost jumping straight into writing tests — ground yourself in **actual errors** first. Build a low-friction viewer; free-form notes; do not categorize too early. The highest-ROI investment is often a **simple domain-specific data viewer**, not a fancier dashboard.

  Convert each high-count category into an engineering ticket with:

  - **Repro trace ID** (or golden query).  
  - **Layer hypothesis** — retrieval / prompt / tool / auth / index freshness (Huyen platform layers help you avoid “swap the LLM” as default).  
  - **Fix type** — code bug vs prompt vs data vs eval-only monitor.  
  - **Regression artifact** — one automated check before merge.  
  - **Demo note** — whether this mode is shown live as a *controlled* failure or must be green on happy path.

  Chip Huyen treats **observability** (logging, monitoring, eval hooks) as a first-class GenAI platform component — without it you cannot see which layer failed. If traces are incomplete (no retrieval set, no tool args, no final citations), fix instrumentation **before** another prompt pass. Anthropic’s public FDE posting lists **evaluation frameworks** alongside prompt engineering, agents, and production deployment as required production LLM experience.

* **The Alternatives:**  

  | Prioritization heuristic | Strength | Weakness |
  |--------------------------|----------|----------|
  | **Count-ranked taxonomy** | Forces focus; demos “data-driven iteration” | Can undervalue rare catastrophic failures (ACL leak, unsafe action) |
  | **Severity / blast-radius first** | Matches production / FDE instincts | Needs explicit severity rubric or you thrash |
  | **frequency × severity × leverage** | Balances product + engineering reality | Requires honest leverage estimates |
  | **Metric chasing** (generic coherence/fluency) | Easy tooling | Misaligned with product; Hamel warns against platform default metrics |
  | **Only automated judges** | Scales | Without human error analysis, you optimize the wrong thing |
  | **Only vibe checks** | Fast early | No regression gate; demo flips flop |
  | **Eval-driven development of imagined failures** | Feels proactive | Hamel: generally **no** — unbounded failure surface; write evals for discovered errors |

  The syllabus selects **frequency × severity × leverage** with severity override for ACL/safety, and **binary pass/fail + critique** for iteration speed.

* **Failure Modes:**  
  - Skipping error analysis → writing generic evals → “improving” the wrong layer (swap LLM when retrieval recall is the bug).  
  - Capstone without a prioritized fix list looks like random prompt thrash in demos and interviews.  
  - Without promoting fixes into regression tests: the same failure returns the night before the demo.  
  - Without severity weighting: you polish tone while an ACL footgun remains.  
  - Incomplete traces (no retrieval set, tool args, or citations) make every diagnosis a guess.  
  - Jumping to judges for ordinary bugs wastes polish week on infrastructure that Weeks 16–17 already covered.

* **Average vs. Strong Engineer:**  
  **Average:** Langfuse/Phoenix/Braintrust traces exist; nobody triages them weekly; README cites “evals” without taxonomy.  
  **Strong:** spreadsheet or tagged traces → top-3/5 failure modes on README; each mode ≥1 regression test; CI or scripted `make eval` blocks prompt/retrieval regressions.  
  **FDE / Applied AI signal:** error-analysis cadence after every significant change; production sample feeds the golden set; “evaluation frameworks” language backed by artifacts. Saying “we look at traces weekly and ship taxonomy-driven fixes” is role-shaped language.

* **Worked Example:**  
  Suppose Deployment Copilot yields 40 open-coded traces after freezing the KB + `get_invoice` slice:

  | Category | Count | Severity (1–5) | Leverage | Score (count×sev×lev) | Action |
  |----------|-------|----------------|----------|------------------------|--------|
  | `chunk_meta_tenant_filter_bug` | 8 | 5 | 3 | 120 | Fix now + ACL golden |
  | `citation_off_by_one` | 10 | 4 | 3 | 120 | Fix now + faithfulness assert |
  | `tool_missing_invoice_id` | 7 | 4 | 3 | 84 | Schema validation |
  | `answers_on_corpus_miss` | 6 | 4 | 2 | 48 | Refusal prompt + goldens |
  | `tone_too_verbose` | 9 | 2 | 2 | 36 | Defer or light prompt tweak |
  | `judge_disagrees_on_style` | 3 | 2 | 1 | 6 | Monitor; Week 17 judge work |

  Severity overrides pure count: an ACL bug at count=2 still outranks verbose tone at count=15 for enterprise/FDE demos. You fix ranks 1–3 immediately (metadata filter before rank, citation aligner + faithfulness assert, JSON schema on `get_invoice`), add ≥1 golden per fixed mode, and keep `tone_too_verbose` deferred. Field Guide pattern: bottom-up coding finds a few issues covering most failures; targeted tests move a stubborn mode from low success (~33%) to high (~95%) — not a generic hallucination dashboard.

* **Apply It:**  
  1. Sample 20–50 traces (aim ~100 diverse working pool); open-code with free-form notes before categorizing.  
  2. Axial-code into named categories with counts; map into the top-5 capstone buckets where they fit.  
  3. Rank by frequency × severity × leverage; apply severity override for ACL / PII / unsafe actions.  
  4. Fix ordinary bugs (metadata, schema, prompt contradiction) before building new judges.  
  5. Promote each fixed mode into a golden / CI eval command documented in README.  
  6. If traces lack retrieval sets, tool args, or citations, fix instrumentation before another prompt pass.  
  7. Put the top-3/5 failure modes and fix status on the README as the interview-facing taxonomy table.

---

### Technical demo narrative (claim → architecture → evidence → failure → next bet)

* **Fundamentals:**  
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

  Five-minute hybrid timing for dual-track (AI Engineer / FDE) prep:

  | Clock | Beat | Anti-pattern |
  |-------|------|--------------|
  | 0:00–0:45 | User stakes | Starting in a boxes diagram |
  | 0:45–1:15 | Requirements freeze | Skipping latency/ACL/refusal |
  | 1:15–2:30 | Architecture (online + offline) | Vapor boxes not in code |
  | 2:30–3:30 | Live success + citations/trace | Chat-only with no hood open |
  | 3:30–4:30 | Live refusal or tool failure | Hiding failures; apologizing without structure |
  | 4:30–5:00 | Metrics, tradeoffs, non-goals | Feature roadmap dump |

  Interviewers trust demos that show **control under failure**, not peak vibes. Recorded backup + live primary is the practical default for take-homes that require a video walkthrough; live-only can signal ops confidence but needs a rollback story.

  During the success path, **open the hood** — show at least one of:

  - Retrieved chunks with scores / filters.  
  - Citation highlights aligned to answer spans.  
  - Tool call JSON (name, args, structured error on failure path).  
  - Eval command or golden-set row that covers this query class.

  Hamel’s product-eval ethos applies to demos: you should be able to debug quickly because traces, assertions, and navigation exist. A demo that cannot show a trace when asked “where did that citation come from?” fails the trust test. Architecture diagrams must match actual code paths — no vapor boxes.

  Failure demos that increase trust:

  | Failure demo | What it proves | Narration cue |
  |--------------|----------------|---------------|
  | **Abstain / corpus miss** | Refusal policy | “No grounded source — I will not invent” |
  | **Bad retrieval labeled** | Observability | “Top chunk is off-topic; we fall back / ask clarify” |
  | **Tool timeout / schema error** | Integration maturity (Week 21) | Structured `TOOL_TIMEOUT`; no blind POST retry |
  | **ACL deny** | Enterprise readiness | Empty retrieval for other-tenant doc; no leak in prompt |

  Do not demo a raw crash. Demo **controlled** degradation with a sentence on the fix already shipped from the taxonomy.

  Extract one **STAR** story from a real fix before the interview:

  - **Situation:** golden-set / trace showed failure mode X at rate Y.  
  - **Task:** make demo-safe before freeze date.  
  - **Action:** layer fix (e.g. tenant filter before rank) + regression case.  
  - **Result:** rate Y → Y′; still deferred Z with reason.

  That single story answers “how do you know it works?” better than a model-name drop. FDE loops weight **customer scenario / ambiguity handling** alongside coding — include a discovery → constraint → ship moment. RAG interview guides repeatedly score requirements clarification, ACL-before-rank, latency budget allocation, eval gate, and guardrails **without being prompted**.

* **The Alternatives:**  

  | Narrative style | Pros | Cons |
  |-----------------|------|------|
  | **Architecture-first** (boxes then demo) | Signals systems maturity | Can bore; delay user value |
  | **User-journey-first** (show chat, reverse-engineer) | Sticky | Looks like a wrapper unless you open the hood |
  | **Eval-first** (show failing cases → fix) | Extremely strong for Applied AI | Needs prepared traces; risk of looking broken if mishandled |
  | **Slide-only** | Safe when live infra flakes | Weak for FDE loops that expect shipping instincts |
  | **Hybrid 5-min** (stakes → arch → live success+fail → metrics) | Best dual-track default | Requires rehearsal; timing discipline |

  The syllabus selects the **hybrid 5-minute** script: stakes → requirements freeze → architecture → live success + failure → metrics/tradeoffs/non-goals.

* **Failure Modes:**  
  - Without narrative structure, interviewers fill gaps with worst assumptions (prompt-only toy, no evals, no production thinking).  
  - Without a rehearsed failure path, the first unexpected abstain looks like incompetence instead of policy.  
  - Without metrics—even approximate—cost/latency probes become hand-waving.  
  - Vapor boxes on the architecture diagram that are not in code destroy trust when probed.  
  - Chat-only success with no hood open reads as a wrapper.  
  - Feature-roadmap dump in the last 30 seconds crowds out tradeoffs and non-goals.  
  - Raw crash demos (vs controlled degradation) signal immaturity, not honesty.

* **Average vs. Strong Engineer:**  
  **Average:** feature tour of chat UI; hope the model behaves; no backup recording.  
  **Strong:** timed script; success + refusal; diagram matches code; metrics slide with quality + latency + cost proxy.  
  **Senior / FDE-shaped:** opens with customer stakes and constraints; shows integration seam; narrates a real eval-driven fix; non-goals are explicit; ready for values/safety probes on “just ship it.” Public OpenAI FDE framing emphasizes owning end-to-end customer deployment; Anthropic-style values rounds punish careless “just ship it” stories.

* **Worked Example:**  
  Deployment Copilot 5-minute walkthrough after the taxonomy fixes:

  | Segment | Time | What you say / show |
  |---------|------|---------------------|
  | **User & stakes** | 0:00–0:45 | Support analyst; wrong policy cite costs a bad production change |
  | **Requirements freeze** | 0:45–1:15 | Frozen KB + `get_invoice`; p95 budget; refuse on corpus miss; ACL filter-before-rank |
  | **Architecture** | 1:15–2:30 | Online: query → hybrid retrieve → rerank → generate → cite/guardrail; offline: ingest → index → eval gate |
  | **Live success** | 2:30–3:30 | Policy question with visible citations + invoice tool trace JSON |
  | **Live failure** | 3:30–4:30 | Intentional corpus-miss abstain **or** structured `TOOL_TIMEOUT` — no blind retry |
  | **Metrics + tradeoffs** | 4:30–5:00 | Faithfulness / recall@5 / p95 / $/1k; non-goals: multi-agent, admin UI, fine-tune |

  STAR from the real fix: Situation — `citation_off_by_one` at 10/40 traces; Task — demo-safe before freeze; Action — citation aligner + faithfulness assert + golden; Result — mode cleared on golden set, tone verbosity still deferred. Palantir Developer Deskside is the visual metaphor: composed workflow (ingest → ontology → interactive action), not a feature tour.

* **Apply It:**  
  1. Write the timed 5-min script with exact happy-path query and one intentional failure.  
  2. Draw request + offline architecture that matches code paths only — delete vapor boxes.  
  3. Rehearse opening the hood (chunks/scores, citation alignment, tool JSON, or golden-row).  
  4. Record a backup; keep live primary; document rollback (pinned model/prompt/index).  
  5. Prepare one metrics line: quality + p95 latency + $/1k (approximate is fine if labeled).  
  6. Extract one STAR story from a taxonomy fix (rate Y → Y′, deferred Z with reason).  
  7. Keep roadmap items as non-goals unless asked — do not dump them in the last 30 seconds.

---

## Week 22 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Freeze:** Write user job, corpus/tools, success metrics, non-goals; pin model/prompt/index; kill side quests.  
2. **Contract:** Happy-path script + three failure demos + clean-machine / deploy URL check.  
3. **Triage:** Sample 20–50 (then ~100) traces; open-code; axial taxonomy with counts.  
4. **Prioritize & fix:** Rank frequency × severity × leverage; fix top classes (1–3 first; #5 severity override); ordinary bugs before judges.  
5. **Regress:** ≥1 golden / CI eval per fixed mode; README documents the eval command.  
6. **Demo:** 5-min hybrid script — stakes → freeze → arch → success + failure → metrics; diagram matches code.  
7. **Interview artifact:** Demo contract + top-5 taxonomy table + success/failure script + metrics line + one STAR from a real fix.

When those steps are true, Week 22 is done in the syllabus sense: one vertical slice is demo-safe, eval logs became a fix queue, and the walkthrough shows control under failure.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-6/week-22-capstone-integration/` (`00`–`03`, README; source map consulted for URL provenance only).  
- No section required `[NEEDS MORE RESEARCH]` for the three syllabus meta-concepts; research Open Questions (single-tenant vs multi-tenant stub for ACL proof, exact safety/ACL severity weights in a five-minute demo, recorded+live vs live-only default, how to present “fixed 3 of 7 buckets,” when agentic orchestration belongs in the freeze vs roadmap, productization noise for Applied AI vs FDE, absolute vs golden-set-only freeze dates, synthetic expansion safety, before/after vs controlled-failure demo framing, estimate cost-number explicitness, customer-stakeholder fiction in personal demos, eval-first opening risk) remain open and were **not** resolved with invented answers.  
- Outside URLs from research are cited inline where the notes already named them; operational detail was inlined from the notes.  
- Week 23 system-design interview drills and Week 24 resume/portfolio language are explicitly deferred.
