# Week 15 — Agent Evaluation (Traces, Trajectory vs Outcome, Failure Patterns)

> Raw source material for evaluating agentic systems.  
> Legal / public sources only. Not a textbook — research dump with citations for later synthesis.  
> Gathered: 2026-09-03

---

## Concept A — Evaluating agentic traces (tool call correctness, order, arguments)

### 1. Fundamentals

An **agentic trace** (also: transcript, trajectory) is the full record of one trial: model messages, tool calls, tool results, handoffs, guardrails, and intermediate state. OpenAI: a trace captures end-to-end model calls, tool calls, guardrails, and handoffs for one run. Anthropic: the transcript is the complete record; for their API, the full messages array across the eval run.

**Trace grading** asks questions that final-answer grading cannot:

- Did the agent pick the **right tool**?  
- Were **arguments** valid (schema) and **correct** (business IDs, amounts, filters)?  
- Was **order** constrained when policy requires it (e.g. verify identity before refund)?  
- Did a **handoff** occur when it should?  
- Were instructions / safety policies violated mid-trajectory?

**Methods for tool-call checks**

| Method | What it checks | Notes |
|--------|----------------|-------|
| Code / deterministic assertions | Tool name present, arg schema, exact arg values, call counts, step budget | Fast, cheap, reproducible (Anthropic; Langfuse) |
| Trajectory match modes (LangChain `agentevals`) | Compare actual vs reference tool sequence | `strict`, `unordered`, `subset`, `superset` |
| LLM-as-judge on trajectory | Reasonableness, efficiency, appropriateness without rigid path | Needs calibration |
| State / outcome checks | DB or environment after tools ran | Catches “said done, didn’t write” |

**LangSmith / AgentEvals match modes** (official docs):

| Mode | Meaning | Use when |
|------|---------|----------|
| `strict` | Same messages/tool calls in same order | Policy ordering matters |
| `unordered` | Same tools/args, any order | Parallel retrieval |
| `subset` | Agent only uses tools from reference (no extras) | Efficiency / scope control |
| `superset` | Agent includes at least reference tools (extras OK) | Minimum required actions |

Default equality: same tool **and** same arguments (configurable via `tool_args_match_mode` / overrides).

**Langfuse** (2026 guidance): evaluate four dimensions — trajectory, tool use, task completion, multi-turn. Tool calls exposed as structured fields (`name`, `arguments`, …) for code and judge evaluators — do not parse raw text. Offline datasets + online sampled production evaluators.

**OpenAI agent evals workflow:** start with **trace grading** while debugging → graduate to datasets / eval runs for repeatability. (Note: OpenAI Evals *platform* deprecation announced June 2026 — read-only Oct 31 2026, shutdown Nov 30 2026; migration guidance points to Promptfoo for portable configs. Trace grading / agent workflow docs remain relevant as concepts.)

**Vertex AI agent evaluation** (Google): trajectory metrics include `trajectory_exact_match`, `trajectory_in_order_match`, `trajectory_precision`, `trajectory_recall` — useful when evaluating A2A/multi-agent tool sequences.

### 2. Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| Strict trajectory match | Catches policy order bugs | Brittle; punishes valid creative paths (Anthropic warns) |
| Soft match (unordered / subset / superset) | Less brittle | Can miss order-sensitive bugs |
| Args-only schema validation | Cheap safety net | Misses semantic wrong-ID errors |
| LLM judge on tools | Flexible | Non-deterministic; cost; needs human calibration |
| Outcome-only grading | Rewards any valid path | Hides unsafe intermediate tool use |
| Hybrid (Anthropic / Langfuse / Hamel) | Best signal | More harness complexity |

Anthropic explicit guidance: instinct to require exact tool sequences is **often too rigid**; prefer grading **what was produced** (and critical invariants) so creative valid solutions aren’t punished. Still use tool-call graders for **required** safety steps (verify_identity before refund).

### 3. Necessity

Without trace-level tool evaluation:

- Agents pass answer rubrics while calling forbidden tools.  
- Wrong arguments (amount, customer_id) look fine in fluent text.  
- Regressions in routing/handoffs only appear as vague “quality feels worse.”  
- Cost/latency blowups from extra tools stay invisible if only final text is scored.

