# 05 — Stopping conditions and loop-limit guardrails

> Week 11 — Agent fundamentals  
> Research notes (raw).

---

## Fundamentals

**Stopping conditions** are the rules that **end** the agent loop. The model’s “I’m done” is **one** of them, not the only one. Production systems use **defense in depth**: semantic stop **and** hard caps.

### Taxonomy (use these names in logs)

| Kind | Signal | Who owns it |
|------|--------|-------------|
| **Model-natural stop** | OpenAI: assistant message with no further `function_call`. Anthropic: `stop_reason` **other than** `tool_use` (e.g. `end_turn`, `refusal`, `stop_sequence`). | Provider + your branch on the enum |
| **Truncation** | `max_tokens` / `max_output_tokens` mid-text or **mid-tool-call JSON** | You must **not** treat as success; resume, error-result, or “answer without tools” (zoom cookbook) |
| **Iteration cap** | Anthropic tool runner `max_iterations`; cookbook defaults like **20**; Agents SDK run `max_turns` (framework-specific) | Application |
| **Graph recursion limit** | LangGraph `recursion_limit` → `GraphRecursionError`; counts **super-steps**, not “tool calls” | Runtime |
| **Proactive step budget** | LangGraph `RemainingSteps` managed value; `config["metadata"]["langgraph_step"]` | Graph logic routes to `END` **before** throw |
| **Resource budgets** | Max tokens in, max $, wall-clock, max invocations **per tool** (`max_uses` on some Anthropic server tools; web_search `max_uses_exceeded`) | Application + provider |
| **Policy / product** | User cancel, safety classifier, approval rejected, authz deny | Product |
| **Goal predicate** | Structured “done” schema; verifier says pass; `tool_use_behavior: stop_on_first_tool` / `StopAtTools` | Application |
| **Circuit break** | Repeated identical tool+args+error (file 04) | Application |
| **Forced tool trap** | `tool_choice` stuck on required/named (file 01) — stop is **never** natural until reset | Framework default vs your bug |

### OpenAI

