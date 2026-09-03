# Week 13 — Orchestration frameworks and multi-agent design

> Phase 3 — Agentic Systems  
> Raw research notes (not textbook prose). Legal sources only; no pirated books.

---

## Concept: Graph-based stateful orchestration (LangGraph-style vs simple chains)

### Fundamentals
LangGraph models agent workflows as **graphs**:

1. **State** — shared snapshot (TypedDict / Pydantic) with **reducers** defining how concurrent updates merge.
2. **Nodes** — functions that read state, do work (LLM, tools, code), return updates.
3. **Edges** — fixed or **conditional** transitions choosing the next node(s).

Execution proceeds in Pregel-like **super-steps**: scheduled nodes run (possibly in parallel), updates merge, then the next step schedules. The run ends when nothing remains to execute ([Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)). Compile with `.compile(...)` to validate structure and attach checkpointers / interrupts.

LangGraph / Anthropic both distinguish:

- **Workflows** — predetermined code paths (prompt chaining, routing, parallelization, orchestrator–worker, evaluator–optimizer).
- **Agents** — the model dynamically chooses tools / next steps inside a loop ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents); [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

A **simple chain** (LCEL pipe, linear `A → B → C`) is a DAG without cycles: great for fixed pipelines (retrieve → generate → format). A **stateful graph** adds cycles (agent ↔ tools), branching, fan-out/`Send`, shared memory, interrupts, and resumable persistence — i.e. production agent harness features. `Command` from nodes can `update` state, `goto` nodes, target parent graphs from subgraphs, or `resume` after interrupts.

### Alternatives & Tradeoffs
| Style | Best for | Weakness |
|-------|----------|----------|
| Linear chain / LCEL | Deterministic ETL-ish LLM pipelines | No native loops, HITL pause, time-travel |
| Single ReAct `while` loop (Week 11) | Few tools, short tasks | Weak branching, persistence, multi-actor |
| LangGraph StateGraph | Cyclic agents, HITL, multi-agent, deployable runs | Learning curve; recursion limits |
| AutoGen event/runtime | Distributed pub-sub agents | Different mental model; ops complexity |
| CrewAI crews/processes | Fast role-based prototypes | Weaker production persistence/HITL story — use cautiously |
| Workflow engines (Temporal, Prefect) | Multi-day business durability | Heavier; LLM-specific patterns less native |

Anthropic warns frameworks obscure prompts/tool IO — start with API loops; add graphs when measured value requires them ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

### Necessity
Naive chains cannot express “call tools until done,” approval gates, or crash recovery mid-task. Without shared state + reducers, parallel nodes clobber each other’s writes. Without recursion limits, cyclic graphs loop forever. Production incidents often look like “it just hung” because control flow lived only in prompt text.

### Industry Practice
- **Common:** LCEL demo chain labeled “agent”; recursion limit unset.
- **Senior:** choose workflow vs agent deliberately; typed state + reducers; set recursion limits; stream for UX; compile once, invoke with `thread_id`; LangSmith / equivalent traces per node; subgraphs for specialized skills.

### Concrete Scenario
Harrison Chase (LangChain) at AI Engineer — “3 ingredients for building reliable enterprise agents” — argues enterprise agents succeed by combining high-value longer-running work, a middle ground of autonomy + deterministic workflows via LangGraph, and observability/evals, with reversible actions and human correction: https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  

Official “Workflows and agents” walkthrough (chaining → routing → parallelization → orchestrator–worker → evaluator–optimizer → agent loops): https://docs.langchain.com/oss/python/langgraph/workflows-agents  
Graph API (state/nodes/edges/super-steps/`Command`): https://docs.langchain.com/oss/python/langgraph/graph-api

### Open Questions
- When does `create_agent` hide too much graph structure for FDE debugging?
- Will MCP + host runtimes shrink app-level graphs, or will graphs wrap MCP tools?
- Graph DSL vs code-defined graphs for enterprise change control?

### Sources
- https://docs.langchain.com/oss/python/langgraph/workflows-agents
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/overview
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://www.anthropic.com/engineering/building-effective-agents
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents

---

## Concept: Single agent with many tools vs multiple specialized agents

### Fundamentals
**Single agent + many tools:** one model, one system prompt, large tool list (or deferred tool-search). Simple topology; selection pressure is high (Week 11).

**Multiple specialized agents:** each agent has a narrow prompt + tool subset (billing, retrieval, coder). A **supervisor / router / handoff** chooses who acts. LangGraph supports this via subgraphs, supervisor patterns, or tools-that-invoke-subagents ([Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs), [Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)). Current LangChain guidance prefers **subagents as tools** on a main `create_agent` over the older `langgraph-supervisor` package; use custom `StateGraph` when you need static subgraph discovery, per-tier checkpoints, or shared state keys.

**Anthropic production lesson:** Research uses an **orchestrator–worker** design (lead agent + parallel specialized subagents). Token use ran ~**15×** a chat interaction; multi-agent wins when breadth/parallel exploration beats a single context, but **detailed task briefs** are mandatory — vague “research X” caused duplicate searches and gaps ([How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)). Follow-up: multi-agent helps for **context pollution**, **parallelizable work**, and **specialization**; otherwise coordination cost dominates ([When to use multi-agent systems](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)). Decompose by **context boundaries**, not arbitrary “researcher vs writer” labels.

**CrewAI (use cautiously):** `Crew` = agents + tasks + process (`sequential` / hierarchical manager). Convenient role/backstory/goal metaphors; treat as a **prototyping layer** — verify persistence, evals, and side-effect controls yourself before enterprise writes ([Crews](https://docs.crewai.com/en/concepts/crews)).

**A2A** is a different axis: interoperability between opaque agents across vendors/frameworks, complementary to MCP tools ([A2A Protocol](https://a2a-protocol.org/latest/)).

### Alternatives & Tradeoffs
| Design | Pros | Cons |
|--------|------|------|
| Monolith agent | Easy to ship; one memory | Tool confusion; giant context; hard permissions |
| Supervisor → workers | Clear roles; parallel workers | Extra LLM hops; cost multiplier; supervisor SPOF |
| Peer handoffs | Natural “transfer to sales” UX | Context engineering; ping-pong loops |
| Subagents-as-tools | Simple API; isolates worker context | Less shared conversational state unless designed |
| Middleware “one agent, many configs” | Simpler than multi-graph | Still one model identity |
| CrewAI sequential/hierarchical crew | Fast demos; role clarity | Ops/HITL/idempotency not solved for you |

Tradeoff: multi-agent is **context and permission partitioning**, not automatic intelligence. Wrong partition → handoff thrash and duplicated work.

### Necessity
Dozens of overlapping tools on one agent degrade tool choice and raise accidental high-privilege calls. Domains with different policies (PII vs public search) need separate agents/servers. Premature multi-agent adds latency, token burn, and “who owns the user reply?” ambiguity.

### Industry Practice
- **Common:** “multi-agent” slide deck; actually one agent; or CrewAI demo with no evals.
- **Senior:** start single-agent; split when evals show systematic tool confusion, context pollution, or blast-radius differences; wrap workers as tools first; escalate to subgraphs for bespoke graphs; measure handoff rate, loopbacks, and $/task vs single-agent baseline (Anthropic’s 15× research cost is a warning, not a goal).

### Concrete Scenario
Anthropic Research: lead agent plans, spawns 3–5 parallel subagents with explicit objectives/tools/boundaries, synthesizes compressed summaries — parallelization cut complex research wall-clock by up to ~90% in their write-up: https://www.anthropic.com/engineering/multi-agent-research-system  
When *not* to multi-agent: https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them  
LangChain: `create_agent` + tool-wrapped subagents: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor

### Open Questions
- Is “agents as tools” strictly preferable to peer handoffs for enterprise support bots?
- How should cost be attributed across supervisor + workers for customer billing?
- Can verification-only subagents pay for themselves on every write path?

### Sources
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them
- https://www.anthropic.com/engineering/building-effective-agents
- https://docs.langchain.com/oss/python/migrate/langgraph-supervisor
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs
- https://docs.crewai.com/en/concepts/crews
- https://a2a-protocol.org/latest/

---

## Concept: Agent handoff patterns

### Fundamentals
**Handoff** (term popularized by OpenAI Swarm): transfer control via a **special tool call** (e.g. `transfer_to_refund_agent`) that updates routing state and/or navigates to another agent. The receiving agent adopts a new persona/tools; the user often continues in the same chat thread.

**LangChain handoffs** ([Handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)):

- Tools update a state variable (`current_step` / `active_agent`); the system reads it to change behavior.
- Use when: sequential constraints, multi-stage conversational flows, direct user interaction across stages (e.g. warranty ID before refund).
- Two implementations:
  1. **Single agent + middleware** — one agent; middleware swaps system prompt/tools per step (recommended default).
  2. **Multiple agent subgraphs** — distinct nodes; handoff tools return `Command(goto=..., graph=Command.PARENT, update=...)`.
- Critical context rule for subgraph handoffs: include the **AIMessage with the tool call** + a matching **ToolMessage** so history stays valid; prefer summarizing, not dumping full subagent internals.

**OpenAI Agents SDK:** handoffs are first-class — represented as tools (`transfer_to_<name>`); optional `input_type` for metadata (reason, priority); `input_filter` to reshape history the next agent sees; `on_handoff` callbacks ([Handoffs](https://openai.github.io/openai-agents-python/handoffs/)).

**Microsoft AutoGen:** handoffs as event-driven pub-sub — triage/refund/sales/human agents; **delegate tools** publish `UserTask` to another topic instead of continuing generation in the same agent; Swarm team selects the next speaker from the latest `HandoffMessage` while sharing message context ([AutoGen handoffs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html), [Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html)).

Anthropic Research handoffs use **compressed summaries**, never full subagent transcripts, to keep the lead’s context for planning/synthesis ([Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)).

### Alternatives & Tradeoffs
| Pattern | UX | Engineering cost |
|---------|----|------------------|
| Middleware step machine | Smooth single persona morph | Careful step design |
| Peer agent transfer | Explicit “I’m transferring you” | Message pairing; active_agent routing |
| Supervisor always in the middle | Central policy | Extra latency every turn |
| Agents-as-tools (no conversation transfer) | Clean isolation | Weaker shared chat continuity |
| Human handoff | Trust | Staffing, SLA, pause persistence |
| Full-history dump | Max context | Token burn; confusion; leakage |

Tradeoff: handoff tools that also perform side effects (create ticket + transfer) blur semantics — keep pure routing tools separate from write tools.

### Necessity
Without disciplined handoffs, multi-agent systems either never transfer (wrong specialist answers) or transfer without valid tool-result pairing (API/history corruption). Unbounded peer transfers create agent ping-pong. FDE customer workflows (triage → act) demand auditable transfers.

### Industry Practice
- **Common:** prompt “if needed, call transfer_*” with no state machine; infinite loops.
- **Senior:** explicit `active_agent` + end conditions (final AIMessage without tool calls → END); middleware for most cases; subgraphs only for bespoke workers; log every transfer; cap transfers per session; human agent as a first-class sink (AutoGen pattern); filter tool internals on handoff; trajectory evals for handoff edges.

### Concrete Scenario
LangChain sales ↔ support handoff with `Command.PARENT` and routing on `active_agent`: https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs  
OpenAI Agents SDK handoff customization (`input_type`, filters, recommended prompt prefix): https://openai.github.io/openai-agents-python/handoffs/  
AutoGen Core handoffs (triage/refund/sales/human, Swarm-inspired): https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html

### Open Questions
- Should handoff be visible to users always, or silent specialist swap?
- How do A2A task delegation semantics map onto in-process LangGraph handoffs?
- Standard handoff envelope across MCP / A2A / framework SDKs?

### Sources
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- https://openai.github.io/openai-agents-python/handoffs/
- https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html
- https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://a2a-protocol.org/latest/

---

## Concept: Persistence and resumable state

### Fundamentals
LangGraph persistence ([Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)):

| System | Persists | Scope | Use |
|--------|----------|-------|-----|
| **Checkpointer** | Graph state snapshots (checkpoints) | Single **thread** (`thread_id`) | Conversation continuity, HITL, time travel, fault tolerance |
| **Store** | App-defined key-value | Cross-thread | User preferences, facts, shared knowledge |

Compile: `builder.compile(checkpointer=..., store=...)`. Invoke with `{"configurable": {"thread_id": "..."}}`. Same `thread_id` resumes; new id starts empty. Checkpoints are written at **super-step** boundaries; per-task writes enable pending-write recovery when a sibling node in the same step fails ([Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)).

Production notes from docs:

- `InMemorySaver` / `MemorySaver` **lost on process restart** — use `PostgresSaver` / `SqliteSaver` for durability.
- Checkpoints can **grow unboundedly** — prune/retain.
- Postgres `thread_id` length limits (<255 chars).
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
| Provider conversation state | Less infra | Vendor lock; weaker custom graph control |
| Temporal/Prefect for durability | Battle-tested long jobs | Dual orchestration brains |

Tradeoff: durable checkpoints are required for serious HITL; they are **not** a full audit log of who approved what (application must add that).

### Necessity
Cloud instance death mid-tool-call without checkpoint → duplicate side effects or abandoned customer tickets. Without stores, every thread re-learns preferences. Interview signal: can you resume an interrupted approval flow after a deploy?

### Industry Practice
- **Common:** MemorySaver in notebooks; surprise empty state in prod.
- **Senior:** Postgres-backed checkpointer behind a pool; stable `thread_id` strategy (user×session); TTL/prune job; separate Store for long-term memory; serialize concurrent invokes per `thread_id`; test resume after kill -9; document subgraph checkpoint namespaces.

### Concrete Scenario
Official persistence quickstart + checkpointer vs store + production troubleshooting (MemorySaver loss, unbounded checkpoints, thread_id length): https://docs.langchain.com/oss/python/langgraph/persistence  
Checkpointers conceptual guide (HITL, time travel, fault tolerance, super-step snapshots): https://docs.langchain.com/oss/python/langgraph/checkpointers  
Interrupts: pause persists via checkpointer; resume with same `thread_id` + `Command(resume=...)`: https://docs.langchain.com/oss/python/langgraph/interrupts

### Open Questions
- What retention/PII policy applies to full graph checkpoints in regulated industries?
- How to migrate checkpoint schemas when node names/state keys change?
- How fine-grained should super-steps be for cost vs resume fidelity?

### Sources
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/checkpointers
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs

---

## Concept: Human-in-the-loop checkpoints

### Fundamentals
**Human-in-the-loop (HITL)** pauses automated execution for approval, edits, or extra input — critical when models can take irreversible actions.

LangGraph **interrupts** ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts); [LangChain blog](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)):

- Call `interrupt(payload)` inside a node (JSON-serializable payload surfaced to caller).
- Requires a **checkpointer** + `thread_id`.
- Graph saves state and waits **indefinitely** (no compute burn while waiting).
- Resume: re-invoke with **same** `thread_id` and `Command(resume=value)`; that value becomes the return of `interrupt()`.
- **Node restarts from the beginning** on resume → keep code **before** `interrupt` side-effect-free / idempotent.
- Patterns: approve/reject critical actions; review/edit LLM or tool args; validate human input; multiple interrupts with paired IDs.
- Prefer dynamic `interrupt()` over only static `interrupt_before`/`interrupt_after` when logic is conditional — and never put irreversible side effects before the pause if using `interrupt_after` semantics.

AutoGen handoffs include a **Human Agent** topic for escalations AI agents cannot handle ([AutoGen handoffs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html)). MCP **elicitation** (Week 12) is complementary when a *tool server* needs human input, not the graph.

Harrison Chase’s AI Engineer talk frames reversible actions + human correction as ingredients of reliable enterprise agents: https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents

### Alternatives & Tradeoffs
| Mechanism | Fit | Caveat |
|-----------|-----|--------|
| LangGraph `interrupt()` | Graph-native pause/resume | Needs durable checkpointer; node replay semantics |
| Static breakpoints at compile | Simple always-pause nodes | Less flexible than conditional interrupt |
| Approve inside tool `run()` | Works with SDK tool runners | Easy to forget persistence across restarts |
| Out-of-band ticket / Slack queue | Familiar ops | Must wire resume idempotently |
| Always-on human | Safest | Not scalable |
| Prompt-only `confirm=True` | Cheap | Model may ignore |

Tradeoff: too many interrupts destroy automation ROI (rubber-stamping); too few create blast-radius incidents.

### Necessity
Money movement, customer emails, prod DB writes, and regulated advice without HITL fail security review and FDE customer trust. HITL without persistence forces the HTTP request to stay open — unusable for async human SLAs (approve hours later).

### Industry Practice
- **Common:** `input()` in a CLI demo called “HITL”; or prompt-based confirmation.
- **Senior:** risk-based interrupts (dollar thresholds, irreversible tool classes); durable checkpointer; UI shows interrupt payload + tool args; approve/edit/reject paths; timeouts/escalation if no human responds; audit who approved; idempotent nodes; test kill-and-resume; combine with tool allowlists; trajectory evals that attempt to bypass confirmation.

### Concrete Scenario
LangGraph interrupts guide — `interrupt("Do you approve this action?")`, detect via stream `interrupted` / `interrupts`, resume with `Command(resume=True)` on the same thread: https://docs.langchain.com/oss/python/langgraph/interrupts  
LangChain announcement of `interrupt` DX for production HITL: https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt  
AI Engineer Europe multi-agent + MCP workshop (orchestration + tools surface): https://www.youtube.com/watch?v=mYSRn6PC1mc

### Open Questions
- Should approval UIs be host-native (Agent Server) or customer IAM ticketing?
- How to prevent rubber-stamp fatigue when interrupt volume is high?
- Can LLM-as-judge replace *some* HITL without recreating rubber-stamp risk?

### Sources
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/checkpointers
- https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt
- https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents
- https://www.youtube.com/watch?v=mYSRn6PC1mc
- https://www.youtube.com/@aidotengineer

---

## Week 13 cross-cutting sources

- LangGraph workflows & agents: https://docs.langchain.com/oss/python/langgraph/workflows-agents  
- LangGraph graph API: https://docs.langchain.com/oss/python/langgraph/graph-api  
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence  
- LangGraph checkpointers: https://docs.langchain.com/oss/python/langgraph/checkpointers  
- LangGraph interrupts (HITL): https://docs.langchain.com/oss/python/langgraph/interrupts  
- LangChain multi-agent handoffs: https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs  
- OpenAI Agents SDK handoffs: https://openai.github.io/openai-agents-python/handoffs/  
- Microsoft AutoGen handoffs: https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html  
- Anthropic building effective agents: https://www.anthropic.com/engineering/building-effective-agents  
- Anthropic multi-agent research system: https://www.anthropic.com/engineering/multi-agent-research-system  
- Anthropic when to use multi-agent: https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them  
- CrewAI crews (cautious): https://docs.crewai.com/en/concepts/crews  
- AI Engineer — Chase enterprise agents talk: https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- YouTube AI Engineer channel: https://www.youtube.com/@aidotengineer  
