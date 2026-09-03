# 02 — Trajectory evaluation vs outcome evaluation

> Week 15 — Path vs environment state; pass@k vs pass^k  
> Research notes (raw).

---

## Fundamentals

Anthropic definitions ([Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)):

- **Transcript / trajectory** — full interaction record (tools, reasoning, messages).  
- **Outcome** — final **environment state** after the trial (e.g. whether a reservation **exists in SQL**), independent of the agent’s closing sentence.

A flight-booking agent can say “Your flight has been booked” while the outcome is **no row**. That trial **failed**, regardless of fluent text. Conversely, Opus 4.5 on a **τ²-bench** flight task found a **policy loophole**: it “failed” the eval as written but produced a **better** user solution. That is the opposite failure mode: **graders too path- or policy-literal**.

**Outcome evaluation:** Did the user goal / business state get achieved? Black-box success rule (exact answer, correct side effect, tests pass). Hamel **phase 1**: end-to-end task success first, with a **precise success rule** per task (human or **validated** LLM judge). Record the **first upstream failure** during error analysis.

**Trajectory evaluation:** Did the **path** matter? Steps, order, tool choice, loops, efficiency, policy adherence. Langfuse: **path ≠ destination**; dimensions fail independently (wasteful path can complete the task; clean path can miss the goal).

| Lens | Catches | Misses |
|------|---------|--------|
| Outcome-only | Wrong final state, failed bookings, wrong answers, “said done / didn’t write” | Unsafe intermediate calls, inefficiency, policy skips that got lucky |
| Trajectory-only | Wrong tools/order, loops, scope creep, skipped verify | Valid alternate paths; may fail creative successes (Anthropic rigidity warning) |
| Combined | Safety + success + efficiency | Higher harness cost |

Hamel on **complex multi-step** workflows: use **both** outcome metrics (was the business case complete / accurate / formatted?) and **process** metrics (step count, time, resources). Process failures are often more deterministic — debug them first. Segment error analysis by **workflow stage** (early understanding vs mid processing vs late format); early errors **cascade** ([multi-step FAQ](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html)).

**Partial credit / checkpoints.** Anthropic: a support agent that identifies the problem and verifies identity but fails the refund is **better** than one that fails immediately — represent the continuum. Hamel **goal checkpoints** on long workflows. LangSmith `superset` is a coarse checkpoint (“at least these tools”).

**Transition failure matrices** (Hamel / Bischof): rows = last successful state, columns = first failure. Example: GenSQL → ExecSQL = 12 failures vs DecideTool → PlanCal = 2 — investigate the hotspot. Bischof *Failure is a Funnel* (Data Council 2025) applies **product-analytics drop-off** thinking to agent stages; Hamel embeds the matrices in the agentic-workflow FAQ. Companion lesson: *Stop Managing AI Projects Like Traditional Software* (Hamel + Bischof, [Maven](https://maven.com/p/9b1bab/stop-managing-ai-projects-like-traditional-software)) — capability funnel + experiments, not a feature roadmap.

### Non-determinism: pass@k vs pass^k

Agent behavior varies across trials. Anthropic + τ-bench culture:

| Metric | Meaning | As k grows | Use when |
|--------|---------|------------|----------|
| **pass@k** | P(at least one success in k trials) | **Rises** | Coding with a verifier; best-of-n is deployable |
| **pass^k** (“pass-hat-k”) | P(**all** k trials succeed) | **Falls** | Customer-facing agents; user gets one shot |

At k=1 they coincide. At large k they tell opposite stories (pass@k → 1, pass^k → 0). τ-bench (Yao et al., 2024): even strong function-calling agents succeeded on **&lt;50%** of tasks; **pass^8 &lt; 25%** in retail — inconsistency, not just capability ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)). If per-trial p = 0.75, pass^3 ≈ 0.42. Anthropic: a 75% per-trial agent is **not** “75% reliable in production” if users cannot retry.

**Capability vs regression suites** (Anthropic): capability starts at **low** pass rate (hill to climb); regression near **100%**. Graduate saturated capability tasks into regression. An eval at 100% tracks regressions but gives **no improvement signal** (SWE-bench Verified: ~30% → **&gt;80%** saturation warning).

### How public benchmarks sit on this split

| Benchmark | Primary signal | Trajectory? |
|-----------|----------------|-------------|
| **SWE-bench Verified / Terminal-Bench** | **Outcome** via tests / environment scripts | Optional transcript heuristics |
| **τ-bench / τ²-bench** | Final answer **and** **DB state** vs annotated goal; user simulator | Transcript **not** the grade (paper: compare DB to goal state so conversations may vary) |
| **WebArena** | **Functional correctness**: URL/page **and backend** (order actually placed, repo contents) | Explicitly **not** action-sequence match — many valid paths |
| **AgentBench** | Interactive success across 8 envs (often SR / F1 / reward) | Process varies by env |
| **LangSmith trajectory match** | Process-centric vs a reference | Pair with a **separate** outcome grader |
| **OSWorld / BrowseComp** (Anthropic) | Artifact/OS scripts; verifiable web needles | Outcome-heavy |

