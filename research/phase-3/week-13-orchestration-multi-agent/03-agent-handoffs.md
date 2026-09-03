# 03 — Agent handoff patterns

> Week 13 — Transfer control with valid history, not vibes  
> Research notes (raw).

---

## Fundamentals

**Handoff** (term popularized by OpenAI Swarm): transfer control via a **special tool call** (e.g. `transfer_to_refund_agent`) that updates routing state and/or navigates to another agent. The receiving agent adopts a new persona/tools; the user often continues in the **same** chat thread.

### LangChain handoffs

Official guide: [Handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs).

**Mechanism:** tools update a state variable (`current_step` / `active_agent`) that **persists across turns**; the system reads it to change behavior (prompt/tools) or to route to another agent node.

**Use when:**

- Sequential constraints (warranty ID **before** refund).  
- Multi-stage conversational flows.  
- The specialist must **talk to the user** (not just return a string to a supervisor).

**Two implementations:**

1. **Single agent + middleware** (recommended default) — one `create_agent`; `@wrap_model_call` swaps system prompt + tool palette from `current_step`. Tools return `Command(update={..., "current_step": "specialist", "messages": [ToolMessage(..., tool_call_id=...)]})`. Needs a **checkpointer** so the step survives turns.  
2. **Multiple agent subgraphs** — distinct nodes; handoff tools return `Command(goto=..., graph=Command.PARENT, update={...})`.

**Critical context rule for subgraph handoffs:** include the **AIMessage with the tool call** + a matching **ToolMessage** so history stays valid. Prefer **summarizing** in the ToolMessage, not dumping full subagent internals. Without the pair, the next model sees a dangling `tool_calls` and errors. Docs assume **no parallel tool calls** in the simple example — if the model called tools in parallel, you must complete **every** call.

**End condition:** after an agent, if the last message is an `AIMessage` **without** tool calls → `END`. Else route on `active_agent`. Initial `START` routes on `active_agent` or a default (e.g. sales).

**Design notes from the same page:**

- Context filter: full history vs filtered vs summary — **per role**.  
- **Tool semantics:** handoff tools should **not** also create tickets. Routing ≠ writes.  
- Token efficiency: as threads grow, summarization matters.

### OpenAI Agents SDK

