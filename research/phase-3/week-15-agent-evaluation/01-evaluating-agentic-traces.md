# 01 — Evaluating agentic traces (tool-call correctness)

> Week 15 — Trace / transcript grading; structured tool assertions  
> Research notes (raw).

---

## Fundamentals

An **agentic trace** (Anthropic: **transcript**; also trajectory) is the complete record of one **trial**: model messages, **tool calls**, tool results, guardrails, handoffs, and intermediate state. For the Anthropic API, that is the **full messages array** across the eval run. For OpenAI, a trace is the end-to-end record of model calls, tool calls, guardrails, and handoffs for **one run** ([agent evals](https://developers.openai.com/api/docs/guides/agent-evals)).

Langfuse stresses a structural point: the unit of evaluation is a **trace** (a tree of observations: LLM calls, tools, retrievals), not a single completion. Tool-argument checks belong on **tool-call observations**; task completion belongs on the **root**. Conversational agents add a third unit: the **session** ([AI agent evaluation](https://langfuse.com/resources/engineering/ai-agent-evaluation)).

**Trace grading** answers questions final-answer grading cannot:

- Did the agent pick the **right tool** (search vs update; cancel vs refund)?  
- Were **arguments** schema-valid **and** semantically correct (business IDs, amounts, filters)?  
- Was **order** constrained when policy requires it (verify identity before refund)?  
- Did a **handoff** occur when it should (OpenAI explicit question)?  
- Were instructions / safety policies violated **mid-trajectory**?  
- Did the agent **recover** from tool errors, or hallucinate success (Hamel: error handling as its own check)?

### Methods for tool-call checks

| Method | What it checks | Notes |
|--------|----------------|-------|
| Code / deterministic assertions | Tool name present, JSON schema, exact or constrained arg values, call counts, step budget | Fast, cheap, reproducible (Anthropic code graders; Langfuse code evaluators) |
| Trajectory match (`agentevals`) | Actual vs reference tool sequence | `strict`, `unordered`, `subset`, `superset` |
| LLM-as-judge on trajectory | Reasonableness, efficiency, appropriateness without a rigid path | Needs human calibration (Hamel YouTube: treat judge as a classifier, measure TPR/TNR) |
| State / outcome checks | DB or environment after tools ran | Catches “said done, didn’t write” — file [02](02-trajectory-vs-outcome-eval.md) |
| Vertex trajectory metrics | Exact / in-order / any-order match; precision; recall; single-tool use | GCP mapping of the same ideas |

### LangSmith / AgentEvals (official docs)

Package: `pip install agentevals` / `npm install agentevals`. Factory: `create_trajectory_match_evaluator(trajectory_match_mode=...)`.

| Mode | Meaning | Use when |
|------|---------|----------|
| `strict` | Identical messages/tool calls in the **same order** (message *content* may differ) | Policy lookup before authorization |
| `unordered` | Same tool calls, **any order** | Parallel independent retrievals |
| `subset` | Agent uses **only** tools from the reference (no extras) | Scope / efficiency |
| `superset` | Agent includes **at least** the reference tools (extras OK) | Minimum required actions |

Docs example: weather agent vs reference `get_weather(city="San Francisco")` → score key `trajectory_strict_match` boolean. Unordered example: `get_events` + `get_weather` in either order. Superset: reference only requires `get_weather`; agent may also call `get_detailed_forecast`.

**Argument equality** is configurable via `tool_args_match_mode` / `tool_args_match_overrides`. Default: same tool **and** same arguments.

**LLM trajectory judge:** `create_trajectory_llm_as_judge(model=..., prompt=TRAJECTORY_ACCURACY_PROMPT)` — **no reference required**. With a reference, use `TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE` and pass `reference_outputs`. Async variants: `create_async_*`.

### Langfuse (2026 engineering guide)

Four dimensions (measure all; they fail independently):

| Dimension | Question | Typical metrics |
|-----------|----------|-----------------|
| Trajectory | Sensible path? | Step count, unnecessary calls, loops, required steps, ordering |
| Tool use | Right tools, right args? | Selection, argument validity, tool error rate, recovery |
| Task completion | User goal met? | Goal achievement, answer correctness, resolution rate |
| Multi-turn | Holds across a conversation? | Context retention, goal drift, turns-to-resolution, session outcome |

Tool calls (July 2026+): structured on the observation (`name`, `arguments`, `id`, `type`, `index`). Code evaluator example: `used_search` boolean + `tool_call_count` numeric. LLM judge can map Tool Calls via JSONPath (`$[*].name` or full array). **Swiss-cheese layers:** cheap code on every sampled trace; LLM judge on semantic subset; humans on disagreements / calibration.

Offline = datasets/experiments (CI). Online = sampled production evaluators. Loop: failing prod traces → dataset items → experiment → keep as regression.

CI: `langfuse/experiment-action@v1.0.0` + `RegressionError` on threshold; pin `dataset_version`. Target **root observation** for whole-run judges (trace-level judges are legacy).

### OpenAI workflow

1. Logs → Traces; inspect a representative run.  
2. Create a grader; run against selected traces (right tool? handoff? policy? prompt/routing change?).  
3. When “good” is known, **datasets + eval runs** for repeatability.  
4. Note: **Evals platform** deprecation announced June 2026 — read-only **31 Oct 2026**, shutdown **30 Nov 2026**; cookbook migrates portable configs to Promptfoo. **Trace-grading concepts remain**; do not build a career on the deprecated UI.

### Anthropic graders (apply to traces)

Code-based: string/regex, binary tests, static analysis, **outcome verification**, **tool-call verification** (tools used, parameters), transcript analysis (`n_turns`, `n_toolcalls`, tokens). Strengths: fast, cheap, objective. Weakness: **brittle** to valid variation.

Model-based: rubrics, NL assertions, pairwise, reference-based, multi-judge. Need **human calibration**.

Human: SME review, spot-check, IAA. Gold standard; slow.

Support-agent YAML in the post requires `verify_identity`, `process_refund` with `amount <= 100`, `send_confirmation`, `max_turns: 10`, plus **state_check** on tickets/refunds — **trace + outcome in one task**.

Anthropic instinct warning: requiring an **exact tool sequence** is **often too rigid**; frontier models find valid paths designers did not anticipate (τ²-bench flight loophole). Still use tool-call graders for **required safety steps**.

### Hamel four-way tool test

On `cancel_order`: (1) selected `cancel_order`, (2) correct order ID, (3) successful tool result, (4) **order status changed** before the user is told. Plus **authorization**. Checkpoints on “Berkeley homes under $1M + schedule viewings”: params, listings, availability, calendar invites — each can fail independently.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| Strict trajectory match | Catches policy-order bugs; deterministic CI | Punishes creative valid paths |
| Soft match (unordered / subset / superset) | Less brittle | Misses order-sensitive bugs if you picked the wrong mode |
| Args-only schema validation | Cheap safety net | Misses semantic wrong-ID (`order_id` of someone else that still parses) |
| LLM judge on tools (no reference) | Flexible | Non-deterministic; cost; uncalibrated judges lie (Hamel) |
| Outcome-only | Rewards any valid path | Hides unsafe intermediate tool use |
| Hybrid (Anthropic / Langfuse / Hamel) | Best signal | More harness complexity |
| Parse tool calls from assistant text | Works on old logs | Fragile; Langfuse explicitly says use structured fields |

**Match-mode selection is a product decision**, not a default. Refund SOP → `strict` or an explicit order assertion. Multi-source research → `unordered` + outcome. “Must call search when the question needs it” → boolean code check (Langfuse RAG-agent section: retrieval is a **tool the agent chooses**).

---

## Necessity

Without trace-level tool evaluation:

- Agents pass answer rubrics while calling **forbidden** tools (payment twice; `drop_table`).  
- Wrong arguments (amount, `customer_id`) look fine in fluent text.  
- Handoff/routing regressions appear as vague “quality feels worse” (OpenAI’s motivation for trace grading).  
- Extra tools blow **cost/latency** while task completion stays green (Langfuse independent dimensions).  
- Error analysis (Week 16) cannot find the **first upstream failure** if tools are not structured.

Hamel on complex workflows: log **LLM calls, tool usage, human approvals, and database writes** — you need that visibility to diagnose ([multi-step FAQ](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html)).

---

## Industry Practice

- **Common:** click through LangSmith/Langfuse; grep strings in the last assistant message.  
- **Strong:** structured assertions in CI (`agentevals`, Langfuse code evaluators, OpenAI graders); **separate scores** for selection, args, order, budget; promote failing prod traces into golden datasets; calibrate trajectory judges on human-labeled traces; **read transcripts** when scores move (Anthropic Step 6 — failures must look *fair*).  
- **FDE bar:** Hamel four checks on the write agent; Langfuse/OpenAI instrumentation on **both** agents; Vertex-style precision/recall as optional analytics, not the only number; balanced tests where a tool **should** and **should not** fire (Anthropic web-search over/under-trigger).

Langfuse agent graph (beta 2026): **Aggregated** mode collapses repeats (`retrieve_docs (3/3)` + cycle edges = loops); **Expanded** unrolls the DAG. Codify the property: “must not call the payment tool twice.”

---

## Concrete Scenario

**LangSmith official weather test** — https://docs.langchain.com/langsmith/trajectory-evals  

Reference trajectory includes `get_weather` with `city: San Francisco`. Evaluator `trajectory_match_mode="strict"`. This is the Week 11 agent’s unit-level analogue: **tool name + args**, not “the model said it was sunny.”

**OpenAI** — https://developers.openai.com/api/docs/guides/agent-evals — debug with traces first (right tool, handoff, policy), then datasets.

**Hamel cancel_order** — https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html — four checks including **resulting state**.

**Langfuse structured tool calls** — https://langfuse.com/resources/engineering/ai-agent-evaluation — `ctx.observation.tool_calls` / `toolCalls`; `within_step_budget` as a production boolean.

**YouTube (calibrate judges):** Hamel *How To Approach Your AI Evals* — https://www.youtube.com/watch?v=DZxaPNYi_k0 — LLM-as-judge is a classifier; measure against humans or evals lose trust.

---

## Open Questions

- Standard **cross-framework** trace schema (OTel GenAI semantic conventions) vs vendor-native trees?  
- Auto-mining **reference trajectories** from successful prod runs without overfitting to one path?  
- How to version **tool schemas** so old dataset items remain meaningful after ACI changes?  
- Observation-level vs root-level judges: teams still attach scores to the wrong span (Langfuse FAQ).  
- Fuzzy arg match: `SF` vs `San Francisco` — hide bugs or reduce flake?

---

## Sources

- https://docs.langchain.com/langsmith/trajectory-evals  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://developers.openai.com/api/docs/guides/agent-evals  
- https://developers.openai.com/api/docs/guides/evals  
- https://developers.openai.com/api/docs/deprecations  
- https://developers.openai.com/cookbook/examples/evaluation/moving-from-openai-evals-to-promptfoo  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html  
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service  
- https://www.youtube.com/watch?v=DZxaPNYi_k0  
- https://www.youtube.com/watch?v=tqUDjc1HzO4  
