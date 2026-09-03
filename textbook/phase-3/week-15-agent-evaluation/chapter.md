# Chapter 15 — Agent evaluation

> **Phase 3 — Agentic Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-3/week-15-agent-evaluation/`  
> **Syllabus Build:** Do **not** ship a third agent. **Instrument and score the two you already have.** (1) Wire traces on the Week 11 loop agent **and** the Week 14 write agent (LangSmith **or** Langfuse **or** OpenAI traces — one primary, map the other). Tool calls must be **structured fields** (`name`, `arguments`, …), not parsed chat text. Session IDs on the conversational agent. (2) Define **split scores**, never one “quality” number: `task_success` (outcome / read-back), `tool_name`, `tool_args`, `policy_order` (e.g. `verify_identity` before `commit_refund`), `within_step_budget`, cost/turns. (3) Add **tool-call correctness** tests: Hamel’s four checks (name, arguments, result, resulting state) plus authorization/preconditions. Use **code graders** for decidable checks; LLM-as-judge only for semantic appropriateness. (4) On the **same** refund (or ticket/calendar) task, show **one strict trajectory assertion** and **one environment outcome assertion** side by side — Anthropic: path can be too rigid; outcome without path misses unsafe intermediates. (5) Codify the **four failure patterns** as regression cases (loop detector, premature-stop outcome fail, missing tool, dropped early constraint). Promote at least one **real** failing prod/dev trace into the dataset. (6) **Literacy assignment (not a product gate):** read τ-bench (state + pass^k), WebArena (functional / backend), AgentBench (cross-env). Do **not** claim you “beat WebArena” as a shipping criterion.

---

## Chapter framing

Week 15 is the **measurement** week of Phase 3. Weeks 11–13 taught the **loop**, **MCP**, and **graphs / HITL**. Week 14 required a **second agent that mutates state**, with idempotency, confirmation, dry-run, and audit. This week does **not** add a third product. It **instruments both agentic systems** you already shipped and grades them the way production teams grade agents: **traces**, **tool-call correctness**, **trajectory vs outcome**, and a **failure-pattern vocabulary**.

**Do not start Week 16 (error-analysis flywheel) from this chapter** — this week instruments and scores; the flywheel that *mines* those failures into a taxonomy and synthetic data is next week. Do **not** skip this week for “we’ll look at LangSmith later.” Week 16 has nothing to annotate if traces are unstructured.

Anthropic’s eval vocabulary is the spine ([Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)):

| Term | Meaning |
|------|---------|
| **Task** | One test with inputs and success criteria |
| **Trial** | One attempt (models are non-deterministic — run many) |
| **Grader** | Logic that scores transcript and/or outcome (code, model, human) |
| **Transcript / trace / trajectory** | Full record of a trial (messages, tools, reasoning, intermediates) |
| **Outcome** | Final **environment** state (SQL reservation, refund row), independent of what the agent *said* |
| **Eval harness** | Runs tasks, records steps, grades, aggregates |
| **Agent harness** | Scaffold + model evaluated **together** (Claude Code is a harness; the model is not the whole agent) |
| **Suite** | Collection of tasks sharing a goal (refunds, cancellations, escalations) |

OpenAI: a **trace** captures end-to-end model calls, **tool calls**, **guardrails**, and **handoffs** for one run. Start with **trace grading** while debugging; graduate to **datasets / eval runs** for repeatability ([agent evals](https://developers.openai.com/api/docs/guides/agent-evals)).

Langfuse: agent quality is **four dimensions that fail independently** — trajectory, tool use, task completion, multi-turn. Evaluating only the final answer misses most failures ([AI agent evaluation](https://langfuse.com/resources/engineering/ai-agent-evaluation)).

Hamel Husain & Shreya Shankar: treat the agent as a black box for **end-to-end task success first**; then score **tool choice, parameters, error handling, context retention, efficiency, goal checkpoints**; use **transition failure matrices** (last good state → first failure) ([agentic workflows](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html)).

**What you ship this week**

```
Week 11 agent ──► tracer (LangSmith | Langfuse | OpenAI traces)
                      │
Week 14 agent ──► same tracer (session_id / thread_id / taskId)
                      │
              ┌───────┴────────┐
              │  code graders  │  tool name, schema, budget, DB state
              │  LLM judges    │  appropriateness, tone (calibrated)
              │  dataset       │  20–50 real failures (Anthropic Step 0)
              └───────┬────────┘
                      ▼
         split scorecard (not one accuracy)
