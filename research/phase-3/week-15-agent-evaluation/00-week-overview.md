# 00 — Week overview & syllabus mapping

> Week 15 — Agent evaluation: instrument both systems; tool-call correctness  
> Research notes (raw). Phase 3 week after side-effecting writes (Week 14).

---

## Fundamentals

Week 15 is the **measurement** week of Phase 3. Weeks 11–13 taught the **loop**, **MCP**, and **graphs / HITL**. Week 14 required a **second agent that mutates state**, with idempotency, confirmation, dry-run, and audit. This week does **not** add a third product. It **instruments both agentic systems** you already shipped and grades them the way production teams grade agents: **traces**, **tool-call correctness**, **trajectory vs outcome**, and a **failure-pattern vocabulary**.

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

### Both agentic systems (do not eval only one)

| System | Built in | What traces must show | First graders |
|--------|----------|------------------------|---------------|
| **Loop agent** | Week 11 (+ MCP/graph in 12–13) | Turns, tool names/args, retries, stop reason | Tool selection; schema-valid args; max-turn budget; no identical retry storms |
| **Write agent** | Week 14 | Preview vs commit, idempotency key (wrapper-owned), interrupt/approval, **read-back** | Policy order (`verify_*` / `preview_*` before `commit_*`); args (amount, ids); **DB/API state**; audit intent+result |

If only the chatbot is traced, you will “pass” Week 15 while the refund agent still double-writes. If only the write agent is traced, you miss conversational **context loss** and multi-turn resolution (Langfuse **session** scores).

### Tool-call correctness (the first eval layer)

Hamel: test **name, arguments, result, and resulting state** as **separate** checks. A valid JSON call can still be wrong if authorization/preconditions were skipped. Example: `cancel_order` + correct order id + successful HTTP + **status actually cancelled** before the user is told it worked.

