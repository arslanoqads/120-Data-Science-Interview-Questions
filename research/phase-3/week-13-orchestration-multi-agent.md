# Week 13 — Orchestration & multi-agent systems

> Phase 3 — Agentic Systems  
> Raw research notes (not textbook prose). Legal sources only; no pirated books.

---

## Concept: Graph-based stateful orchestration (LangGraph-style) vs simple chains

### Fundamentals
LangGraph models agent workflows as **graphs**:

1. **State** — shared snapshot (TypedDict / dataclass / Pydantic) with **reducers** defining how updates merge.
2. **Nodes** — functions that read state, do work (LLM, tools, code), return updates.
3. **Edges** — fixed or **conditional** transitions choosing the next node(s).

Execution proceeds in Pregel-like **super-steps**: active nodes run, messages pass along channels, nodes without work halt; the graph ends when all are inactive and nothing is in transit ([Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)). Compile with `.compile(...)` to validate structure and attach checkpointers/breakpoints.

LangChain/LangGraph distinguish ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)):

- **Workflows** — predetermined code paths (prompt chaining, routing, parallelization, orchestrator–worker, evaluator–optimizer).
- **Agents** — dynamic control: the model chooses tools/next steps inside a loop.

A **simple chain** (LCEL pipe, linear `A → B → C`) is a DAG without cycles: great for fixed pipelines (retrieve → generate → format). A **stateful graph** adds cycles (agent ↔ tools), branching, fan-out/`Send`, shared memory, interrupts, and resumable persistence — i.e. production agent harness features.

`Command` from nodes can `update` state, `goto` nodes, target `Command.PARENT` from subgraphs, or `resume` after interrupts ([Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)).

### Alternatives & Tradeoffs
| Style | Best for | Weakness |
|-------|----------|----------|
| Linear chain / LCEL | Deterministic ETL-ish LLM pipelines | No native loops, HITL pause, time-travel |
| Single ReAct `while` loop (Week 11) | Few tools, short tasks | Weak branching, persistence, multi-actor |
| LangGraph StateGraph | Cyclic agents, HITL, multi-agent, deployable runs | Learning curve; recursion limits |
| AutoGen event/runtime | Distributed pub-sub agents | Different mental model; ops complexity |
| Pure workflow DSL | Compliance-heavy fixed paths | Brittle when tasks need open-ended tool use |

Tradeoff: graphs buy control and observability at the cost of more explicit state design than “just chat messages.”

### Necessity
Naive chains cannot express “call tools until done,” approval gates, or crash recovery mid-task. Without shared state + reducers, parallel nodes clobber each other’s writes. Without recursion limits, cyclic graphs loop forever (`GRAPH_RECURSION_LIMIT` is a first-class error in LangGraph troubleshooting).

### Industry Practice
- **Common:** LCEL demo chain labeled “agent.”
- **Senior:** choose workflow vs agent pattern deliberately; model state channels + reducers; set recursion limits; stream for UX; compile once, invoke with `thread_id`; use LangSmith traces to compare patterns ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)).

### Concrete Scenario
Official “Workflows and agents” guide walks prompt chaining, routing, parallelization, orchestrator–worker, evaluator–optimizer, and agent loops on LangGraph: https://docs.langchain.com/oss/python/langgraph/workflows-agents  
Graph API conceptual model (state/nodes/edges/super-steps/Command): https://docs.langchain.com/oss/python/langgraph/graph-api

### Open Questions
- When does `create_agent` hide too much graph structure for FDE debugging?
- Are enterprise “agent platforms” converging on LangGraph-like checkpoints, or on provider Agents SDKs?

### Sources
- https://docs.langchain.com/oss/python/langgraph/workflows-agents
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/overview
- https://docs.langchain.com/oss/python/langgraph/why-langgraph

---

## Concept: Single agent with many tools vs multiple specialized agents

### Fundamentals
**Single agent + many tools:** one model, one system prompt, large tool list (or tool-search deferred list). Simple topology; selection pressure is high (Week 11).

**Multiple specialized agents:** each agent has a narrow prompt + tool subset (billing, retrieval, coder). A **supervisor / router / handoff** mechanism chooses who acts. LangGraph supports this via subgraphs, supervisor patterns, or tools-that-invoke-subagents ([Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs), [Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)).