### 4. Industry Practice

**Common:** Manual spot-check of LangSmith/Langfuse traces; ad-hoc string checks.

**Strong:**

- Structured tool assertions in CI (`agentevals`, Langfuse code evaluators, OpenAI graders).  
- Separate scores: tool selection, argument correctness, order invariants, step budget.  
- Hamel/Shankar: test tool **name, arguments, result, and resulting state** as separate checks; include authorization/preconditions.  
- Calibrate LLM trajectory judges on human-labeled traces.  
- Promote failing prod traces into golden datasets.

### 5. Concrete Scenario (URL)

LangSmith trajectory evaluations (strict / unordered / subset / superset + LLM judge):  
https://docs.langchain.com/langsmith/trajectory-evals  

OpenAI — evaluate agent workflows via trace grading:  
https://developers.openai.com/api/docs/guides/agent-evals  

Hamel — tool call testing example (`cancel_order` + order status state):  
https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  

### 6. Open Questions

- How much argument fuzzy-matching is safe (city aliases, amount formatting) before hiding bugs?  
- Standard schema for cross-framework traces (OTel GenAI) vs vendor-native run trees?  
- Auto-mining reference trajectories from successful prod runs without overfitting?

### 7. Sources

- https://docs.langchain.com/langsmith/trajectory-evals  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://developers.openai.com/api/docs/guides/agent-evals  
- https://developers.openai.com/api/docs/guides/evals  
- https://developers.openai.com/api/docs/deprecations  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service  
- https://discuss.google.dev/t/end-to-end-evaluation-of-multi-agent-systems-on-vertex-ai-with-cloud-run-deployment-for-a2a-agents/250552  

---

## Concept B — Trajectory evaluation vs outcome evaluation

### 1. Fundamentals

**Definitions (Anthropic):**

- **Transcript / trajectory** — full interaction record (tools, reasoning, messages).  
- **Outcome** — final **environment state** after the trial (e.g. reservation exists in SQL), independent of what the agent claimed.

**Outcome evaluation:** Did the user goal / business state get achieved? Black-box success rule (exact answer, correct side effect, tests pass). Hamel phase 1: end-to-end task success first.

**Trajectory evaluation:** Did the path matter? Steps, order, tool choice, loops, efficiency, policy adherence. Langfuse: path ≠ destination; dimensions fail independently (wasteful path can still complete task; clean path can miss goal).

**Why both exist**

| Lens | Catches | Misses |
|------|---------|--------|
| Outcome-only | Wrong final state, failed bookings, wrong answers | Unsafe intermediate calls, inefficiency, policy skips that “got lucky” |
| Trajectory-only | Wrong tools/order, loops, scope creep | Valid alternate paths; may fail creative successes |
| Combined | Safety + success + efficiency | Higher build cost |

**Benchmark philosophy**

- **SWE-bench Verified / Terminal-Bench:** primarily **outcome** via tests / environment scripts.  
- **τ-bench / τ2-bench:** outcome = answer **and** DB state under policy; multi-turn user simulator.  
- **WebArena:** URL/page state + **backend state** for mutations (order actually placed).  
- **AgentBench:** success across interactive environments (OS, DB, web, …).  
- **LangSmith trajectory match:** process-centric; pair with separate outcome graders.

**Non-determinism metrics (Anthropic; τ2-bench culture):**

- **pass@k** — P(at least one success in k trials); rises with k.  
- **pass^k** — P(all k succeed); falls with k; critical for customer-facing reliability.

Capability vs regression suites: capability starts low pass rate (hill to climb); regression near 100%; graduate tasks as they stabilize.

### 2. Alternatives & Tradeoffs

| Strategy | Tradeoff |
|----------|----------|
| Grade outcomes only (Anthropic often prefers for open tasks) | Avoids brittle path tests; may allow policy-violating paths |
| Strict trajectory gold paths | Good for regulated workflows; brittle |
| Partial credit / checkpoints (Hamel goal checkpoints; Anthropic partial credit) | Better signal on long tasks |
| Transition failure matrices (Hamel / Bischof) | Diagnoses *where* paths break without requiring one gold path |
| LLM judge on trajectory without reference | Scalable nuance; calibration burden |