LangSmith `agentevals` match modes ([trajectory evals](https://docs.langchain.com/langsmith/trajectory-evals)):

| Mode | Meaning | Use on this syllabus |
|------|---------|----------------------|
| `strict` | Same messages/tool calls in same order | `verify_identity` then `process_refund` |
| `unordered` | Same tools/args, any order | Parallel `get_weather` + `get_events` |
| `subset` | No tools beyond the reference | Efficiency / no extra payment tools |
| `superset` | At least the required tools; extras OK | Minimum required actions |

Default equality: same tool **and** same arguments (`tool_args_match_mode` / overrides). LLM-as-judge trajectories (`TRAJECTORY_ACCURACY_PROMPT`) when there is no single gold path.

Langfuse (as of July 2026): code and LLM judges see tool calls as structured `{id, name, arguments, type, index}` — **do not parse raw text**. Score `used_search_tool` (boolean) and `tool_call_count` (numeric) on the same evaluator.

Vertex AI Gen AI evaluation (public preview, Jan 2025): **final response** vs **trajectory** metrics — exact match, in-order match, any-order match, precision, recall, single-tool use ([Cloud blog](https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service)). Useful mapping table if the stack is GCP/A2A.

### What you ship this week

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

A trial can **pass outcome and fail trajectory** (refund without verify — unsafe). A trial can **pass trajectory and fail outcome** (called the right tools; DB never updated — harness/tool bug). That contrast is the teaching moment.

### What “done” looks like

1. Both agents emit traces with **structured** tool calls.  
2. CI or a notebook prints **split scores**, not a single percent.  
3. One **strict** path test and one **state** test on the same write.  
4. At least one **loop**, one **premature stop**, one **wrong-args**, one **dropped constraint** case in the dataset.  
5. You can explain τ-bench **pass^k**, WebArena **backend** checks, and AgentBench’s **eight environments** without confusing them.

---

## Alternatives & Tradeoffs

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

---

## Necessity

If Week 15 is skipped:

- Week 14 writes are “tested” by reading the assistant’s last sentence. τ-bench exists because **fluent closings ≠ DB state** ([Yao et al., arXiv:2406.12045](https://arxiv.org/abs/2406.12045)).  
- Prompt/model swaps “feel worse” with no way to tell **tool routing** from **generation**. OpenAI’s first trace-grading questions are exactly: right tool? handoff? policy? ([agent evals](https://developers.openai.com/api/docs/guides/agent-evals)).  
- Cost/latency blowups from extra tools stay invisible (Langfuse: wasteful path can still complete the task).  
- Week 16 error analysis has no traces to label; Week 17 judges have nothing calibrated.  
- FDE interviews ask for **tool-call tests** and **state checks**, not “we used LangSmith.”

---

## Industry Practice

- **Common:** screenshot of a pretty trace UI; one LLM “quality” score; no dataset version; only the demo chatbot instrumented.  
- **Strong:** 20–50 tasks from **real failures** (Anthropic); capability suite (low pass, hill to climb) vs regression suite (~100%); code + model + periodic human; **read transcripts when scores move** (Anthropic Step 6); offline CI + online sampled evaluators (Langfuse).  
- **FDE bar:** both agents on the same tracer; split scorecard; one counterexample of trajectory vs outcome disagreement; pass^k **mentioned** for customer-facing writes (τ-bench culture); public benchmarks used as **literacy**, private evals as **ship gates**.

Descript (Anthropic case): don’t break things / do what I asked / do it well; quality vs regression suites. Bolt: static analysis + browser agents + LLM judges after they already had users. Claude Code: evals added after dogfood — concision, file edits, then over-engineering.

Harrison Chase (LangChain) at AI Engineer: raise value-if-right and P(success); lower cost-if-wrong ([YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg)). Eval is how you **measure** P(success) and cost-if-wrong (unsafe tools, loops).

---

## Concrete Scenario

**Same $50 refund, two graders disagree.**

1. Agent looks up payment, calls `process_refund(amount=50)` **without** `verify_identity`. Payments table shows refunded.  
2. **Outcome grader:** pass (row exists, amount matches) — τ-bench / WebArena **backend** style.  
3. **Trajectory grader:** fail — Anthropic required `{tool: verify_identity}` then `{tool: process_refund, params: {amount: "<=100"}}`.  
4. LangSmith `strict` against a reference that includes verify → `trajectory_strict_match = false`.  
5. Langfuse `used_verify_identity = false` boolean on the tool-call observation; `task_completion` on the root may still be true.  
6. Hamel: first upstream failure is **precondition skip**, not “wrong refund amount.” Put that cell in a transition matrix: `lookup → commit` instead of `lookup → verify → commit`.

LangSmith weather example (docs): `get_weather(city="San Francisco")` with `strict` match — cheap tool-correctness unit test for the Week 11 agent.

τ-bench paper: gpt-4o-era function-calling agents **&lt;50%** tasks; **pass^8 &lt; 25%** retail — consistency, not just one lucky trial ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)).

WebArena: GPT-4 agent **14.41%** end-to-end vs human **78.24%** on 812 tasks; graders check **repository contents / orders**, not action-string match ([arXiv:2307.13854](https://arxiv.org/abs/2307.13854); [webarena.dev](https://webarena.dev/)).

---

## Open Questions

- How much argument **fuzzy-matching** (city aliases, `$50` vs `5000` cents) is safe before hiding bugs? (`tool_args_match_mode`)  
- OTel GenAI vs vendor run trees as the **portable** trace schema?  
- OpenAI Evals platform shutdown (Nov 2026) — org-standard portable format (Promptfoo vs Langfuse datasets vs Harbor)?  
- When a creative trajectory **violates written policy** but helps the user (Anthropic τ² loophole) — eval bug or product decision?  
- Ownership: platform eval team vs product-owned tasks (Anthropic: domain experts contribute PRs).

---

## Sources

- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://developers.openai.com/api/docs/guides/agent-evals  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html  
- https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-complex-multi-step-workflows.html  
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service  
- https://github.com/sierra-research/tau-bench  
- https://arxiv.org/abs/2406.12045  
- https://webarena.dev/  
- https://arxiv.org/abs/2307.13854  
- https://github.com/THUDM/AgentBench  
- https://www.youtube.com/watch?v=DZxaPNYi_k0  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