WebArena authors: comparing **surface-form action sequences** is unreliable; functional validators allow **alternative valid paths** ([arXiv:2307.13854](https://arxiv.org/abs/2307.13854)). That is Anthropic’s “grade what was produced” in a web setting. τ-bench is the **support-agent** version of the same idea (DB as outcome) **plus** policy documents the agent must follow.

---

## Alternatives & Tradeoffs

| Strategy | Tradeoff |
|----------|----------|
| Grade outcomes only (Anthropic often prefers for **open** tasks) | Avoids brittle path tests; may allow policy-violating paths |
| Strict trajectory gold paths | Good for **regulated** workflows; brittle; τ² loophole risk |
| Soft trajectory (unordered / subset / superset / Vertex precision-recall) | Less flake; can miss order bugs |
| Partial credit / checkpoints | Better signal on long tasks; more grader design |
| Transition matrices | Diagnoses *where* without one gold path; needs a state machine you believe |
| LLM judge on trajectory without reference | Scalable nuance; calibration burden (Hamel) |
| pass@k only | Looks like improvement when you sample more; hides unreliability |
| pass^k only | Harsh; expensive (k trials × tasks) |

Hamel recommended **order**: E2E success **first** → step-level diagnostics on **failing** workflows. Do not drown in step metrics while the agent never books the flight.

Scoring combinations (Anthropic): **weighted** (combined scores hit a threshold), **binary** (all graders pass), or **hybrid**.

---

## Necessity

**Outcome-only** → ship agents that refund without verifying identity if the DB sometimes “looks right,” or that take 40 steps and blow cost budgets (Langfuse: completion with a wasteful trajectory). Week 14 audit/idempotency cannot be proven from chat text.

**Trajectory-only** → reject agents that solve the user’s problem via a better unforeseen sequence (Anthropic τ² example; WebArena’s reason for functional graders). CORE-Bench / METR anecdotes in the Anthropic post: **brittle graders** penalized valid formats (`96.12` vs full float) or **followed the written threshold** while the grader required exceeding it — scores moved from 42% → 95% after harness/grader fixes. **Always read transcripts** (Step 6).

Without **both**, FDE interviews cannot answer: “How do you know the agent didn’t skip KYC?” and “How do you avoid punishing a better tool sequence?”

---

## Industry Practice

- **Common:** single “accuracy” on final text; one trial per task; no isolation between trials (shared files/cache — Anthropic: Claude cheated by reading **git history of previous trials**).  
- **Strong:** explicit split scores (`task_success`, `state_check`, `trajectory_*`, `tool_args_*`, cost/turns); **isolated** environments per trial; offline CI + online judges (Langfuse); capability vs regression; balanced **should-fire / should-not-fire** sets; Swiss-cheese (evals + prod monitoring + A/B + transcript review + human studies).  
- **FDE bar:** same refund task with **disagreement** between graders as a demo; pass^k discussed for the write agent; public benchmarks as **literacy**; **private** domain suite as the ship gate (academic scores ≠ cost, safety, maintainability).

Bolt: static analysis + **browser agents** testing the **app outcome** + LLM judges for instruction following. Descript: three outcome-ish dimensions of an editing workflow. Coding agents: SWE-bench-style **fail-to-pass without regressions**, plus optional transcript rubrics for tool/user behavior.

---

## Concrete Scenario

**Anthropic flight booking** — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

Transcript says booked; **outcome** is SQL reservation existence; graders on **state + tools + rubric**. Partial credit if identity verified but refund missing.

**τ-bench** — https://github.com/sierra-research/tau-bench — https://arxiv.org/abs/2406.12045  

User LM + agent + APIs + **policy markdown**. Reward from **DB vs annotated goal**. pass^k for reliability. Retail pass^8 &lt; 25% for gpt-4o-era FC agents.

**WebArena** — https://webarena.dev/ — https://arxiv.org/abs/2307.13854  

812 tasks; `evaluator_router` scores functional correctness (page + **backend**). GPT-4 ~14.4% vs human ~78%. Reset Docker env between evals so trials are isolated.

**Hamel E2E then steps** — https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  

Berkeley homes example: checkpoints independent. Transition matrix → where to invest.

**YouTube:** Hamel *How to Automate AI Evals (Correctly)* — https://www.youtube.com/watch?v=tqUDjc1HzO4 — analyze / measure / improve; do not ask a model to “do evals” as one glob. *Why AI evals are the hottest new skill* — https://www.youtube.com/watch?v=BsWxPI9UM4c — code-based vs LLM judge; start from **actual errors**.

---

## Open Questions

- When should a creative trajectory that **violates written policy** but helps the user count as pass? (eval hacking vs user value vs policy update)  
- How to **weight** partial credit on long-horizon tasks?  
- Contamination and saturation (SWE-bench &gt;80%) — when do public benchmarks stop guiding **product** work?  
- pass^k sample size: how many trials before the reliability curve is stable?  
- Dual-control τ² (user also has tools) — how to attribute outcome failures to **agent vs user-sim**?

---

## Sources

- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://github.com/sierra-research/tau-bench  
- https://arxiv.org/abs/2406.12045  
- https://github.com/sierra-research/tau2-bench  
- https://arxiv.org/abs/2506.07982  
- https://webarena.dev/  
- https://arxiv.org/abs/2307.13854  
- https://github.com/THUDM/AgentBench  
- https://maven.com/p/9b1bab/stop-managing-ai-projects-like-traditional-software  
- https://www.youtube.com/watch?v=tqUDjc1HzO4  
- https://www.youtube.com/watch?v=BsWxPI9UM4c  