```

A trial can **pass outcome and fail trajectory** (refund without verify — unsafe). A trial can **pass trajectory and fail outcome** (called the right tools; DB never updated — harness/tool bug). That contrast is the teaching moment.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume Deployment Copilot’s Week 11 loop agent and Week 14 write agent on the **same** tracer.

---

### Instrumenting both agentic systems (tool-call correctness as first eval layer)

* **Fundamentals:**  
  Week 15’s first job is **instrumentation**, not a third agent. Both systems you already shipped must emit traces:

  | System | Built in | What traces must show | First graders |
  |--------|----------|------------------------|---------------|
  | **Loop agent** | Week 11 (+ MCP/graph in 12–13) | Turns, tool names/args, retries, stop reason | Tool selection; schema-valid args; max-turn budget; no identical retry storms |
  | **Write agent** | Week 14 | Preview vs commit, idempotency key (wrapper-owned), interrupt/approval, **read-back** | Policy order (`verify_*` / `preview_*` before `commit_*`); args (amount, ids); **DB/API state**; audit intent+result |

  If only the chatbot is traced, you will “pass” Week 15 while the refund agent still double-writes. If only the write agent is traced, you miss conversational **context loss** and multi-turn resolution (Langfuse **session** scores).

  **Tool-call correctness** is the **first eval layer**. Hamel: test **name, arguments, result, and resulting state** as **separate** checks. A valid JSON call can still be wrong if authorization/preconditions were skipped. Example: `cancel_order` + correct order id + successful HTTP + **status actually cancelled** before the user is told it worked.

  LangSmith `agentevals` match modes ([trajectory evals](https://docs.langchain.com/langsmith/trajectory-evals)):

  | Mode | Meaning | Use on this syllabus |
  |------|---------|----------------------|
  | `strict` | Same messages/tool calls in same order | `verify_identity` then `process_refund` |
  | `unordered` | Same tools/args, any order | Parallel `get_weather` + `get_events` |
  | `subset` | No tools beyond the reference | Efficiency / no extra payment tools |
  | `superset` | At least the required tools; extras OK | Minimum required actions |

  Default equality: same tool **and** same arguments (`tool_args_match_mode` / overrides). LLM-as-judge trajectories (`TRAJECTORY_ACCURACY_PROMPT`) when there is no single gold path.

  Langfuse: code and LLM judges see tool calls as structured `{id, name, arguments, type, index}` — **do not parse raw text**. Score `used_search_tool` (boolean) and `tool_call_count` (numeric) on the same evaluator. Vertex AI Gen AI evaluation (public preview, Jan 2025): **final response** vs **trajectory** metrics — exact match, in-order match, any-order match, precision, recall, single-tool use ([Cloud blog](https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service)). Useful mapping table if the stack is GCP/A2A.

  Illustrative split (refund task — both graders on **one** trial):

  ```python
  # Outcome (environment) — Week 14 read-back is truth
  assert db.refunds.get(payment_id).status == "processed"
  assert db.refunds.get(payment_id).amount_cents == 5000

  # Trajectory (policy) — Anthropic support example
  tools = [tc["name"] for tc in trace.tool_calls]
  assert "verify_identity" in tools
  assert tools.index("verify_identity") < tools.index("process_refund")
  assert any(tc["name"] == "process_refund" and tc["args"]["amount"] <= 100 for tc in trace.tool_calls)

  # Budget — Langfuse within_step_budget
  assert len(trace.tool_calls) <= MAX_TOOLS
  ```

* **The Alternatives:**  

  | Path | What you optimize | What you sacrifice |
  |------|-------------------|-------------------|
  | **Split scores + both agents** (syllabus) | Debuggable, interviewable | Harness work |
  | Final-text accuracy only | One slide | Hidden unsafe tools, loops, wrong IDs |
  | Strict gold trajectories only | Policy order | Punishes valid creative paths (Anthropic; τ² loophole) |
  | Outcome-only (SWE-bench style) | Any valid path | Policy skips that “got lucky” |
  | LLM-judge everything | Flexible | Cost, non-determinism, uncalibrated TPR/TNR |
  | Public leaderboard as ship gate | Comparable numbers | Contamination, cost/safety unscored |
  | Trace one agent only | Less wiring | Blind spot on writes **or** on multi-turn |

  | Primary harness | Pros | Cons |
  |-----------------|------|------|
  | LangSmith + `agentevals` | Match modes; LC ecosystem | Vendor run tree |
  | Langfuse | Four dimensions; structured tool fields; self-host; CI action | Observation-level targeting discipline |
  | OpenAI traces + graders | Fast debug in dashboard | Evals **platform** deprecation (read-only Oct 31 2026, shutdown Nov 30 2026 — migrate portable configs, e.g. Promptfoo cookbook) |
  | Vertex agent eval | Trajectory precision/recall; A2A stacks | GCP-centric |
  | Harbor / Braintrust | Containerized / experiment tracking (Anthropic appendix) | Extra product |

  Default path (synthesis): **instrument first**; **outcome is the store** (Week 14 read-back) and trajectory is **path and policy** — score both independently; Hamel order **E2E first** then step diagnostics; prefer **code** graders for tool name/schema/budget and **LLM judge** for reasonableness (calibrated against humans); use LangSmith match modes with intent (`strict` for policy order, `unordered` for independent reads, `subset` for no extras, `superset` for required actions) — Anthropic: do not over-use strict sequences.

* **Failure Modes:**  
  - Week 14 writes are “tested” by reading the assistant’s last sentence. τ-bench exists because **fluent closings ≠ DB state** ([Yao et al., arXiv:2406.12045](https://arxiv.org/abs/2406.12045)).  
  - Prompt/model swaps “feel worse” with no way to tell **tool routing** from **generation**. OpenAI’s first trace-grading questions are exactly: right tool? handoff? policy?  
  - Cost/latency blowups from extra tools stay invisible (Langfuse: wasteful path can still complete the task).  
  - Week 16 error analysis has no traces to label; Week 17 judges have nothing calibrated.  
  - FDE interviews ask for **tool-call tests** and **state checks**, not “we used LangSmith.”  
  - Only one agent instrumented → blind spot on writes **or** on multi-turn context loss.

* **Average vs. Strong Engineer:**  
  **Average:** screenshot of a pretty trace UI; one LLM “quality” score; no dataset version; only the demo chatbot instrumented.  
  **Strong:** 20–50 tasks from **real failures** (Anthropic); capability suite (low pass, hill to climb) vs regression suite (~100%); code + model + periodic human; **read transcripts when scores move** (Anthropic Step 6); offline CI + online sampled evaluators (Langfuse). **FDE bar:** both agents on the same tracer; split scorecard; one counterexample of trajectory vs outcome disagreement; pass^k **mentioned** for customer-facing writes (τ-bench culture); public benchmarks used as **literacy**, private evals as **ship gates**. Descript (Anthropic case): don’t break things / do what I asked / do it well; quality vs regression suites. Bolt: static analysis + browser agents + LLM judges after they already had users. Harrison Chase (LangChain) at AI Engineer: raise value-if-right and P(success); lower cost-if-wrong — eval measures P(success) and cost-if-wrong (unsafe tools, loops) ([YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg)).

* **Worked Example:**  
  **Same $50 refund, two graders disagree.**

  1. Agent looks up payment, calls `process_refund(amount=50)` **without** `verify_identity`. Payments table shows refunded.  
  2. **Outcome grader:** pass (row exists, amount matches) — τ-bench / WebArena **backend** style.  
  3. **Trajectory grader:** fail — Anthropic required `{tool: verify_identity}` then `{tool: process_refund, params: {amount: "<=100"}}`.  
  4. LangSmith `strict` against a reference that includes verify → `trajectory_strict_match = false`.  
  5. Langfuse `used_verify_identity = false` boolean on the tool-call observation; `task_completion` on the root may still be true.  
  6. Hamel: first upstream failure is **precondition skip**, not “wrong refund amount.” Put that cell in a transition matrix: `lookup → commit` instead of `lookup → verify → commit`.

  LangSmith weather example (docs): `get_weather(city="San Francisco")` with `strict` match — cheap tool-correctness unit test for the Week 11 agent. τ-bench paper: gpt-4o-era function-calling agents **&lt;50%** tasks; **pass^8 &lt; 25%** retail — consistency, not just one lucky trial. WebArena: GPT-4 agent **14.41%** end-to-end vs human **78.24%** on 812 tasks; graders check **repository contents / orders**, not action-string match.

* **Apply It:**  
  1. Pick **one** primary tracer (LangSmith, Langfuse, or OpenAI traces); map the other for literacy — do not dual-maintain two production trees yet.  
  2. Emit structured tool calls (`name`, `arguments`, …) from **both** the Week 11 loop agent and the Week 14 write agent; add `session_id` / `thread_id` / `taskId`.  
  3. Define split scores: `task_success`, `tool_name`, `tool_args`, `policy_order`, `within_step_budget`, cost/turns — never one “quality” percent.  
  4. On one refund (or ticket/calendar) task, assert **outcome** (DB read-back) and **trajectory** (verify before commit) on the **same** trial.  
  5. Print a split scorecard in CI or a notebook; keep the trajectory/outcome disagreement as an interview artifact.  
  6. Seed a dataset of 20–50 tasks from **real** failures (Anthropic Step 0); promote at least one failing prod/dev trace.

---

### Evaluating agentic traces (structured tool-call graders)

* **Fundamentals:**  
  An **agentic trace** (Anthropic: **transcript**; also trajectory) is the complete record of one **trial**: model messages, **tool calls**, tool results, guardrails, handoffs, and intermediate state. For the Anthropic API, that is the **full messages array** across the eval run. For OpenAI, a trace is the end-to-end record of model calls, tool calls, guardrails, and handoffs for **one run** ([agent evals](https://developers.openai.com/api/docs/guides/agent-evals)).

  Langfuse stresses a structural point: the unit of evaluation is a **trace** (a tree of observations: LLM calls, tools, retrievals), not a single completion. Tool-argument checks belong on **tool-call observations**; task completion belongs on the **root**. Conversational agents add a third unit: the **session** ([AI agent evaluation](https://langfuse.com/resources/engineering/ai-agent-evaluation)).

  **Trace grading** answers questions final-answer grading cannot:

  - Did the agent pick the **right tool** (search vs update; cancel vs refund)?  
  - Were **arguments** schema-valid **and** semantically correct (business IDs, amounts, filters)?  
  - Was **order** constrained when policy requires it (verify identity before refund)?  
  - Did a **handoff** occur when it should (OpenAI explicit question)?  
  - Were instructions / safety policies violated **mid-trajectory**?  
  - Did the agent **recover** from tool errors, or hallucinate success (Hamel: error handling as its own check)?

  | Method | What it checks | Notes |
  |--------|----------------|-------|
  | Code / deterministic assertions | Tool name present, JSON schema, exact or constrained arg values, call counts, step budget | Fast, cheap, reproducible (Anthropic code graders; Langfuse code evaluators) |
  | Trajectory match (`agentevals`) | Actual vs reference tool sequence | `strict`, `unordered`, `subset`, `superset` |
  | LLM-as-judge on trajectory | Reasonableness, efficiency, appropriateness without a rigid path | Needs human calibration (Hamel YouTube: treat judge as a classifier, measure TPR/TNR) |
  | State / outcome checks | DB or environment after tools ran | Catches “said done, didn’t write” — next concept |
  | Vertex trajectory metrics | Exact / in-order / any-order match; precision; recall; single-tool use | GCP mapping of the same ideas |

  **LangSmith / AgentEvals.** Package: `pip install agentevals` / `npm install agentevals`. Factory: `create_trajectory_match_evaluator(trajectory_match_mode=...)`. Docs example: weather agent vs reference `get_weather(city="San Francisco")` → score key `trajectory_strict_match` boolean. Unordered: `get_events` + `get_weather` in either order. Superset: reference only requires `get_weather`; agent may also call `get_detailed_forecast`. Argument equality via `tool_args_match_mode` / `tool_args_match_overrides`. **LLM trajectory judge:** `create_trajectory_llm_as_judge(...)` with `TRAJECTORY_ACCURACY_PROMPT` (no reference) or `TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE`.

  **Langfuse four dimensions** (measure all; they fail independently):

  | Dimension | Question | Typical metrics |
  |-----------|----------|-----------------|
  | Trajectory | Sensible path? | Step count, unnecessary calls, loops, required steps, ordering |
  | Tool use | Right tools, right args? | Selection, argument validity, tool error rate, recovery |
  | Task completion | User goal met? | Goal achievement, answer correctness, resolution rate |
  | Multi-turn | Holds across a conversation? | Context retention, goal drift, turns-to-resolution, session outcome |

  Tool calls (July 2026+): structured on the observation (`name`, `arguments`, `id`, `type`, `index`). **Swiss-cheese layers:** cheap code on every sampled trace; LLM judge on semantic subset; humans on disagreements / calibration. Offline = datasets/experiments (CI). Online = sampled production evaluators. CI: `langfuse/experiment-action@v1.0.0` + `RegressionError` on threshold; pin `dataset_version`. Target **root observation** for whole-run judges (trace-level judges are legacy).

  **OpenAI workflow:** (1) Logs → Traces; inspect a representative run. (2) Create a grader; run against selected traces. (3) When “good” is known, **datasets + eval runs**. Note: **Evals platform** deprecation announced June 2026 — read-only **31 Oct 2026**, shutdown **30 Nov 2026**; cookbook migrates portable configs to Promptfoo. **Trace-grading concepts remain**; do not build a career on the deprecated UI.

  **Anthropic graders:** Code-based (string/regex, binary tests, static analysis, outcome verification, tool-call verification, transcript analysis `n_turns` / `n_toolcalls` / tokens) — fast, cheap, objective; **brittle** to valid variation. Model-based (rubrics, NL assertions, pairwise, reference-based, multi-judge) — need **human calibration**. Human: SME review, spot-check, IAA. Support-agent YAML requires `verify_identity`, `process_refund` with `amount <= 100`, `send_confirmation`, `max_turns: 10`, plus **state_check** — **trace + outcome in one task**. Instinct warning: requiring an **exact tool sequence** is **often too rigid**; still use tool-call graders for **required safety steps**.

  **Hamel four-way tool test** on `cancel_order`: (1) selected `cancel_order`, (2) correct order ID, (3) successful tool result, (4) **order status changed** before the user is told — plus **authorization**. Checkpoints on long workflows can each fail independently.

* **The Alternatives:**  

  | Approach | Pros | Cons |
  |----------|------|------|
  | Strict trajectory match | Catches policy-order bugs; deterministic CI | Punishes creative valid paths |
  | Soft match (unordered / subset / superset) | Less brittle | Misses order-sensitive bugs if you picked the wrong mode |
  | Args-only schema validation | Cheap safety net | Misses semantic wrong-ID (`order_id` of someone else that still parses) |
  | LLM judge on tools (no reference) | Flexible | Non-deterministic; cost; uncalibrated judges lie (Hamel) |
  | Outcome-only | Rewards any valid path | Hides unsafe intermediate tool use |
  | Hybrid (Anthropic / Langfuse / Hamel) | Best signal | More harness complexity |
  | Parse tool calls from assistant text | Works on old logs | Fragile; Langfuse explicitly says use structured fields |

  **Match-mode selection is a product decision**, not a default. Refund SOP → `strict` or an explicit order assertion. Multi-source research → `unordered` + outcome. “Must call search when the question needs it” → boolean code check (Langfuse: retrieval is a **tool the agent chooses**).

* **Failure Modes:**  
  - Agents pass answer rubrics while calling **forbidden** tools (payment twice; `drop_table`).  
  - Wrong arguments (amount, `customer_id`) look fine in fluent text.  
  - Handoff/routing regressions appear as vague “quality feels worse” (OpenAI’s motivation for trace grading).  
  - Extra tools blow **cost/latency** while task completion stays green (Langfuse independent dimensions).  
  - Error analysis (Week 16) cannot find the **first upstream failure** if tools are not structured.  
  - Hamel on complex workflows: without logging **LLM calls, tool usage, human approvals, and database writes**, diagnosis stalls.

* **Average vs. Strong Engineer:**  
  **Average:** click through LangSmith/Langfuse; grep strings in the last assistant message.  
  **Strong:** structured assertions in CI (`agentevals`, Langfuse code evaluators, OpenAI graders); **separate scores** for selection, args, order, budget; promote failing prod traces into golden datasets; calibrate trajectory judges on human-labeled traces; **read transcripts** when scores move (Anthropic Step 6 — failures must look *fair*). **FDE bar:** Hamel four checks on the write agent; Langfuse/OpenAI instrumentation on **both** agents; Vertex-style precision/recall as optional analytics, not the only number; balanced tests where a tool **should** and **should not** fire (Anthropic web-search over/under-trigger). Langfuse agent graph (beta 2026): **Aggregated** mode collapses repeats (`retrieve_docs (3/3)` + cycle edges = loops); **Expanded** unrolls the DAG — codify “must not call the payment tool twice.”

* **Worked Example:**  
  **LangSmith official weather test** — reference trajectory includes `get_weather` with `city: San Francisco`; evaluator `trajectory_match_mode="strict"`. This is the Week 11 agent’s unit-level analogue: **tool name + args**, not “the model said it was sunny” ([trajectory evals](https://docs.langchain.com/langsmith/trajectory-evals)).

  **OpenAI** — debug with traces first (right tool, handoff, policy), then datasets ([agent evals](https://developers.openai.com/api/docs/guides/agent-evals)).

  **Hamel `cancel_order`** — four checks including **resulting state** ([agentic workflows FAQ](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html)).

  **Langfuse** — `ctx.observation.tool_calls` / `toolCalls`; `within_step_budget` as a production boolean ([AI agent evaluation](https://langfuse.com/resources/engineering/ai-agent-evaluation)).

  Calibrate judges: Hamel *How To Approach Your AI Evals* ([YouTube](https://www.youtube.com/watch?v=DZxaPNYi_k0)) — LLM-as-judge is a classifier; measure against humans or evals lose trust.

* **Apply It:**  
  1. Ensure tool calls land as **structured fields** on observations — ban parsing assistant text for graders.  
  2. Add code graders for tool name, JSON schema, constrained args, call counts, and step budget.  
  3. For policy-order SOPs, use LangSmith `strict` (or an explicit order assertion); for independent reads, use `unordered`.  
  4. Implement Hamel’s four checks on the write agent’s primary mutate tool (name, args, result, resulting state + authorization).  
  5. Score Langfuse dimensions separately (or equivalent split scores); attach task-completion judges to the **root** observation.  
  6. If using an LLM trajectory judge, calibrate TPR/TNR against a human-labeled slice before trusting CI.

  `[NEEDS MORE RESEARCH]`: how much argument **fuzzy-matching** (city aliases, `$50` vs `5000` cents) is safe before hiding bugs; whether OTel GenAI or vendor run trees should be the portable cross-framework trace schema; how to version tool schemas so old dataset items remain meaningful after ACI changes.

---

### Trajectory evaluation vs outcome evaluation

* **Fundamentals:**  
  Anthropic definitions ([Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)):

  - **Transcript / trajectory** — full interaction record (tools, reasoning, messages).  
  - **Outcome** — final **environment state** after the trial (e.g. whether a reservation **exists in SQL**), independent of the agent’s closing sentence.

  A flight-booking agent can say “Your flight has been booked” while the outcome is **no row**. That trial **failed**, regardless of fluent text. Conversely, Opus 4.5 on a **τ²-bench** flight task found a **policy loophole**: it “failed” the eval as written but produced a **better** user solution — graders too path- or policy-literal.

  **Outcome evaluation:** Did the user goal / business state get achieved? Black-box success rule (exact answer, correct side effect, tests pass). Hamel **phase 1**: end-to-end task success first, with a **precise success rule** per task (human or **validated** LLM judge). Record the **first upstream failure** during error analysis.

  **Trajectory evaluation:** Did the **path** matter? Steps, order, tool choice, loops, efficiency, policy adherence. Langfuse: **path ≠ destination**; dimensions fail independently (wasteful path can complete the task; clean path can miss the goal).

  | Lens | Catches | Misses |
  |------|---------|--------|
  | Outcome-only | Wrong final state, failed bookings, wrong answers, “said done / didn’t write” | Unsafe intermediate calls, inefficiency, policy skips that got lucky |
  | Trajectory-only | Wrong tools/order, loops, scope creep, skipped verify | Valid alternate paths; may fail creative successes (Anthropic rigidity warning) |
  | Combined | Safety + success + efficiency | Higher harness cost |

  Hamel on **complex multi-step** workflows: use **both** outcome metrics and **process** metrics (step count, time, resources). Process failures are often more deterministic — debug them first. Segment error analysis by **workflow stage**; early errors **cascade** ([multi-step FAQ](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html)).

  **Partial credit / checkpoints.** Anthropic: a support agent that identifies the problem and verifies identity but fails the refund is **better** than one that fails immediately. Hamel **goal checkpoints** on long workflows. LangSmith `superset` is a coarse checkpoint (“at least these tools”).

  **Transition failure matrices** (Hamel / Bischof): rows = last successful state, columns = first failure. Example: GenSQL → ExecSQL = 12 failures vs DecideTool → PlanCal = 2 — investigate the hotspot. Bischof *Failure is a Funnel* (Data Council 2025) applies product-analytics drop-off thinking to agent stages.

  **Non-determinism: pass@k vs pass^k** (Anthropic + τ-bench culture):

  | Metric | Meaning | As k grows | Use when |
  |--------|---------|------------|----------|
  | **pass@k** | P(at least one success in k trials) | **Rises** | Coding with a verifier; best-of-n is deployable |
  | **pass^k** (“pass-hat-k”) | P(**all** k trials succeed) | **Falls** | Customer-facing agents; user gets one shot |

  At k=1 they coincide. At large k they tell opposite stories. τ-bench: even strong function-calling agents succeeded on **&lt;50%** of tasks; **pass^8 &lt; 25%** in retail. If per-trial p = 0.75, pass^3 ≈ 0.42. Anthropic: a 75% per-trial agent is **not** “75% reliable in production” if users cannot retry.

  **Capability vs regression suites** (Anthropic): capability starts at **low** pass rate (hill to climb); regression near **100%**. Graduate saturated capability tasks into regression. An eval at 100% tracks regressions but gives **no improvement signal** (SWE-bench Verified: ~30% → **&gt;80%** saturation warning).

  How public benchmarks sit on this split:

  | Benchmark | Primary signal | Trajectory? |
  |-----------|----------------|-------------|
  | **SWE-bench Verified / Terminal-Bench** | **Outcome** via tests / environment scripts | Optional transcript heuristics |
  | **τ-bench / τ²-bench** | Final answer **and** **DB state** vs annotated goal; user simulator | Transcript **not** the grade (conversations may vary) |
  | **WebArena** | **Functional correctness**: URL/page **and backend** | Explicitly **not** action-sequence match |
  | **AgentBench** | Interactive success across 8 envs (often SR / F1 / reward) | Process varies by env |
  | **LangSmith trajectory match** | Process-centric vs a reference | Pair with a **separate** outcome grader |

* **The Alternatives:**  

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

  Hamel recommended **order**: E2E success **first** → step-level diagnostics on **failing** workflows. Do not drown in step metrics while the agent never books the flight. Scoring combinations (Anthropic): **weighted**, **binary** (all graders pass), or **hybrid**.

* **Failure Modes:**  
  - **Outcome-only** → ship agents that refund without verifying identity if the DB sometimes “looks right,” or that take 40 steps and blow cost budgets. Week 14 audit/idempotency cannot be proven from chat text.  
  - **Trajectory-only** → reject agents that solve the user’s problem via a better unforeseen sequence (Anthropic τ² example; WebArena’s reason for functional graders).  
  - Brittle graders: CORE-Bench / METR anecdotes in the Anthropic post — valid formats or threshold wording punished; scores moved from 42% → 95% after harness/grader fixes. **Always read transcripts** (Step 6).  
  - Shared files/cache across trials: Claude cheated by reading **git history of previous trials** (Anthropic).  
  - Without **both**, FDE interviews cannot answer: “How do you know the agent didn’t skip KYC?” and “How do you avoid punishing a better tool sequence?”

* **Average vs. Strong Engineer:**  
  **Average:** single “accuracy” on final text; one trial per task; no isolation between trials.  
  **Strong:** explicit split scores (`task_success`, `state_check`, `trajectory_*`, `tool_args_*`, cost/turns); **isolated** environments per trial; offline CI + online judges (Langfuse); capability vs regression; balanced **should-fire / should-not-fire** sets; Swiss-cheese (evals + prod monitoring + A/B + transcript review + human studies). **FDE bar:** same refund task with **disagreement** between graders as a demo; pass^k discussed for the write agent; public benchmarks as **literacy**; **private** domain suite as the ship gate. Bolt: static analysis + **browser agents** testing the **app outcome** + LLM judges. Coding agents: SWE-bench-style **fail-to-pass without regressions**, plus optional transcript rubrics.

* **Worked Example:**  
  **Anthropic flight booking** — transcript says booked; **outcome** is SQL reservation existence; graders on **state + tools + rubric**. Partial credit if identity verified but refund missing ([Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

  **τ-bench** — User LM + agent + APIs + **policy markdown**. Reward from **DB vs annotated goal**. pass^k for reliability. Retail pass^8 &lt; 25% for gpt-4o-era FC agents ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)).

  **WebArena** — 812 tasks; `evaluator_router` scores functional correctness (page + **backend**). GPT-4 ~14.4% vs human ~78%. Reset Docker env between evals so trials are isolated ([webarena.dev](https://webarena.dev/)).

  **Hamel E2E then steps** — Berkeley homes example: checkpoints independent. Transition matrix → where to invest ([agentic workflows FAQ](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html)).

  Deployment Copilot interview demo: one refund trial that **fails trajectory / passes outcome** (or vice versa) on the same scorecard.

* **Apply It:**  
  1. For every write task, define an **environment success rule** (read-back) separate from any path assertion.  
  2. On the same refund/ticket task, keep one **strict** (or order) trajectory grader and one **state** grader side by side.  
  3. Prefer Hamel order: measure E2E task success first; only then dive into step diagnostics on failures.  
  4. Add at least one **checkpoint / partial-credit** score on a long workflow (e.g. verified identity but refund missing).  
  5. Discuss **pass^k** for the customer-facing write agent; do not report pass@k as if reliability improved.  
  6. Isolate trials (reset DB / Docker / files); when scores move, **read transcripts** before changing prompts.

  `[NEEDS MORE RESEARCH]`: when a creative trajectory that **violates written policy** but helps the user should count as pass (eval hacking vs user value vs policy update); how to weight partial credit on long-horizon tasks; pass^k sample size before the reliability curve is stable.

---

### Common agent failure patterns

* **Fundamentals:**  
  These patterns are the **named bugs** that trace + outcome evals exist to catch. They recur across Anthropic, Langfuse, Hamel, τ-bench analyses, WebArena error discussion, and AgentBench’s “typical reasons of failures.” Teach them as **labels you attach to traces**, then (Week 16) count them. This week: **recognize, instrument, write a regression case**.

  **C1. Tool misuse** — Wrong tool selected (search vs update; `cancel_order` vs `refund`); right tool, **wrong arguments** (IDs, dates, amounts, filters); skipping **precondition** tools (`verify_identity`, preview, policy fetch); calling **write** tools when a read would suffice (or answering from parametric memory when retrieval was required); ignoring tool **errors / empty results** and hallucinating success; **over-trigger / under-trigger** (Anthropic web-search evals); RAG-agent special case (Langfuse): skip retrieval, rewrite the query into something the index cannot serve, or loop retrieve without converging. Why: overlapping tool descriptions (bad ACI — Anthropic *Building effective agents*); schema too loose; no poka-yoke; policy only in the prompt. Eval hooks: tool **name** assertions; JSON schema; semantic arg checks; Hamel four-way + authorization; LangSmith `strict` / `subset`; Langfuse boolean `used_search_tool`; state read-back; Anthropic support YAML required tools.

  **C2. Infinite loops / retry storms** — Repeated **identical** failing tool calls; oscillation between two tools without progress; re-entering propose/commit after `already_consumed` (Week 14) without noticing; no **max-turn / max-tool** budget; Langfuse aggregated graph cycle edges (`retrieve_docs (12/12)`). Why: empty tool result not treated as a branch; missing circuit breaker; model “tries again” instead of clarifying. Eval hooks: step count, **loop detection**, `within_step_budget`; transcript metrics `n_turns` / `n_toolcalls`; harness hard stops; hash `(tool_name, canonical_args)` and fail if identical failure repeats ≥ N; distinguish **legitimate exploration** from **storms**.

  **C3. Premature stopping** — Agent ends before the goal is complete (“I’ve started the process…”); partial multi-step workflow (identified the issue, **did not refund**); exits on **ambiguous** tool output; conversational: five locally reasonable turns that never **resolve the session**; coding: stops before tests are run (Anthropic requires `run_tests` in tool_calls). Why: stop condition is “model emitted a final message,” not “environment matches goal.” Eval hooks: **outcome** state checks; goal checkpoints / partial credit; `superset` for required tools; session scores `resolved` / `escalated` / `abandoned`; `max_turns` **and** min-required-actions — budget alone can encourage **early exit**; τ-bench: episode ends on user `###STOP###` then **DB compare** — chat without write → reward 0.

  **C4. Context loss across long horizons** — Drops earlier constraints (budget, preferences, “don’t email the customer”); forgets entities already created → **duplicates** (Week 14 idempotency mitigates; eval still needs a case); multi-turn **goal drift**; summarization removes **critical IDs**; handoffs (Week 13 / A2A): peer does not receive constraints. Why: context windows; naive summarization; session not the eval unit; AgentBench authors: **poor long-term reasoning** is a main obstacle ([ICLR’24](https://arxiv.org/abs/2308.03688)); WebArena authors hypothesize weak **exploration and failure recovery**. Eval hooks: session-level scores; constraint injected in turn 1 required in turn 8 (Hamel **context retention**); AgentBench / WebArena long interactive tasks; τ-bench long conversations + policy; commit args still match earlier **preview** payload (Week 14 parity).

  **Related patterns** (teach, don’t collapse into C1–C4):

  | Pattern | Signal | Notes |
  |---------|--------|-------|
  | **Eval hacking / loopholes** | Pass graders without real solve | Anthropic: make graders resistant; τ² policy loophole |
  | **Harness/environment flakiness** | Correlated failures across “independent” trials | Shared state, leftover files, CPU; Claude reading prior-trial git history |
  | **Brittle graders** | Valid format / path punished | CORE-Bench float; METR threshold wording |
  | **Unsafe but successful paths** | Outcome green, trajectory red | The Week 15 teaching contrast |
  | **Over-refusal** | Balanced evals needed | Anthropic should/should-not sets |
  | **Instruction-following collapse** | AgentBench: OSS models vs GPT-4 gap | Multi-turn alignment data helps (paper) |

  Mitigations (not a substitute for evals): better ACI / fewer overlapping tools; max iterations + repeated-call detectors; explicit completion criteria + required tool supersets; external state store + session evals; Week 14 idempotency + audit for duplicates.

* **The Alternatives:**  

  | Debugging style | Pros | Cons |
  |-----------------|------|------|
  | One viral prompt fix | Fast | Same pattern returns next week |
  | **Taxonomy + regression cases** (syllabus) | Compounds | Needs traces and labels |
  | Only outcome SLOs | Ships “works” | Misses C1 unsafe paths, C2 cost, C4 drift |
  | Only loop/budget metrics | Cheap | Green loops that still fail the user |
  | Transition matrices (Hamel/Bischof) | Shows **where** the funnel drops | Needs agreed states |
  | Agent graph visual (Langfuse) | Fast loop spotting | Not a score |

  Hamel/Shankar **error analysis**: look at traces, free-form notes, **then** categories — do not start with a universal “accuracy” bar ([Intro to error analysis](https://www.youtube.com/watch?v=qH1dZ8JLLdU); full flywheel is Week 16).

* **Failure Modes:**  
  - These patterns dominate production incidents for **side-effecting** agents. Benchmarks that only score final text **under-detect** them — hence WebArena **backend** checks, τ-bench **DB state**, trajectory tooling, and Anthropic’s required `verify_identity` even when money moved.  
  - Without names, teams file “agent was weird” tickets. With names: **12/20 failures are C2 on `commit_refund`** and write a `within_step_budget` gate.  
  - AgentBench: poor **long-term reasoning, decision-making, and instruction following** map onto C4 + C1 + C3.  
  - Skipping regression fixtures → the same viral failure returns after the next prompt tweak.

* **Average vs. Strong Engineer:**  
  **Average:** fix one-off prompt after a viral failure.  
  **Strong (Anthropic roadmap + Hamel):** (1) start with **20–50** tasks from **real failures**; (2) record **first upstream failure**; (3) build **transition failure matrices**; (4) codify as regression tests (capability → regression graduation); (5) code graders + calibrated LLM judges + periodic human review; (6) **always read transcripts** when scores move. **FDE bar:** one fixture per C1–C4 on **both** agents (loop on the Week 11 search agent; skipped verify on the Week 14 write agent; premature close on a ticket; dropped budget constraint on a multi-turn shopper). Langfuse: when you find a bad trajectory, add the input to a dataset and write the violated property (“must not call the payment tool twice”).

* **Worked Example:**  
  - **C1 policy skip** — Anthropic support agent: missing `verify_identity` is a trajectory fail even if money moves.  
  - **C2 budgets** — Langfuse `within_step_budget`, loop detection, aggregated graph cycle edges.  
  - **C3 / C4 long horizon** — WebArena multi-step site tasks (Wikipedia + map + GitLab README); AgentBench OS/DB/web.  
  - **τ-bench failures** — complex DB reasoning, **ad-hoc policy**, **compound requests** — mix of C1 and C4 ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)).  
  - **Transition matrices** — Hamel agentic-workflow FAQ; Bischof *Failure is a Funnel* (Data Council 2025).  
  - Handoffs drop context — DeepLearning.AI A2A trailer ([YouTube](https://www.youtube.com/watch?v=4gYm0Rp7VHc)). Chase cost-if-wrong (unsafe tools) ([YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg)).

* **Apply It:**  
  1. Label traces with C1–C4 (plus related patterns when needed); do not invent a giant taxonomy this week.  
  2. Codify one regression case each: loop detector, premature-stop outcome fail, missing/wrong tool, dropped early constraint.  
  3. On the Week 11 agent: fail identical `(tool_name, canonical_args)` repeats ≥ N; assert `within_step_budget`.  
  4. On the Week 14 agent: fail skipped `verify_*` / `preview_*` before `commit_*` even if DB looks green.  
  5. Add a multi-turn fixture that injects a constraint early and requires it late (context retention).  
  6. Promote at least one **real** failing prod/dev trace into the dataset with its pattern label.

  `[NEEDS MORE RESEARCH]`: automatic loop classifiers that don’t flag legitimate exploratory search; how to eval memory systems separately from the policy model; whether multi-agent context loss at the **handoff boundary** is a different class than intra-agent truncation.

---

### Agent benchmarks (τ-bench, WebArena, AgentBench)

* **Fundamentals:**  
  Public agent benchmarks exist so teams can **compare models/harnesses** and **steal grader patterns**. They are **not** a substitute for private product evals (cost, safety, maintainability, your SOPs). Anthropic: use them as inspiration (state checks, user sims, isolation); **read transcripts** before taking a leaderboard at face value. Primary three for the syllabus: **τ-bench / τ²-bench**, **WebArena**, **AgentBench**. Adjacent (Anthropic post): SWE-bench Verified, Terminal-Bench, OSWorld, BrowseComp.

  **τ-bench (Tool-Agent-User)** — Sierra, 2024. Paper: Yao, Shinn, Razavi, Narasimhan ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)); code [sierra-research/tau-bench](https://github.com/sierra-research/tau-bench). Attacks prior benchmarks that give the agent **all information in one shot**, have **no human in the loop**, and **no domain policy**. Formulation: each task is a POMDP; state = **DB ⊗ user**; actions = DB APIs ∪ natural-language to the user; agent **cannot see** raw DB rows — only API observations; user **cannot see** tool traces; a **markdown policy** partially describes the world. User simulation: an LM plays the user from a scenario instruction; episode ends on `###STOP###`. **Grading (outcome-centric):** compare **database state at end** to an **annotated goal state** — transcript is **not** graded. **pass^k:** P(all k i.i.d. trials succeed). Headline (paper era): FC gpt-4o-class agents **&lt;50%** task success; retail **~61% pass^1** vs airline **~35%**; **pass^8 &lt; ~25%** retail. Failures: complex DB reasoning, **policy following**, **compound requests**. Domains: τ-retail, τ-airline.

  **τ²-bench** — Sierra et al., 2025 ([arXiv:2506.07982](https://arxiv.org/abs/2506.07982); [tau2-bench](https://github.com/sierra-research/tau2-bench)). Gap: original τ-bench is **single-control** (only the agent has tools). Real tech support is **dual-control**: the user also acts on a shared world. What’s new: **Telecom** Dec-POMDP where **both** agent and user have tools; compositional task generator; user-sim constrained by tools/observables; ablations separating reasoning vs **communication/coordination**. pass^k culture continues; Anthropic cites τ²: Opus 4.5 found a **policy loophole** on a flight task — failed the written eval, better for the user. Repo (2026): domains include `mock`, `airline`, `retail`, `telecom`, `banking_knowledge`; `tau2 run --num-trials`.

  `[NEEDS MORE RESEARCH]`: exact telecom pass^1 figures from τ²-bench Figure 3 — research notes cite secondary summaries (e.g. gpt-4.1 ~74% / ~56% vs ~34% telecom) and instruct to **re-read the PDF** before quoting in a lecture.

  **WebArena** — CMU, NeurIPS 2024 Oral. Paper: Zhou et al. ([arXiv:2307.13854](https://arxiv.org/abs/2307.13854)); [webarena.dev](https://webarena.dev/). Attacks oversimplified / static cached sites and evals that compared **action strings** to a reference path. Environment: self-hosted, reproducible Docker; e-commerce, social forum, GitLab, CMS, plus map/calculator/scratchpad, Wikipedia, manuals; Gym-style API; **reset** to deterministic initial state between evals. Observations: URL, tabs, screenshot, DOM, or accessibility tree; multi-tab. **812** long-horizon tasks with high-level NL intents. **Grading:** programmatic validators — **repository contents**, whether an **order was placed** (backend), URL/page predicates — allows **many valid paths**. Headline: best **GPT-4** agent **14.41%** vs **human 78.24%**; weak **active exploration** and **failure recovery**. Family: VisualWebArena, WebArena-Infinity, TheAgentCompany; newer experiments often via BrowserGym / AgentLab.

  **AgentBench** — THUDM, ICLR 2024 ([arXiv:2308.03688](https://arxiv.org/abs/2308.03688); [THUDM/AgentBench](https://github.com/THUDM/AgentBench)). Multi-dimensional eval of LLM-as-agent in **interactive, multi-turn** environments — eight environments:

  | Env | Origin | What it tests | Typical metric |
  |-----|--------|---------------|----------------|
  | **OS** | New | Ubuntu Docker bash | Success rate (SR) |
  | **DB** | New | Real SQL interfaces, multi-table | SR |
  | **KG** | New | Knowledge-graph tooling | SR / task-specific |
  | **DCG** | New | Digital card game | Reward / win |
  | **LTP** | New | Lateral thinking puzzles | SR |
  | **HH** | ALFWorld / TextWorld | Household text games | SR |
  | **WS** | WebShop | Web shopping | Reward / SR |
  | **WB** | Mind2Web (adapted) | Browse/click/type across sites | SR / F1-style |

  Findings: large gap between top **API** models and many **OSS ≤70B**; failure reasons: **long-term reasoning**, **decision-making**, **instruction following**; high-quality **multi-round alignment** data helps; **code training** has **ambivalent** effects across tasks. Curriculum use: **breadth** probe (OS vs DB vs web), not a customer-support policy test (τ-bench) and not a realistic multi-site web product test (WebArena).

  **Adjacent (Anthropic map):** SWE-bench Verified (fail-to-pass without regressions; saturation &gt;80%); Terminal-Bench (Harbor; ambiguous filepath grader bugs); OSWorld (scripts inspect files/configs/DB/UI); BrowseComp (hard web needles).

* **The Alternatives:**  

  | Choice | Pros | Cons |
  |--------|------|------|
  | **Public benchmarks** | Comparable, citable, steal graders | Saturating, contaminable, missing cost/safety/your SOP |
  | **Private domain evals** | Predictive for users | Expensive; not comparable externally |
  | **Hybrid** (syllabus) | Literacy + ship gate | Two harnesses to maintain |
  | τ-bench-style **user sim** | Tests information gathering | Sim ≠ real users; sim LLM cost; dual-control still young |
  | WebArena **self-host** | Reproducible, backend truth | Heavy Docker; 812-task runtime |
  | Action-sequence match (Mind2Web original style) | Easy | Punishes valid paths (WebArena critique) |
  | Leaderboard chasing | Hiring signal | Gaming; pass^k still rare outside τ-family |

  Use benchmarks to compare **models/harnesses**. Use **private product evals** for deployment. Google Vertex (Jan 2025): trajectory exact / in-order / any-order / precision / recall / single-tool — industrial cousin of LangSmith match modes, not a replacement for τ-bench policy+DB.

* **Failure Modes:**  
  - Without shared benchmark **literacy**, teams reinvent **text-match** evals and then discover τ-bench/WebArena already solved “grade the DB/backend.”  
  - Without **private** evals, teams overfit public sets and fail in production (your refund SOP is not GitLab issue #812).  
  - Confusing **pass@k** with **pass^k** → reporting the write agent as more reliable when you only sampled more.  
  - Pasting a WebArena or SWE-bench number on a slide; never run isolation/reset; never read a failing transcript.  
  - Claiming you “beat WebArena” as a shipping criterion.

* **Average vs. Strong Engineer:**  
  **Average:** paste a public leaderboard number; never isolate trials; never read a failing transcript.  
  **Strong:** borrow **grader patterns** (state check, functional validator, user sim, pass^k, isolated trials); run a **tiny** public slice to test the harness; invest in **20–50 private** tasks (Anthropic). Harbor for containerized tasks; Braintrust/LangSmith/Langfuse as product harnesses. **FDE bar:** explain **why** τ-bench grades DB not chat; **why** WebArena refuses action-string match; **why** AgentBench is eight-env breadth; name **pass^k** vs **pass@k**; refuse to ship on a public leaderboard alone.

* **Worked Example:**  
  **τ-bench airline (paper Figure 1):** user wants to change a basic-economy flight; **policy** may require reject + cancel/rebook instead of a naive change. Agent must use reservation APIs **and** talk. Success = **DB** matches gold, not a particular utterance.

  **WebArena:** find Pittsburgh art museums (Wikipedia), plan a route (map), update a **GitLab README**. Grader checks **repo contents**, not the click path. GPT-4 14.41% vs human 78.24%.

  **AgentBench OS:** “count files matching X outside `/home`” in Ubuntu Docker — SR. Failure often **instruction following** over many turns.

  Deployment Copilot literacy note in the interview: “We steal τ-bench’s DB-state grader and WebArena’s backend-check instinct; our ship gate is a private refund suite with pass^k on writes.”

* **Apply It:**  
  1. Read τ-bench (DB state + pass^k), WebArena (functional / backend), and AgentBench (eight envs) — literacy, not a product gate.  
  2. Steal patterns into the private suite: state check, functional validator, isolated trial reset, pass^k for writes.  
  3. Optionally run a **tiny** public slice only to validate the harness — not to claim a leaderboard win.  
  4. Keep the **private** refund/ticket suite as the ship gate; document cost/safety/SOP gaps that public benches miss.  
  5. In interviews, explain why grading chat text fails and why pass^k matters for customer-facing writes.  
  6. Do **not** block Week 15 on voice/τ³ extensions or full WebArena-Infinity migration.

---

## Week 15 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Instrument both agents:** Week 11 loop + Week 14 write on one primary tracer; structured tool-call fields; session/thread/task IDs.  
2. **Split scores:** `task_success`, `tool_name`, `tool_args`, `policy_order`, `within_step_budget`, cost/turns — never one accuracy.  
3. **Tool-call correctness:** Hamel four checks + authorization; code graders for decidable checks; LLM judge only where calibrated.  
4. **Trajectory vs outcome:** same write task with one strict/path assertion and one environment state assertion side by side.  
5. **Failure patterns:** regression fixtures for C1–C4; promote at least one real failing trace into the dataset.  
6. **Benchmark literacy:** τ-bench / WebArena / AgentBench understood; private suite remains the ship gate.

When those six steps are true, Week 15 is done in the syllabus sense: both agents are measurable, tool-call correctness is the first eval layer, and Week 16 has structured traces to mine.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-3/week-15-agent-evaluation/` (`00`–`04`, README).  
- `[NEEDS MORE RESEARCH]` markers appear where research Open Questions leave a claim ungrounded (fuzzy arg match / portable trace schema / tool-schema versioning; creative-vs-policy pass criteria / partial-credit weighting / pass^k sample size; loop classifiers / memory evals / handoff-vs-truncation class; τ²-bench telecom pass^1 figures pending PDF re-read).  
- Outside URLs from research are cited inline; operational detail was inlined from the notes.  
- No third agent is introduced; Week 16 error-analysis flywheel is explicitly deferred.