Current LangChain guidance: prefer **subagents as tools** on a main `create_agent` (`@tool` wrapping `subagent.invoke`) over the older `langgraph-supervisor` package; use custom `StateGraph` when you need static subgraph discovery, per-tier checkpoints, or shared state keys ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)).

**A2A** addresses a different axis: interoperability between **opaque agents across vendors/frameworks**, complementary to MCP tools ([A2A Protocol](https://a2a-protocol.org/latest/)).

### Alternatives & Tradeoffs
| Design | Pros | Cons |
|--------|------|------|
| Monolith agent | Easy to ship; one memory | Tool confusion; giant context; hard permissions |
| Supervisor → workers | Clear roles; parallel workers | Extra LLM hops; supervisor as SPOF |
| Peer handoffs | Natural “transfer to sales” UX | Context engineering; ping-pong loops |
| Subagents-as-tools | Simple API; isolates worker context | Less shared conversational state unless designed |
| Middleware “one agent, many configs” | Simpler than multi-graph | Still one model identity |

Tradeoff: multi-agent is not automatically smarter — it is a **context and permission partitioning** strategy. Wrong partition → handoff thrash and duplicated work.

### Necessity
Dozens of overlapping tools on one agent degrade tool choice and raise accidental high-privilege calls. Domains with different policies (PII vs public search) need separate agents/servers. Conversely, premature multi-agent adds latency and failure modes (who owns the user reply?).

### Industry Practice
- **Common:** “multi-agent” PowerPoint; actually one agent.
- **Senior:** start single-agent; split when evals show systematic tool confusion or when blast radius differs; wrap workers as tools first; escalate to subgraphs for bespoke internal graphs; measure handoff rate and loopbacks.

### Concrete Scenario
LangChain migration note: replace `create_supervisor` with `create_agent` + tool-wrapped subagents; nest tools for hierarchies; fall back to custom StateGraph for advanced checkpoint/shared-state needs: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor  
Subgraphs for multi-agent / team boundaries: https://docs.langchain.com/oss/python/langgraph/use-subgraphs  
A2A for cross-framework agent collaboration vs MCP for tools: https://a2a-protocol.org/latest/

### Open Questions
- Is “agents as tools” strictly preferable to peer handoffs for enterprise support bots?
- How should cost be attributed across supervisor + workers for customer billing?

### Sources
- https://docs.langchain.com/oss/python/migrate/langgraph-supervisor
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- https://a2a-protocol.org/latest/

---

## Concept: Agent handoff patterns

### Fundamentals
**Handoff** (term popularized by OpenAI Swarm): transfer control via a **special tool call** (e.g. `transfer_to_sales_agent`) that updates routing state and/or navigates to another agent. The receiving agent adopts a new persona/tools; the user often continues in the same chat thread.

**LangChain handoffs docs** ([Handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)):

- Core idea: tools update a state variable (`current_step` / `active_agent`); system reads it to change behavior.
- Use when: sequential constraints, multi-stage conversational flows, direct user interaction across stages (e.g. warranty ID before refund).
- Two implementations:
  1. **Single agent + middleware** — one agent; middleware swaps system prompt/tools per `current_step` (recommended default).
  2. **Multiple agent subgraphs** — distinct nodes; handoff tools return `Command(goto=..., graph=Command.PARENT, update=...)`.

**Critical context rule for subgraph handoffs:** include the **AIMessage with the tool call** + a matching **ToolMessage** so history stays valid; prefer **not** dumping full subagent internals (confusion + tokens). Summarize in the ToolMessage if needed.

**Microsoft AutoGen** implements handoffs as event-driven pub-sub: triage/refund/sales/human agents; delegate tools publish `UserTask` to another topic; scales to distributed runtime ([AutoGen handoffs](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/handoffs.html)).

**OpenAI Agents SDK** also treats handoffs as a first-class transfer (alongside “agents as tools”) — see Agents SDK tools docs for the distinction ([Agents SDK tools](https://openai.github.io/openai-agents-python/tools/)).

### Alternatives & Tradeoffs
| Pattern | UX | Engineering cost |
|---------|----|------------------|
| Middleware step machine | Smooth single persona morph | Careful step design |
| Peer agent transfer | Explicit “I’m transferring you” | Message pairing, active_agent routing |
| Supervisor always in the middle | Central policy | Extra latency every turn |
| Human handoff | Trust | Staffing, SLA, pause persistence |

Tradeoff: handoff tools that also perform side effects (create ticket + transfer) blur semantics — LangChain advises clarifying pure routing vs actions with side effects.

### Necessity
Without disciplined handoffs, multi-agent systems either never transfer (wrong specialist answers) or transfer without valid tool-result pairing (API/history corruption). Unbounded peer transfers create agent ping-pong.

### Industry Practice
- **Common:** prompt “if needed, call transfer_*” with no state machine; infinite loops.
- **Senior:** explicit `active_agent` + end conditions (AIMessage without tool calls → END); middleware for most cases; subgraphs only for bespoke workers; log every transfer; cap transfers per session; human agent as a first-class sink (AutoGen pattern).

### Concrete Scenario
LangChain sales ↔ support handoff example with `Command.PARENT`, `transfer_to_sales` / `transfer_to_support`, and routing on `active_agent`: https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs  
AutoGen Core handoffs notebook (triage/refund/sales/human, Swarm-inspired): https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/handoffs.html

### Open Questions
- Should handoff be visible to users always, or silent specialist swap?
- How do A2A task delegation semantics map onto in-process LangGraph handoffs?

### Sources
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/handoffs.html
- https://openai.github.io/openai-agents-python/tools/
- https://a2a-protocol.org/latest/

---

## Concept: Persistence and resumable state

### Fundamentals
LangGraph persistence ([Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)):

| System | Persists | Scope | Use |
|--------|----------|-------|-----|
| **Checkpointer** | Graph state snapshots (checkpoints) | Single **thread** (`thread_id`) | Conversation continuity, HITL, time travel, fault tolerance |
| **Store** | App-defined key-value | Cross-thread | User preferences, facts, shared knowledge |

Compile: `builder.compile(checkpointer=..., store=...)`. Invoke with `{"configurable": {"thread_id": "..."}}`. Same `thread_id` resumes; new id starts empty.

Production notes from docs:

- `InMemorySaver` / `MemorySaver` **lost on process restart** — use `PostgresSaver` (or durable equivalent) / `SqliteSaver` for dev.
- Checkpoints can **grow unboundedly** — prune/retain.
- `thread_id` length limits on Postgres (<255 chars).
- Subgraphs may have separate checkpoint namespaces — parent may not see child updates; use Store or shared channels carefully.
- Agent Server can manage persistence for you.

Resumability enables: multi-day conversations, crash recovery mid-graph, and HITL waits without holding a hot worker.

### Alternatives & Tradeoffs
| Approach | Pros | Cons |
|----------|------|------|
| No persistence | Simple scripts | No resume/HITL/time travel |
| In-memory checkpointer | Fast local | Dies with process |
| Postgres checkpointer | Multi-instance workers | Ops + retention policy |
| External session DB only | Familiar | Reimplement graph cursor semantics |
| Provider conversation state (`previous_response_id`) | Less infra | Tied to vendor; weaker custom graph control |

Tradeoff: durable checkpoints are required for serious HITL; they are **not** a full audit log of who approved what (application must add that).

### Necessity
Without checkpoints, interrupts cannot wait hours; deploys kill in-flight agents; you cannot time-travel debug. Without stores, every thread re-learns user preferences.

### Industry Practice
- **Common:** MemorySaver in notebooks; surprise empty state in prod.
- **Senior:** Postgres/Redis-backed checkpointer; stable `thread_id` strategy (user×session); TTL/prune job; separate Store for long-term memory; test resume after kill -9; document subgraph checkpoint namespaces.

### Concrete Scenario
Official persistence quickstart + checkpointer vs store table + production troubleshooting (MemorySaver loss, unbounded checkpoints, thread_id length): https://docs.langchain.com/oss/python/langgraph/persistence  
Interrupt docs: pause persists via checkpointer; resume with same `thread_id` + `Command(resume=...)`: https://docs.langchain.com/oss/python/langgraph/interrupts

### Open Questions
- What retention/PII policy applies to full graph checkpoints in regulated industries?
- How to migrate checkpoint schemas when node names/state keys change (graph migrations)?

### Sources
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/add-memory
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs

---

## Concept: Human-in-the-loop checkpoints

### Fundamentals
**Human-in-the-loop (HITL)** pauses automated execution for approval, edits, or extra input — critical when models can take irreversible actions.

LangGraph **interrupts** ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)):

- Call `interrupt(payload)` inside a node (JSON-serializable payload surfaced to caller).
- Requires a **checkpointer** + `thread_id`.
- Graph saves state and waits **indefinitely** (no compute burn while waiting).
- Resume: re-invoke with **same** `thread_id` and `Command(resume=value)`; that value becomes the return of `interrupt()`.
- **Node restarts from the beginning** on resume → keep code **before** `interrupt` side-effect-free / idempotent.
- Patterns: approve/reject critical actions; review/edit LLM or tool calls; validate human input; multiple interrupts with paired IDs.
- Prefer dynamic `interrupt()` over only static `interrupt_before`/`interrupt_after` breakpoints when logic is conditional.

AutoGen handoffs include a **Human Agent** topic for escalations the AI agents cannot handle ([AutoGen handoffs](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/handoffs.html)).

MCP **elicitation** is a related primitive (server asks client/user for input) at the protocol layer (Week 12) — complementary when the tool server needs a human, not the graph.

### Alternatives & Tradeoffs
| Mechanism | Fit | Caveat |
|-----------|-----|--------|
| LangGraph `interrupt()` | Graph-native pause/resume | Needs durable checkpointer; node replay semantics |
| Static breakpoints at compile | Simple always-pause nodes | Less flexible than conditional interrupt |
| Approve inside tool `run()` | Works with SDK tool runners | Easy to forget persistence across process restarts |
| Out-of-band ticket queue | Familiar ops | Must wire resume idempotently |
| Always-on human | Safest | Not scalable |

Tradeoff: too many interrupts destroy automation ROI; too few create blast-radius incidents.

### Necessity
Money movement, emails to customers, prod DB writes, and medical/legal advice without HITL are unacceptable risk. HITL without persistence forces the HTTP request to stay open — unusable for async human SLAs.

### Industry Practice
- **Common:** `input()` in a CLI demo called “HITL.”
- **Senior:** risk-based interrupts (threshold routing); durable checkpointer; UI shows interrupt payload; timeouts/escalation if no human responds; audit who approved; idempotent nodes; test kill-and-resume; combine with tool allowlists.

### Concrete Scenario
LangGraph interrupts guide — `interrupt("Do you approve this action?")`, stream `stream.interrupted` / `stream.interrupts`, resume with `Command(resume=True)` on the same thread: https://docs.langchain.com/oss/python/langgraph/interrupts  
Supervisor migration notes that `interrupt` inside tool-wrapped subagents propagates to the outermost graph and still resumes with `Command(resume=...)`: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor

### Open Questions
- Should approval UIs be host-native (Agent Server) or customer IAM ticketing?
- How to prevent “rubber-stamp” fatigue when interrupt volume is high?

### Sources
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/migrate/langgraph-supervisor
- https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/handoffs.html

---

## Week 13 cross-cutting sources

- LangGraph workflows & agents: https://docs.langchain.com/oss/python/langgraph/workflows-agents  
- LangGraph graph API: https://docs.langchain.com/oss/python/langgraph/graph-api  
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence  
- LangGraph interrupts (HITL): https://docs.langchain.com/oss/python/langgraph/interrupts  
- LangGraph subgraphs: https://docs.langchain.com/oss/python/langgraph/use-subgraphs  
- LangChain multi-agent handoffs: https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs  
- Migrate from langgraph-supervisor: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor  
- Microsoft AutoGen handoffs: https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/handoffs.html  
- Google/Linux Foundation A2A: https://a2a-protocol.org/latest/  
- AI Engineer YouTube (orchestration talks ecosystem): https://www.youtube.com/@aidotengineer  
- AI Engineer Europe multi-agent + MCP workshop: https://www.youtube.com/watch?v=mYSRn6PC1mc  