[Handoffs](https://openai.github.io/openai-agents-python/handoffs/): first-class. Represented as tools (`transfer_to_<name>`). Pass `Agent` in `handoffs=[...]` or `handoff(agent, ...)`.

Customization:

| Knob | Role |
|------|------|
| `tool_name_override` / `tool_description_override` | What the model sees |
| `handoff_description` on Agent | Hint appended to default description |
| `on_handoff` | Callback (logging, prefetch). Runs **before** transfer completes; raise to **block** |
| `input_type` | Schema for **handoff tool args** (reason, priority) — **not** the next agent’s main input; **not** a dispatcher among destinations |
| `input_filter` | Reshape `HandoffInputData` (history) for the next agent |
| `is_enabled` | Bool or function — evaluated **before** the model picks args (cannot auth based on those args) |
| `nest_handoff_history` | Opt-in compact nested summaries (beta; disabled by default) |

`agents.extensions.handoff_filters.remove_all_tools` strips tool items so the specialist is not confused by internals. Recommended prompt prefix: `RECOMMENDED_PROMPT_PREFIX` / `prompt_with_handoff_instructions`. Guardrails: input guardrails apply to the **first** agent; output to the **last**; handoffs are not function-tool guardrails.

Prefer `Agent.as_tool` when you want a nested specialist **without** transferring the conversation (same distinction as LangChain subagents-as-tools vs peer transfer).

### Microsoft AutoGen

[Core handoffs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html): Swarm-inspired, **event-driven pub-sub**.

Customer-service topology:

- **Triage** — understand request, decide delegate.  
- **Refund** / **Sales** — domain tools.  
- **Human Agent** — first-class sink when AI cannot handle.  
- **User Agent** — customer I/O.

Protocol (events): `UserLogin`, `UserTask` (chat history), `AgentResponse` (`reply_to_topic_type` + context). **Delegate tools** publish `UserTask` to another **topic** instead of continuing generation in the same agent. Regular tools execute locally then the model is called again.

Advantages claimed vs original Swarm / AutoGen 0.2: distributed runtime, bring-your-own agent, async/UI-friendly.

[AgentChat Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html): team selects the next speaker from the latest `HandoffMessage` while sharing message context (higher-level than Core pub-sub).

### Anthropic Research

Handoffs to the **lead** use **compressed summaries**, never full subagent transcripts ([Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)). Same rule as LangChain’s “don’t dump internals.”

---

## Alternatives & Tradeoffs

| Pattern | UX | Engineering cost |
|---------|----|------------------|
| Middleware step machine | Smooth single persona morph | Careful step design; still one identity |
| Peer agent transfer (`Command.PARENT`) | Explicit “I’m transferring you” | Message pairing; `active_agent` routing |
| Supervisor always in the middle | Central policy | Extra latency **every** turn |
| Agents-as-tools (no conversation transfer) | Clean isolation | Weaker shared chat continuity |
| AutoGen topic delegate + Human Agent | Distributed; human sink | Pub-sub ops; protocol types to maintain |
| OpenAI SDK `handoff()` | First-class tools + filters | Stays in one `Runner.run`; nested history still settling |
| Human handoff | Trust | Staffing, SLA, **pause persistence** (file 04–05) |
| Full-history dump | Max context | Token burn; confusion; leakage |

Tradeoff: handoff tools that also perform side effects (create ticket **and** transfer) blur semantics and make retries unsafe. Keep **pure routing** separate from **writes**.

---

## Necessity

Without disciplined handoffs, multi-agent systems either **never** transfer (wrong specialist answers) or transfer **without** valid tool-result pairing (API/history corruption). Unbounded peer transfers create **ping-pong**. FDE customer workflows (triage → act) demand **auditable** transfers: who, when, why (`input_type.reason`), what context was passed.

Prompt-only “if needed, call transfer_*” with no state machine → infinite loops.

---

## Industry Practice

- **Common:** transfer tools with no `ToolMessage`; no transfer cap; no human sink; mixing ticket creation into `transfer_to_sales`.  
- **Senior:** explicit `active_agent` / `current_step` + end conditions (final AIMessage without tool calls → END); middleware for most cases; subgraphs only for bespoke workers; log every transfer; **cap transfers per session**; human agent as a first-class sink (AutoGen); `input_filter` / summaries; trajectory evals for handoff **edges** (Week 15); OpenAI `on_handoff` for audit metadata.

---

## Concrete Scenario

**LangChain sales ↔ support:** `transfer_to_sales` builds `[last_ai_message, ToolMessage(tool_call_id=...)]`, sets `active_agent`, `goto="sales_agent"`, `graph=Command.PARENT`. Router: if last AIMessage has no tool calls → END; else active agent. https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs  

**OpenAI:** triage → billing/refund with `input_type` `{reason, priority}` logged in `on_handoff`; FAQ agent uses `remove_all_tools` filter. https://openai.github.io/openai-agents-python/handoffs/  

**AutoGen Core:** triage/refund/sales/**human** topics; delegate tool publishes `UserTask` to refund topic. https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html  

---

## Open Questions

- Should handoff be **visible** to users always, or a silent specialist swap?  
- How do A2A task-delegation semantics map onto in-process LangGraph handoffs (Week 14)?  
- Standard handoff envelope across MCP / A2A / framework SDKs?  
- Parallel tool calls **plus** a handoff in the same turn — canonical pairing strategy?

---

## Sources

- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs  
- https://openai.github.io/openai-agents-python/handoffs/  
- https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html  
- https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html  
- https://www.anthropic.com/engineering/multi-agent-research-system  
- https://a2a-protocol.org/latest/  
