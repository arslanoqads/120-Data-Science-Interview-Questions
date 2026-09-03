# Week 13 — Orchestration frameworks and multi-agent design

> Phase 3 — Agentic Systems  
> Raw research notes (not textbook prose). Legal sources only.

---

## Concept: Graph-based stateful orchestration (LangGraph-style vs simple chains)

### Fundamentals
A **chain** is a mostly linear pipeline (prompt → model → parse). A **graph orchestrator** (LangGraph and peers) models the agent as nodes (steps) and edges (transitions), with an explicit **shared state** object updated each step. Cycles enable plan→act→observe loops; conditional edges encode branching (retry, escalate, finish). Checkpoints snapshot state at super-step boundaries so runs can pause, resume, and time-travel debug.

### Alternatives & Tradeoffs
| Approach | Pros | Cons |
|----------|------|------|
| Simple chain / LCEL | Easy to read; low overhead | Weak for retries, HITL, multi-actor |
| Implicit `while` agent loop | Fast to prototype | Opaque control flow; hard to persist mid-loop |
| Explicit graph (LangGraph) | Debuggable, interruptible, testable nodes | Framework lock-in; learning curve |
| Workflow engines (Temporal, Prefect) | Strong durability for business workflows | Heavier; LLM-specific patterns less native |

Tradeoff: graphs add structure that interviewers and FDEs can draw on a whiteboard; over-graphing a Q&A bot wastes complexity budget.

### Necessity
Naive loops collapse under tool failures, partial writes, and process restarts. Without explicit state + edges, you cannot prove which node failed or resume after human approval. Production agent incidents often look like “it just hung” because control flow lived only in prompt text.

### Industry Practice
- **Common:** LangChain agent executor / raw tool loop in one FastAPI handler.
- **Senior:** typed state schema; named nodes; conditional edges for confidence/escalation; compile with checkpointer; metrics per node; subgraphs for specialized skills.

### Concrete Scenario
LangGraph persistence / checkpointers overview: https://docs.langchain.com/oss/python/langgraph/persistence  
Checkpointers enable HITL and fault tolerance: https://docs.langchain.com/oss/python/langgraph/checkpointers  
YouTube: LangChain “LangGraph” official deep-dives — https://www.youtube.com/results?search_query=langgraph+orchestration+langchain

### Open Questions
- Will MCP + host runtimes reduce need for app-level graphs, or will graphs wrap MCP tools?
- Graph DSL vs code-defined graphs for enterprise change control?

### Sources
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/checkpointers
- https://mastra.ai/articles/langgraph

---

## Concept: Single agent with many tools vs multiple specialized agents

### Fundamentals
**Single agent + many tools**: one policy/prompt selects among a large tool catalog. **Multi-agent**: specialized agents (research, SQL, ticket writer) with narrower prompts/tools, coordinated by a supervisor or handoffs. Specialization reduces tool-confusion; coordination adds latency and failure modes at handoff boundaries.

### Alternatives & Tradeoffs
| Design | When it wins | Failure mode |
|--------|--------------|--------------|
| Single agent | <10–15 clearly distinct tools | Tool mis-selection as catalog grows |
| Supervisor + specialists | Clear domains (billing vs docs) | Supervisor loops; context loss |
| Peer swarm | Parallel exploration | Cost explosion; hard evals |
| Dynamic single agent (middleware swaps tools/prompt) | Staged workflows without full multi-agent | Middleware complexity |

LangChain handoff docs recommend single agent + middleware for most cases; multi-agent subgraphs when specialists are themselves complex graphs.

### Necessity
Dumping 40 near-duplicate enterprise tools into one agent → wrong CRM update tool, infinite clarify loops, and unsafe side effects. Multi-agent without shared contracts → duplicated work and contradictory actions.

### Industry Practice
- **Common:** one mega-agent; tools named vaguely (`search`, `query`).
- **Senior:** tool taxonomy + disambiguation descriptions; split agents at trust/permission boundaries; shared trace IDs; evals for routing accuracy separately from task success.

### Concrete Scenario
Handoffs architecture (single vs multi-agent): https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs

### Open Questions
- Optimal tool-count thresholds before specialization (empirical, model-dependent)?
- Does stronger tool-calling in frontier models shrink the multi-agent premium?

### Sources
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- https://docs.langchain.com/oss/python/langgraph/

---

## Concept: Agent handoff patterns

### Fundamentals
A **handoff** transfers control (and usually conversation state) from one agent/configuration to another—via a tool that updates `active_agent` / `current_step`, or via graph `Command` routing to another node. Critical detail: LLM message histories expect tool calls paired with tool results; broken handoffs corrupt the dialogue schema and cause cryptic model errors.