Docs: continue the tool-calling flow **as long as the task requires** — implying **you** decide when to stop requesting ([Function calling](https://developers.openai.com/api/docs/guides/function-calling)). Agents SDK: `tool_use_behavior` can **stop the run** on first tool or on named tools (output becomes final without another model round). `reset_tool_choice` exists specifically so forced tool use does not **diverge**. There is no substitute for an application **turn counter** on a raw Responses loop.

### Anthropic

Tool runner: loops until Claude returns **without** tool use, **or** `max_iterations`; you may `break` while iterating messages ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)). All seven SDKs support `max_iterations`. Zoom cookbook uses `max_iterations=20` as a runaway guard ([Zoom cookbook](https://platform.claude.com/cookbook/multimodal-crop-tool)). Handle `max_tokens` as a **first-class stop**, especially if a `tool_use` block is incomplete.

### LangGraph (required citation for this week)

[Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api):

- `recursion_limit` = max **super-steps** per execution.  
- Exceeded → `GraphRecursionError`.  
- **Starting 1.0.6, default is 1000.** Pass `recursion_limit` on `invoke`/`stream` as a **top-level config key**, **not** inside `configurable`.  
- Step counter: `config["metadata"]["langgraph_step"]`.  
- **`RemainingSteps`**: managed value for **proactive** routing to a wrap-up / `END` node before the throw.

[GRAPH_RECURSION_LIMIT](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT): often an **infinite cycle** (a→b→a) *or* a legitimately deep graph hitting the default. Troubleshooting: fix the cycle **or** raise the limit if you expected many iterations.

[Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api): loops **require** a termination condition (conditional edge to `END`); recursion limit is the backstop; catch `GraphRecursionError`; extended example returns state using remaining-steps instead of throwing. Super-steps ≠ node count when parallel branches run in one step.

**Do not copy “default 25” from old blog posts** without checking your version. **Do** set the limit **explicitly** per agent profile (support bot 15, research agent 80).

Functional API quickstart `while True` **without** a cap is the naive loop (file 01) wearing official clothes — wrap it with a counter or compile through the graph runtime’s limit.

### What to emit to the UI

Never silently 504. Emit structured:

```text
AgentStopped
  reason: max_iterations | recursion_limit | max_tokens | budget_usd | deadline | policy_deny | user_cancel | end_turn | refusal | circuit_break
  turn: 12
  last_tools: [docs_search]
  user_message: "I hit my step limit while searching docs. Partial findings: …"
```

Near-limit prompts (“wrap up in the next answer, no more tools”) are a **soft** guard; hard caps still fire.

Read-only vs mutating: **separate** remaining quotas (100 searches vs 3 creates).

---

## Alternatives & Tradeoffs

| Guardrail | Strength | Weakness |
|-----------|----------|----------|
| `max_iterations` / `max_turns` only | Simple; matches tool runner | Stops mid-task; need a user-facing fallback |
| Token / $ budget | Aligns with billing | Hard to estimate per task; streaming complicates |
| Wall-clock deadline | UX-friendly | Flaky under load; doesn’t stop a stuck tool without timeouts (file 04) |
| Structured DONE / stop tool | Clear semantic end | Model claims done early (`StopAtTools` can be abused) |
| Recursion limit (graphs) | Handles cycles | Super-step ≠ LLM call; parallel branches change the math |
| `RemainingSteps` wrap-up node | Graceful degradation | You must implement the wrap-up prompt |
| Catch `GraphRecursionError` only | Easy | **Reactive** — user sees a crash unless you translate it |
| Tight caps | Protect spend | More “I ran out of steps” |
| Loose caps | Completes long tasks | Runaway agents |

Chase (AI Engineer): enterprise agents need **reviewable, reversible** work. A stop that dumps a stack trace is high **cost if wrong**. A stop that returns **partial artifacts + reason** is low cost.

---

## Necessity

- Unlimited loops = **cost, rate limits, stuck workers** (production incident).  
- Caps without **user-visible fallback** = silent failure / infinite spinner.  
- Ignoring `max_tokens` truncated tool JSON = corrupted state / illegal next request.  
- Raising LangGraph `recursion_limit` to “fix” a cycle = **paying for a bug**.  
- `tool_choice=required` without reset = **infinite paid loop**.  
- Week 13 HITL: interrupt is another stop; if Week 11 has no taxonomy, HITL looks like a hang.  
- Interview: “how do you stop an agent?” answered with “the model stops” is a reject.

---

## Industry Practice

- **Common:** infinite loop until client timeout (504); or LangGraph default whatever-the-version-is; no `AgentStopped`.  
- **Senior:**  
  - Configurable caps **per agent profile**.  
  - Typed stop reason to UI **and** traces.  
  - Near-limit wrap-up turn.  
  - Separate limits for read-only vs mutating tools.  
  - Proactive `RemainingSteps` on graphs; don’t rely on except-only.  
  - Combine with HITL for high-impact actions (Week 13).  
  - Dashboards: `stop_reason` distribution (if 40% are `max_iterations`, the agent is under-tooled or under-capped).  
- **FDE bar:** quote tool runner `max_iterations`, OpenAI “as many as the task requires” as **your** responsibility, LangGraph 1.0.6 default **1000** + explicit config, `RemainingSteps` vs `GraphRecursionError`.

---

## Concrete Scenario

**Anthropic Tool Runner:** loops until no tool use **or** `max_iterations`; early `break`: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner  

**Zoom cookbook:** `max_iterations=20` + token-capped turn handling: https://platform.claude.com/cookbook/multimodal-crop-tool  

**OpenAI:** application-owned continue-or-stop: https://developers.openai.com/api/docs/guides/function-calling  

**LangGraph:**

- Set limit: `graph.invoke(inputs, config={"recursion_limit": 5})` — https://docs.langchain.com/oss/python/langgraph/graph-api  
- Error reference: https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT  
- Loops + catch `GraphRecursionError` + remaining-steps wrap-up: https://docs.langchain.com/oss/python/langgraph/use-graph-api  

**Week 11 lab:**

1. Task that needs ~4 tool turns (docs → SQL → list calendar → final). Cap `max_iterations=3` → expect `AgentStopped(max_iterations)` **with** a partial summary, not an exception.  
2. Same task, cap 12 → `end_turn`.  
3. LangGraph: two-node cycle **without** `should_continue` to `END` → `GraphRecursionError`; then add `RemainingSteps < 3 → wrap_up`.  
4. Truncation drill: set tiny `max_tokens` on a tool-call turn; assert you **do not** execute half-parsed args.

**Talk:** Harrison Chase, *3 ingredients for building reliable enterprise agents* (control flow + observability so stops are reviewable): https://www.youtube.com/watch?v=kTnfJszFxCg — https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  

---

## Open Questions

- Should stop reasons be **standardized** across providers for observability platforms (OpenTelemetry gen-AI semantic conventions)?  
- Is “budget left” something the model should see as an observation to plan within limits, or does that distort tool choice?  
- Super-step vs LLM-call vs tool-call: which counter should product SLAs use?  
- For hosted server tools that loop internally, how should **your** `max_iterations` count?

---

## Sources

- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
- https://platform.claude.com/cookbook/multimodal-crop-tool  
- https://developers.openai.com/api/docs/guides/function-calling  
- https://openai.github.io/openai-agents-python/agents/  
- https://docs.langchain.com/oss/python/langgraph/graph-api  
- https://docs.langchain.com/oss/python/langgraph/use-graph-api  
- https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT  
- https://docs.langchain.com/oss/python/langgraph/quickstart  
- https://arxiv.org/abs/2210.03629  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://www.youtube.com/@aidotengineer  