Hamel recommended order: **E2E success first** → then step-level diagnostics on failing workflows. Anthropic: don’t over-constrain paths; still verify critical tool invariants and state.

### 3. Necessity

Outcome-only → ship agents that refund without verifying identity if the DB still “looks” right sometimes, or that take 40 steps and blow cost budgets.  
Trajectory-only → reject agents that solve the user’s problem via a better unforeseen tool sequence (Anthropic τ2-bench loophole example: model found better policy-compliant solution than the eval authors anticipated).

### 4. Industry Practice

**Common:** Single “accuracy” number on final text.

**Strong:**

- Explicit split scores: `task_success`, `state_check`, `trajectory_*`, `tool_args_*`, cost/turns.  
- Offline CI on datasets; online judges on sampled prod (Langfuse).  
- Read transcripts regularly (Anthropic Step 6) — failures must look *fair*.  
- Balanced sets: cases where behavior **should** and **should not** fire (search over/under-trigger example).

### 5. Concrete Scenario (URL)

Anthropic — flight booking: transcript says booked; **outcome** is SQL reservation existence; graders on state + tools + rubric:  
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

τ-bench repo (DB state + policy):  
https://github.com/sierra-research/tau-bench  

WebArena (functional sites + backend verification):  
https://webarena.dev/  

Hamel — E2E then step diagnostics + transition matrices:  
https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  

Bryan Bischof talk referenced by Hamel (“Failure is A Funnel”, Data Council 2025) — transition matrices for text-to-SQL agents (see Hamel FAQ for embedding/context).

### 6. Open Questions

- When should a creative trajectory that violates written policy but helps the user count as pass? (eval hacking vs user value)  
- How to weight partial credit on long-horizon tasks?  
- Contamination and benchmark saturation (SWE-bench >80%) — when do public benchmarks stop guiding product work?

### 7. Sources

- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://github.com/sierra-research/tau-bench  
- https://webarena.dev/  
- https://github.com/THUDM/AgentBench  
- https://www.anthropic.com/engineering/building-effective-agents  

---

## Concept C — Common agent failure patterns

### 1. Fundamentals

Recurring failure modes called out across Anthropic, Langfuse, Hamel, and academic agent benchmarks:

#### C1. Tool misuse

- Wrong tool selected (search vs update; cancel vs refund).  
- Right tool, **wrong arguments** (IDs, dates, amounts, filters).  
- Skipping precondition tools (no auth/policy check).  
- Calling write tools when read would suffice (or vice versa).  
- Ignoring tool errors / empty results and hallucinating success.

**Eval hooks:** tool name assertions; JSON schema validation; semantic arg checks; state read-back; Hamel separate checks for name/args/result/state.

#### C2. Infinite loops / retry storms

- Repeated identical failing tool calls.  
- Oscillation between two tools without progress.  
- Re-entering propose/commit after `already_consumed`.  
- No max-turn / max-tool budget.

**Eval hooks:** Langfuse step-budget / loop detection code evaluators; transcript metrics `n_turns`, `n_toolcalls`; agent harness hard stops (Anthropic: stopping conditions). Aggregated agent graphs showing cycle edges.

#### C3. Premature stopping

- Agent ends turn before goal complete (“I’ve started the process…”).  
- Stops after partial multi-step workflow (identified issue, didn’t refund).  
- Exits when tool returns ambiguity instead of clarifying or retrying.

**Eval hooks:** outcome state checks; goal checkpoints; partial credit; max-turns *and* min-required-actions (superset trajectory); conversational resolution session scores.

#### C4. Context loss across long horizons

- Drops earlier constraints (budget, user preferences, prior confirmations).  
- Forgets which entities were already created → duplicates.  
- Multi-turn goal drift; answers each turn locally but never resolves session (Langfuse multi-turn dimension).  
- Summarization / memory truncation removes critical IDs.

**Eval hooks:** multi-turn / session-level scores; tests that require remembering constraints introduced early; AgentBench long interactive tasks; WebArena multi-step web tasks; Hamel context-retention diagnostic.

#### C5. Related patterns (include when teaching)