### Alternatives & Tradeoffs
- **State-variable handoff** (same agent, new prompt/tools): simpler continuity.
- **Subgraph / distinct agent nodes**: stronger isolation; must manage parent/child commands and history validity.
- **A2A / network protocols**: cross-framework delegation (Week 14); more integration surface.
Tradeoff: invisible handoffs (prompt-only “you are now X”) vs explicit tools that auditors can see in traces.

### Necessity
Without disciplined handoffs, multi-agent demos work once and fail when the second agent lacks prior tool results or user constraints (ACLs, ticket IDs). FDE customer workflows (triage → act) demand auditable transfers.

### Industry Practice
- **Common:** concatenate transcripts into a new system prompt and “hope.”
- **Senior:** handoff tools with schemas; persist `active_agent` in checkpointer; validate message pairing; test handoff edge cases in trajectory evals.

### Concrete Scenario
LangChain multi-agent handoffs guide: https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs

### Open Questions
- Standard handoff envelope across MCP / A2A / LangGraph?
- How to hand off *partial* credentials without over-privilege?

### Sources
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs

---

## Concept: Persistence and resumable state

### Fundamentals
**Checkpointers** persist thread-scoped graph state after super-steps (conversation continuity, resume after crash/interrupt). **Stores** hold cross-thread long-term memory (preferences, facts). Together they separate “this run’s progress” from “durable knowledge.” Pending writes at task level support partial recovery when one parallel node fails.

### Alternatives & Tradeoffs
| Store | Use | Tradeoff |
|-------|-----|----------|
| In-memory checkpointer | Dev only | Lost on restart |
| Postgres/SQLite checkpointer | Prod threads | Ops + migration |
| External workflow engine | Multi-day jobs | Dual orchestration brains |
| Only chat history in Redis | Simple bots | Weak for HITL mid-tool |

### Necessity
Cloud Run instance death mid-tool-call without checkpoint → duplicate side effects or abandoned customer tickets. Interview signal: can you resume an interrupted approval flow?

### Industry Practice
- **Common:** session dict in process memory.
- **Senior:** thread_id per user/session; durable checkpointer; idempotent tools on resume; time-travel for debugging bad trajectories.

### Concrete Scenario
https://docs.langchain.com/oss/python/langgraph/persistence  
https://docs.langchain.com/oss/python/langgraph/checkpointers

### Open Questions
- Checkpoint PII retention vs GDPR deletion workflows?
- How fine-grained should super-steps be for cost vs resume fidelity?

### Sources
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/checkpointers

---

## Concept: Human-in-the-loop checkpoints

### Fundamentals
**HITL** pauses the graph before high-stakes actions (send email, modify prod record, spend money), surfaces state to a human, then resumes with approval/edits. Requires persistence: the person inspects a checkpoint and the graph continues from that exact point. Interrupts are first-class in LangGraph, not a hacky `input()`.

### Alternatives & Tradeoffs
- **Always-on HITL**: safest; kills latency/UX for low-risk tasks.
- **Risk-based interrupts** (confidence, dollar amount, irreversible tools): balanced.
- **Post-hoc review only**: faster; too late for irreversible actions.
- **Policy engine / static allowlists**: predictable; less flexible than human judgment.
Tradeoff: interrupt too often → rubber-stamping; too rare → production incidents.

### Necessity
Syllabus build: add HITL for one high-stakes action. Without it, agent demos that “file tickets” are unsafe for FDE customer environments and fail security review.

### Industry Practice
- **Common:** `confirm=True` boolean in prompt (model may ignore).
- **Senior:** hard interrupt before side-effecting tools; UI shows tool args; approve/edit/reject paths; audit log of human decisions; evals that attempt to bypass confirmation.

### Concrete Scenario
LangGraph checkpointers cite HITL as a primary reason persistence exists: https://docs.langchain.com/oss/python/langgraph/checkpointers  
Practitioner HITL walkthrough: https://oleg-dubetcky.medium.com/building-smarter-agents-a-human-in-the-loop-guide-to-langgraph-dfe1673d8b7b  
YouTube: LangChain HITL / interrupts sessions — https://www.youtube.com/results?search_query=langgraph+human+in+the+loop

### Open Questions
- Can LLM-as-judge replace some HITL without recreating rubber-stamp risk?
- Async HITL (email/Slack approve hours later) as default enterprise pattern?

### Sources
- https://docs.langchain.com/oss/python/langgraph/checkpointers
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://oleg-dubetcky.medium.com/building-smarter-agents-a-human-in-the-loop-guide-to-langgraph-dfe1673d8b7b