- **Over-refusal / under-trigger** (balanced evals needed).  
- **Eval hacking / loopholes** (pass graders without real solve — Anthropic: make graders resistant to bypasses).  
- **Harness/environment flakiness** mistaken for agent failure (shared state between trials).  
- **Brittle graders** punishing valid formats (CORE-Bench / METR examples in Anthropic post).  
- **Unsafe but successful paths** (outcome green, trajectory red).

### 2. Alternatives & Tradeoffs (mitigations)

| Failure | Mitigation | Tradeoff |
|---------|------------|----------|
| Tool misuse | Better ACI/docs; fewer overlapping tools; schema strictness; poka-yoke args (Anthropic Appendix 2) | Upfront tool design cost |
| Loops | Max iterations; detect repeated calls; circuit breakers | May stop recoverable retries early |
| Premature stop | Explicit completion criteria in prompt; outcome graders; required tool supersets | Longer average trajectories |
| Context loss | External memory/state store; periodic goal restatement; session evals | Memory complexity / noise |
| Duplicates | Idempotency + audit (Week 14) | Infra dependency |

### 3. Necessity

These patterns dominate production incidents for side-effecting agents. Benchmarks that only score final text systematically under-detect them — hence WebArena backend checks, τ-bench DB state, and trajectory tooling in LangSmith/Langfuse/Vertex.

### 4. Industry Practice

**Common:** Fix one-off prompt after a viral failure.

**Strong (Anthropic roadmap + Hamel):**

1. Start with 20–50 tasks from **real failures**.  
2. Record **first upstream failure** in error analysis.  
3. Build **transition failure matrices** (last good state → first fail).  
4. Codify as regression tests (capability → regression graduation).  
5. Combine code graders + calibrated LLM judges + periodic human review (Swiss-cheese layers).  
6. Always read transcripts when scores move.

### 5. Concrete Scenario (URL)

**Tool misuse / policy:** Anthropic support agent example requiring `verify_identity` then `process_refund` with amount constraint — missing verify is a trajectory fail even if money moves.  
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

**Loops / budgets:** Langfuse trajectory quantitative checks (step count, loop detection, `within_step_budget`):  
https://langfuse.com/resources/engineering/ai-agent-evaluation  

**Context / long horizon:** WebArena multi-step site tasks; AgentBench multi-environment:  
https://webarena.dev/ · https://github.com/THUDM/AgentBench  

**Transition matrices for debugging multi-tool agents:**  
https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  

**YouTube / course:** DeepLearning.AI A2A course (multi-agent failure surfaces when handoffs drop context) — https://goo.gle/dlai-a2a ; Bryan Bischof “Failure is A Funnel” (Data Council 2025) referenced from Hamel FAQ.

### 6. Open Questions

- Automatic loop classifiers that don’t flag legitimate exploratory search?  
- How to eval memory systems separately from the policy model?  
- Standardized taxonomy of agent failures across vendors (shared labels for incident → dataset pipelines)?

### 7. Sources

- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html  
- https://webarena.dev/  
- https://github.com/THUDM/AgentBench  
- https://github.com/sierra-research/tau-bench  
- https://developers.openai.com/api/docs/guides/agent-evals  

---

## Concept D — Academic & industry agent benchmarks (reference map)

### 1. Fundamentals

| Benchmark | Focus | Primary signal |
|-----------|--------|----------------|
| **AgentBench** (THUDM, ICLR’24) | LLM-as-agent across 8 envs (OS, DB, KG, games, ALFWorld, WebShop, Mind2Web, …) | Cross-domain interactive success |
| **WebArena** | Realistic self-hosted websites; multi-step browser tasks | End state / URL / **backend DB** |
| **τ-bench / τ2-bench** (Sierra) | Tool-agent-user; retail/airline (+ telecom in τ2); policy rules | Final answer + **DB state**; **pass^k** reliability |
| **SWE-bench Verified** | Real GH issues | Fail-to-pass tests without regressions |
| **Terminal-Bench** | End-to-end technical tasks in terminal | Environment scripts |
| **OSWorld** | Full OS computer use | Artifact/OS state scripts |
| **BrowseComp** | Hard web research needles | Verifiable answers |

Use benchmarks to compare **models/harnesses**; use **private product evals** for deployment decisions (academic review literature stresses disconnect between benchmark scores and deployment viability — cost, safety, maintainability often unscored).

### 2. Alternatives & Tradeoffs

Public benchmarks: comparable, citable, saturating, contaminable.  
Private domain evals: predictive for your users, expensive to build, not comparable externally.  
Hybrid: run both; never ship on public leaderboard alone.

### 3. Necessity

Without some shared benchmark literacy, teams reinvent weak evals (text match only). Without private evals, teams overfit to public sets and fail in production.

### 4. Industry Practice

Anthropic customers (Bolt, Descript, Claude Code, etc.) build domain suites; use Harbor/Braintrust/LangSmith/Langfuse as harnesses; borrow grader patterns from SWE-bench / τ-bench (state checks + rubrics).

### 5. Concrete Scenario (URL)

- https://github.com/THUDM/AgentBench  
- https://webarena.dev/  
- https://github.com/sierra-research/tau-bench  
- Anthropic discussion of these benchmarks: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

### 6. Open Questions

- Leaderboard gaming vs. real reliability (pass^k still rare outside τ-family).  
- Multimodal / computer-use eval cost.  
- Multi-agent A2A benchmarks still immature vs single-agent.

### 7. Sources

- https://github.com/THUDM/AgentBench  
- https://webarena.dev/  
- https://github.com/sierra-research/tau-bench  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://arxiv.org/abs/2308.03688 (AgentBench paper — use arXiv, not pirate mirrors)  
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service  

---

## Concept E — Practical eval stack & process (synthesis)

### 1. Fundamentals

**Graders (Anthropic triad):** code-based · model-based · human. Prefer deterministic where possible; LLM where necessary; humans for calibration/gold.

**Process (merge Anthropic + Hamel + Langfuse + OpenAI):**

1. Instrument traces (tools structured).  
2. Debug with trace grading on real runs.  
3. Define unambiguous tasks + reference solutions.  
4. Split **outcome** vs **trajectory** scores.  
5. Offline experiments in CI; online sampling in prod.  
6. Error analysis → transition matrices → new regression cases.  
7. Watch saturation; refresh hard tasks.  
8. Read transcripts continuously.

**Framework pointers:** LangSmith + `agentevals`; Langfuse datasets/experiments/evaluators; OpenAI trace graders / datasets (mind platform deprecation → Promptfoo); Braintrust; Harbor for containerized benchmark-style tasks; Vertex Gen AI Evaluation for GCP/A2A stacks.

### 2–4. Alternatives, Necessity, Industry Practice

Covered in Concepts A–C; treat this as the operating checklist for FDEs.

### 5. Concrete Scenario (URL)

Anthropic full roadmap (“Going from zero to one”):  
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

OpenAI agent eval decision page:  
https://developers.openai.com/api/docs/guides/agent-evals  

Promptfoo migration (post-OpenAI Evals deprecation):  
https://developers.openai.com/cookbook/examples/evaluation/moving-from-openai-evals-to-promptfoo  

### 6. Open Questions

- Org ownership: platform eval team vs product-owned tasks (Anthropic favors domain experts contributing tasks).  
- Online deterministic graders maturity differs by vendor — verify current GA status before standardizing.

### 7. Sources

- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://developers.openai.com/api/docs/guides/agent-evals  
- https://developers.openai.com/cookbook/examples/evaluation/moving-from-openai-evals-to-promptfoo  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  

---

## Cross-cutting notes for curriculum authors

1. Teach **transcript ≠ outcome** in the first hour; reuse Week 14 side-effect examples.  
2. Show one **strict** trajectory test and one **outcome** state test side-by-side on the same refund task.  
3. Drill the four failure patterns with a single Langfuse/LangSmith trace screenshot each.  
4. Assign reading: Anthropic demystifying evals + Hamel agentic workflow FAQ + LangSmith trajectory docs.  
5. Optional media: DeepLearning.AI A2A course trailer (https://goo.gle/dlai-a2a); Bischof Data Council talk via Hamel.  
6. Next weeks: Week 16 error-analysis flywheel; Week 17 LLM-judge calibration & observability deepen model-based graders introduced here.
