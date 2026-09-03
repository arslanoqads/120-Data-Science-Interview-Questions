# Chapter 13 — Orchestration frameworks and multi-agent design

> **Phase 3 — Agentic Systems**  
> **Editorial status:** COMPLETE  
> **Source of truth:** `research/phase-3/week-13-orchestration-multi-agent/`  
> **Syllabus Build:** Ship a **stateful graph** with a **durable pause** before an irreversible (or expensive) write — not a notebook ReAct loop and not Week 14’s full safety catalog: (1) model the task as a **`StateGraph`** with typed state + reducers, at least one **cycle** (LLM ↔ tools) *or* a deterministic workflow with a **conditional edge** into an approval node; compile once; invoke with `{"configurable": {"thread_id": "…"}}`; (2) put **one high-stakes action** behind HITL (`send_customer_email`, `issue_refund`, or prod calendar write — not a read-only search); the node calls `interrupt(payload)` **before** the side effect with a JSON-serializable payload (question + tool args + blast radius); (3) compile with a **checkpointer** (`InMemorySaver` locally; document that production needs `PostgresSaver` / `SqliteSaver`); same `thread_id` on resume; (4) drive with `stream_events(..., version="v3")` (or `invoke` + `__interrupt__`); detect `stream.interrupted` / `stream.interrupts`; resume with **`Command(resume=…)`** — approve, reject, or edited args; (5) prove **node replay**: code **before** `interrupt` is idempotent (or has no side effects); kill the process while paused; restart; resume the same thread; (6) log thread id, checkpoint id, who/what approved, tool name, before/after args. Interview artifact = **trace of pause → human decision → resume** on a durable thread, plus a **named high-stakes tool that did not run until approved**.

---

## Prerequisites Recap

Before this week you should already have from Week 12:

- An **MCP server / client** story — Host (Desktop or Code) owns a Client that is **1:1** with your Server; `initialize` ↔ capabilities; stdio for local attach.  
- **Primitives** advertised accurately: at least one **tool** (recommended: Week 11 `docs_search`), optional **resource** / **prompt**; list → call → observation feeds the Week 11 loop.  
- An **FDE integration surface**: the same capability attaches to **two hosts** (Claude Desktop `claude_desktop_config.json` + Claude Code `claude mcp add` / `.mcp.json`) without rewriting schemas per product.  
- A documented **trust boundary** (reachable dirs/APIs, secrets in `env`, confirmation for writes) — MCP is the wire; it does not schedule graphs or durable pauses.

You do **not** need a `StateGraph`, checkpointer, `thread_id` resume cursor, or graph `interrupt()` yet. That is what this week teaches (Week 14 adds the full side-effect safety envelope and A2A).

---

## What this week builds

Week 11 shipped the **loop contract**. Week 12 shipped the **connector** (MCP server/client, primitives, FDE host attach). Week 13 is the **harness** week of Phase 3. This week does **not** replace either. It is how you **schedule work over time**: shared state, branches, cycles, crash recovery, and a human pause that can last hours without holding a hot worker.

**Do not start Week 14 (side-effecting domain agent + safety envelope / A2A) from this chapter** — this week is graphs, handoffs, persistence, and HITL *inside one process/runtime*. Idempotency keys, preview/commit splits, audit logs, and A2A protocol implementation belong next week. MCP elicitation (Week 12) is **complementary**: a *tool server* asking the host for input. Graph `interrupt` is the **orchestrator** asking the **application** to wait. Do not conflate them.

LangGraph models the harness as a **graph** ([Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)):

| Piece | Job |
|-------|-----|
| **State** | Snapshot schema (`TypedDict` / dataclass / Pydantic) + **reducers** (how concurrent writes merge) |
| **Nodes** | Functions: read state → LLM / tools / code → return **updates** |
| **Edges** | Fixed or **conditional** “what runs next” |
| **Compile** | Validate (no orphan nodes), attach checkpointer / interrupts / breakpoints |

Execution is Pregel-like **super-steps**: scheduled nodes run (possibly in parallel), updates merge, next step schedules. The run **halts** when nothing is active and no messages are in transit. Cycles are first-class (agent ↔ tools). `Command` from a node can `update` state, `goto` another node, target `Command.PARENT` from a subgraph, or `resume` after an interrupt.

LangGraph and Anthropic use the same split ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents); [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)):

- **Workflows** — predetermined code paths: prompt chaining, routing, parallelization, orchestrator–worker, evaluator–optimizer.  
- **Agents** — the model dynamically chooses tools / next steps inside a loop.

A **simple chain** (LCEL pipe, `A → B → C`) is a DAG without cycles: retrieve → generate → format. A **stateful graph** adds cycles, fan-out/`Send`, shared memory, interrupts, and **resumable persistence**.

### Persistence is not optional for this week’s artifact

Two complementary systems ([Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)):

| System | Persists | Scope |
|--------|----------|-------|
| **Checkpointer** | Graph state snapshots at super-step (and per-task writes) | One **thread** (`thread_id`) |
| **Store** | App-defined key-value | Cross-thread (prefs, facts) |

HITL **requires** a checkpointer + `thread_id`. `InMemorySaver` / `MemorySaver` **dies with the process**. Production: `PostgresSaver` / `SqliteSaver` (or Agent Server, which owns persistence for you).

### Syllabus artifact: graph + high-stakes HITL

**What you ship:** one compiled graph, one durable thread, one **high-stakes** write that **cannot execute** until a human resume.

**Recommended high-stakes action:** `send_customer_email` **or** `issue_refund` **or** `calendar_create_event` against a real calendar (Week 11 tool, now gated). Do **not** pick a read-only search as the gated action.

Sketch of the control flow:

```
START → agent (LLM + tools)
           ↓ (wants send_customer_email)
        prepare_payload (no side effect)
           ↓
        interrupt({ question, to, subject, body, estimated_blast })
           ↓ Command(resume=True|False|{edited fields})
        execute_send  OR  cancel
           ↓
          END
```

`interrupt(payload)` inside a node ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)):

1. Super-step checkpoint is written.  
2. Graph waits **indefinitely** (no compute burn).  
3. Caller sees payload on `stream.interrupts` (`stream_events` v3) or `result["__interrupt__"]` (`invoke`).  
4. Resume: **same** `thread_id`, `Command(resume=value)`. That value is the **return** of `interrupt()`.  
5. **The node restarts from the top.** Anything before `interrupt` runs again → keep it **side-effect-free / idempotent**. Put the email send **after** a successful resume (or in a **separate node**).

Minimal shape (illustrative, not a full app):

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from typing import Literal, Optional, TypedDict

class MailState(TypedDict):
    to: str
    subject: str
    body: str
    status: Optional[Literal["pending", "sent", "rejected"]]

def approval_node(state: MailState) -> Command[Literal["send", "cancel"]]:
    decision = interrupt({
        "question": "Approve sending this customer email?",
        "to": state["to"],
        "subject": state["subject"],
        "body": state["body"],
        "irreversible": True,
    })
    return Command(goto="send" if decision else "cancel")

def send_node(state: MailState):
    # side effect lives HERE, after interrupt
    # smtp_send(state["to"], state["subject"], state["body"])
    return {"status": "sent"}

def cancel_node(state: MailState):
    return {"status": "rejected"}

builder = StateGraph(MailState)
builder.add_node("approval", approval_node)
builder.add_node("send", send_node)
builder.add_node("cancel", cancel_node)
builder.add_edge(START, "approval")
builder.add_edge("send", END)
builder.add_edge("cancel", END)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "ticket-4821"}}
```

Drive it:

```python
stream = graph.stream_events(
    {"to": "alex@customer.example", "subject": "Refund", "body": "…", "status": "pending"},
    config=config,
    version="v3",
)
_ = stream.output
assert stream.interrupted
# human reviews stream.interrupts[0].value
resumed = graph.stream_events(Command(resume=True), config=config, version="v3")
assert resumed.output["status"] == "sent"
```

Official approve/reject example uses the same pattern with `"Transfer $500"` as `action_details` ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)). That is the **syllabus shape**.

### What “done” looks like

1. Graph compiles; invoke with a stable `thread_id`.  
2. Run pauses **before** the write; payload shows recipients/amount/SQL.  
3. Process can be killed; on restart, `get_state(config)` still shows the interrupt.  
4. `Command(resume=False)` never sends. `resume=True` sends **once** (idempotency key if the node might replay).  
5. You can point LangSmith / traces at **node names**, not a blob called “agent.”

Harrison Chase (LangChain) at AI Engineer frames the economics: raise **value if right** and **P(success)** (deterministic workflow + autonomy via LangGraph; observability/evals), **lower cost if wrong** (reversible actions + human correction / inbox of pending approvals) — [talk page](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents), [YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg). This week implements the **cost-if-wrong** lever as a real interrupt, not a slide.

**Default path (synthesis):**

1. Prefer a **single agent + middleware** (or subagents wrapped as **tools**) until evals show context pollution, parallel search, or permission partitions ([When to use multi-agent](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)).  
2. Prefer **LangGraph** when you need cycles, HITL, time travel, or multi-actor routing. Prefer **LCEL / a linear chain** when the path is a fixed DAG with no pause.  
3. Prefer **dynamic `interrupt()`** over only static `interrupt_before`/`interrupt_after` when the gate is risk-conditional (dollar threshold, tool class).  
4. Compile **only the outermost** graph with a checkpointer when nesting `create_agent` subagents so `interrupt` can bubble ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)).  
5. Interview artifact = **trace of pause → human decision → resume** on a durable thread, plus a **named high-stakes tool that did not run until approved**.

Do **not** skip this week for “we’ll add `interrupt_before` later.” You cannot debug Week 14 side-effect safety or Week 15 trajectories if the **cursor** (`thread_id`) and **approval gate** are implicit.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) gaining a **StateGraph** harness and a **HITL gate** before a high-stakes customer-facing write — on tools that may already attach via Week 12 MCP.

---

### Graph-based orchestration vs simple chains

* **Fundamentals:**  
  A **simple chain** is a directed **acyclic** pipeline. Each step’s output is the next step’s input. LangChain LCEL (`prompt | model | parser`) and “retrieve → generate → format” RAG pipes are this shape. Great when the **control flow is known at authoring time** and you do not need to pause, loop, or fan-out with merge semantics.

  A **graph** (LangGraph) is a **state machine** over a shared snapshot ([Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)):

  1. **State** — schema for the snapshot. Default reducer is **overwrite**. `Annotated[list, add]` (or a custom binary reducer) **merges** updates so parallel nodes do not clobber lists.  
  2. **Nodes** — ordinary functions (LLM, tools, or code). They return **partial updates**, not a new world object you must merge by hand.  
  3. **Edges** — `add_edge` (fixed) or `add_conditional_edges` (branch). Cycles are allowed (e.g. `llm_call` ↔ `tool_node`).  
  4. **Super-steps** — Pregel-style ticks. Nodes scheduled together run in the **same** super-step (parallel); sequential hops are **separate** super-steps. Inactive nodes with no messages halt; the graph ends when all are inactive.  
  5. **Compile** — `.compile(...)` checks structure (orphans) and attaches runtime: checkpointer, `interrupt_before` / `interrupt_after`, store.

  **Input / output / private schemas:** `StateGraph(OverallState, input_schema=…, output_schema=…)` can hide keys from `invoke` while **streaming still emits all channels** unless you pass `output_keys`. Private channels are **not** a security boundary.

  **`Command`:** from a node you can `update`, `goto`, `graph=Command.PARENT` (subgraph → parent), or (as **input** to invoke/stream) `Command(resume=…)` after interrupts. Docs: `Command(resume=…)` is the **only** Command pattern meant as **invoke input**; do not pass `Command(update=…)` to continue a chat — pass a plain dict ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)).

  **Workflows vs agents** ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents); Anthropic [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)):

  | Pattern | Control lives in | Typical graph |
  |---------|------------------|---------------|
  | Prompt chaining | Code + optional gates | Linear nodes + conditional “pass/fail” |
  | Routing | Classifier then specialists | Conditional edges from a router node |
  | Parallelization | Fan-out then merge | Same super-step / `Send` |
  | Orchestrator–worker | Lead plans, workers execute | Dynamic subtasks (not a fixed DAG) |
  | Evaluator–optimizer | Generate ↔ critique loop | Cycle with stop condition |
  | Agent loop | Model chooses tools | Cycle until no tool calls / END |

  A chain is **one** of these (usually chaining). Calling a chain an “agent” hides missing loops, HITL, and persistence.

  **Recursion:** cyclic graphs need a **limit** (`recursion_limit` / remaining-steps patterns from Week 11). The graph will not “just know” to stop.

  **`create_agent`:** factory that **is** a graph underneath. Fine for a ReAct cycle; drop to explicit `StateGraph` when you need custom nodes, static subgraph discovery, or teaching/debugging the topology.

* **The Alternatives:**  

  | Style | Best for | Weakness |
  |-------|----------|----------|
  | Linear chain / LCEL | Deterministic ETL-ish LLM pipelines | No native loops, HITL pause, time-travel |
  | Single ReAct `while` (Week 11) | Few tools, short tasks | Weak branching, persistence, multi-actor |
  | LangGraph `StateGraph` | Cyclic agents, HITL, multi-agent, deployable runs | Learning curve; recursion limits; checkpoint ops |
  | `create_agent` only | Fast ReAct + tools | Topology opaque when debugging handoffs |
  | AutoGen event/runtime | Distributed pub-sub agents | Different mental model; ops complexity |
  | CrewAI crews/processes | Fast role-based prototypes | Persistence/HITL/idempotency not solved for you |
  | Workflow engines (Temporal, Prefect) | Multi-day business durability | Heavier; LLM-specific patterns less native |
  | Prompt-only “then call tools until done” | Zero infra | Control flow not testable; hangs; no resume |

  Tradeoff: graphs **do not** make the model smarter. They make **control flow inspectable**. Anthropic warns frameworks obscure prompts/tool IO — start with API loops; add graphs when measured value requires them ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)). Chase’s enterprise talk: reliability comes from putting required behavior in **control flow** (LangGraph) plus evals (LangSmith), not from a bigger prompt ([AI Engineer talk](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents)).

  The syllabus selects **StateGraph + checkpointer + `interrupt`** because pause/resume and shared state **are** the product this week, not decoration. Prefer LCEL when the path is a fixed DAG with no pause.

* **Failure Modes:**  
  - Naive chains cannot express “call tools until done” **and** “wait for legal to approve the email.”  
  - Instance death mid-tool duplicates refunds or abandons tickets without checkpoints.  
  - Parallel nodes **clobber** state without reducers.  
  - Cyclic graphs **hang** without `recursion_limit` (Week 11 stop conditions still apply).  
  - Production incidents look like “it hung” because the loop lived only in prompt text.  
  - Without compile-time graph checks, you ship orphan nodes and surprise `END`.  
  - LCEL demo branded as LangGraph; one mega-node that is a hidden `while`.  
  - `stream_mode` dumping private channels to the client.

* **Average vs. Strong Engineer:**  
  **Average:** LCEL pipe labeled “agent”; recursion limit unset; `create_agent` only with opaque topology; draws a single box labeled LangChain in interviews.  
  **Strong:** chooses workflow vs agent **deliberately**; typed state + reducers on list/message channels; set recursion limits; stream for UX (`stream_events` v3); compile **once**, invoke with `thread_id`; LangSmith traces **per node**; subgraphs for specialized skills; `output_keys` so UIs don’t leak private channels; documents `Command` vs plain input; can draw **nodes and edges** for “research then email with approval.” Official workflow walkthrough order: chaining → routing → parallelization → orchestrator–worker → evaluator–optimizer → agent loops ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)).

* **Worked Example:**  
  Deployment Copilot’s “translate this deploy note” stays a **joke-pipeline-shaped DAG**: linear nodes with an optional quality gate — like LangGraph’s chaining example `generate_joke` → gate `check_punchline` → maybe `improve_joke` → `polish_joke` ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)). The support path that **must** call `docs_search` then maybe `send_customer_email` needs a **cycle** plus an interrupt (HITL section). Using the joke DAG for the support bot drops the loop; using an unbounded agent loop for “translate this paragraph” wastes tokens.

  Sketch: `START → llm_call ⇄ tool_node → (conditional) approval → send | cancel → END`, with `Annotated[list, add]` on `messages` so parallel tool results merge. Compile once; invoke with `thread_id="ticket-4821"`. Traces name `llm_call`, `tool_node`, `approval`, `send` — not a blob called “agent.”

* **Apply It:**  
  1. Draw nodes and edges for Deployment Copilot’s “research then gated email” path before writing code.  
  2. Define typed state with reducers on any list/message channels parallel nodes will write.  
  3. Prefer explicit `StateGraph` when you need custom approval nodes; use `create_agent` only for a plain ReAct cycle.  
  4. Set `recursion_limit`; add Week 11-style stop conditions on the agent cycle.  
  5. Compile once; stream with `stream_events` v3; restrict client-facing channels with `output_keys` if you use private state.  
  6. Keep LCEL for fixed DAG transforms that never pause or loop.

---

### Single agent with many tools vs multiple specialized agents

* **Fundamentals:**  
  **Single agent + many tools:** one model, one system prompt, one tool list (or deferred tool-search — Week 11). Topology is simple. Failure mode is **selection pressure**: overlapping descriptions, accidental high-privilege calls, context filled with irrelevant tool results.

  **Multiple specialized agents:** each agent has a **narrow** prompt + **subset** of tools (billing, retrieval, coder). A **supervisor / router / handoff** chooses who acts. Coordination is extra tokens, extra latency, extra failure points.

  LangGraph / LangChain current guidance ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)):

  - The `langgraph-supervisor` package is **not actively maintained**.  
  - Prefer **subagents as tools** on a main `create_agent`: wrap `research_agent.invoke(...)` in `@tool("research_expert", ...)`. Control history in the wrapper (`last_message` vs summary vs full dump).  
  - Nested supervisors → nest **tool calls** (middle `create_agent` itself has tools that call leaf agents) **or** flatten to one supervisor with one tool per leaf.  
  - Use a custom **`StateGraph`** when you need **static subgraph discovery**, **checkpoint namespaces per tier**, or **shared state keys** between levels ([Use subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)).  
  - **Interrupt** inside a subagent tool **can bubble** if only the **outermost** graph is compiled with a checkpointer; inner `create_agent`s omit `checkpointer=` so they inherit at runtime.

  **Anthropic production lesson** ([How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)): Research uses **orchestrator–worker** — lead agent + parallel specialized subagents. Token use ran ~**15×** a chat interaction. Multi-agent wins when **breadth / parallel exploration** beats a single context. **Detailed task briefs** are mandatory — vague “research X” caused duplicate searches and gaps. Follow-up ([When to use multi-agent systems](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)):

  Split when you have **at least one** of:

  1. **Context pollution** — subtask dumps >~1k tokens that the main task does not need (example: full order history vs a 50–100 token summary).  
  2. **Parallelizable work** — independent facets (research). Wall-clock cuts (their write-up: up to ~90% on complex research) come from concurrency, not from more logos.  
  3. **Specialization** — different tools/policies (PII vs public search; math vs web).

  Otherwise **coordination cost dominates**. In testing, multi-agent often uses **3–10×** tokens vs single-agent for equivalent tasks (duplicate context, coordination messages, summaries). Teams spent months on planner/executor/reviewer graphs and found **better single-agent prompting** matched results. Decompose by **context boundaries**, not arbitrary “researcher vs writer” labels.

  **CrewAI (use cautiously):** `Crew` = agents + tasks + process (`sequential` / hierarchical manager) ([Crews](https://docs.crewai.com/en/concepts/crews)). Convenient role/backstory/goal metaphors; treat as a **prototyping layer**. Verify persistence, evals, and side-effect controls yourself.

  **A2A** is a different axis: interoperability between **opaque** agents across vendors — complementary to MCP tools, **Week 14** for implementation ([A2A Protocol](https://a2a-protocol.org/latest/)). This week: in-process topology only.

* **The Alternatives:**  

  | Design | Pros | Cons |
  |--------|------|------|
  | Monolith agent | Easy to ship; one memory | Tool confusion; giant context; hard permissions |
  | Supervisor → workers (subagents-as-tools) | Clear roles; isolates worker context; simple API | Extra LLM hops; cost multiplier; supervisor SPOF |
  | Peer handoffs (next concept) | Natural “transfer to sales” UX | Context engineering; ping-pong loops |
  | Subgraphs as nodes | Shared channels; per-tier checkpoints | Heavier; parent may not see child state |
  | Middleware “one agent, many configs” | Simpler than multi-graph | Still one model identity |
  | CrewAI sequential/hierarchical crew | Fast demos; role clarity | Ops/HITL/idempotency not solved for you |
  | Always multi-agent “for scale” | Slide-friendly | 3–15× tokens; lost context at each hop |

  Tradeoff: multi-agent is **context and permission partitioning**, not automatic intelligence. Wrong partition → handoff thrash and duplicated work. Prefer single agent + middleware (or subagents-as-tools) until evals force a split.

* **Failure Modes:**  
  - Dozens of overlapping tools degrade tool choice (Week 11) and raise accidental **high-privilege** calls.  
  - Premature multi-agent adds latency, token burn, and “who owns the user reply?” ambiguity.  
  - Without **task briefs**, parallel subagents duplicate searches.  
  - Without **compressed summaries**, the lead’s context dies.  
  - Still depending on unmaintained `create_supervisor` / `langgraph-supervisor`.  
  - “Multi-agent” slide that is actually one agent, or a CrewAI demo with no evals.  
  - Measuring logos instead of **$/task vs single-agent baseline** (15× research cost is a **warning**, not a goal).

* **Average vs. Strong Engineer:**  
  **Average:** always multi-agent “for scale”; copies supervisor packages; role labels (“researcher vs writer”) without context boundaries; no cost baseline.  
  **Strong:** starts single-agent; wraps workers as **tools** first; escalates to subgraphs for bespoke graphs; measures **handoff rate**, loopbacks, and **$/task vs single-agent baseline**; compile checkpointer only on the outer graph so HITL still works; flattens nested supervisors unless intermediate coordination is real; partitions by pollution / parallel / specialization criteria from Anthropic’s when-to-use guidance.

* **Worked Example:**  
  Deployment Copilot support: lookup an order then debug a login. Prefer a **lookup subagent that returns a summary** (or a single agent with a tight tool) rather than planner + researcher + writer + critic ([When to use multi-agent](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)).

  For a research-heavy “compare three deploy strategies” path, mirror Anthropic Research: lead agent plans, spawns 3–5 parallel subagents with explicit objectives/tools/boundaries, synthesizes compressed summaries — parallelization cut complex research wall-clock by up to ~90% in their write-up ([Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)).

  LangChain migration shape for Deployment Copilot:

  ```python
  # outer create_agent; research_expert / math_expert are @tool wrappers
  # around research_agent.invoke(...) / math_agent.invoke(...)
  # Control returned history: last_message or summary — not full dump
  # Outer graph only: compile(checkpointer=...)
  ```

  Replacing `create_supervisor` with `create_agent` + tool-wrapped experts: [Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor).

* **Apply It:**  
  1. Ship Deployment Copilot as a **single agent** with a short tool list first; measure tool-confusion and context size.  
  2. Split only when evals show pollution, parallelizable breadth, or policy/tool specialization.  
  3. Wrap specialists as **tools** returning summaries; avoid dumping full subagent transcripts.  
  4. Do not adopt `langgraph-supervisor`; follow the migrate guide.  
  5. Compile the checkpointer **only** on the outermost graph so nested `interrupt` can bubble.  
  6. Track $/task and handoff rate against the single-agent baseline before celebrating multi-agent.

---

### Agent handoff patterns

* **Fundamentals:**  
  **Handoff** (term popularized by OpenAI Swarm): transfer control via a **special tool call** (e.g. `transfer_to_refund_agent`) that updates routing state and/or navigates to another agent. The receiving agent adopts a new persona/tools; the user often continues in the **same** chat thread.

  **LangChain handoffs** ([Handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)):

  Tools update a state variable (`current_step` / `active_agent`) that **persists across turns**; the system reads it to change behavior (prompt/tools) or to route to another agent node.

  **Use when:** sequential constraints (warranty ID **before** refund); multi-stage conversational flows; the specialist must **talk to the user** (not just return a string to a supervisor).

  **Two implementations:**

  1. **Single agent + middleware** (recommended default) — one `create_agent`; `@wrap_model_call` swaps system prompt + tool palette from `current_step`. Tools return `Command(update={..., "current_step": "specialist", "messages": [ToolMessage(..., tool_call_id=...)]})`. Needs a **checkpointer** so the step survives turns.  
  2. **Multiple agent subgraphs** — distinct nodes; handoff tools return `Command(goto=..., graph=Command.PARENT, update={...})`.

  **Critical context rule for subgraph handoffs:** include the **AIMessage with the tool call** + a matching **ToolMessage** so history stays valid. Prefer **summarizing** in the ToolMessage, not dumping full subagent internals. Without the pair, the next model sees a dangling `tool_calls` and errors. Docs assume **no parallel tool calls** in the simple example — if the model called tools in parallel, you must complete **every** call.

  **End condition:** after an agent, if the last message is an `AIMessage` **without** tool calls → `END`. Else route on `active_agent`. Initial `START` routes on `active_agent` or a default (e.g. sales).

  Design notes: context filter (full history vs filtered vs summary) **per role**; handoff tools should **not** also create tickets (routing ≠ writes); as threads grow, summarization matters.

  **OpenAI Agents SDK** ([Handoffs](https://openai.github.io/openai-agents-python/handoffs/)): first-class. Represented as tools (`transfer_to_<name>`). Pass `Agent` in `handoffs=[...]` or `handoff(agent, ...)`.

  | Knob | Role |
  |------|------|
  | `tool_name_override` / `tool_description_override` | What the model sees |
  | `handoff_description` on Agent | Hint appended to default description |
  | `on_handoff` | Callback (logging, prefetch). Runs **before** transfer completes; raise to **block** |
  | `input_type` | Schema for **handoff tool args** (reason, priority) — **not** the next agent’s main input; **not** a dispatcher among destinations |
  | `input_filter` | Reshape `HandoffInputData` (history) for the next agent |
  | `is_enabled` | Bool or function — evaluated **before** the model picks args (cannot auth based on those args) |
  | `nest_handoff_history` | Opt-in compact nested summaries (beta; disabled by default) |

  `agents.extensions.handoff_filters.remove_all_tools` strips tool items so the specialist is not confused by internals. Recommended prompt prefix: `RECOMMENDED_PROMPT_PREFIX` / `prompt_with_handoff_instructions`. Guardrails: input guardrails apply to the **first** agent; output to the **last**; handoffs are not function-tool guardrails. Prefer `Agent.as_tool` when you want a nested specialist **without** transferring the conversation (same distinction as LangChain subagents-as-tools vs peer transfer).

  **Microsoft AutoGen** ([Core handoffs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html)): Swarm-inspired, **event-driven pub-sub**. Customer-service topology: **Triage** (understand, decide delegate); **Refund** / **Sales** (domain tools); **Human Agent** (first-class sink when AI cannot handle); **User Agent** (customer I/O). Protocol events: `UserLogin`, `UserTask` (chat history), `AgentResponse` (`reply_to_topic_type` + context). **Delegate tools** publish `UserTask` to another **topic** instead of continuing generation in the same agent. Regular tools execute locally then the model is called again. Claimed advantages vs original Swarm / AutoGen 0.2: distributed runtime, bring-your-own agent, async/UI-friendly. [AgentChat Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html): team selects the next speaker from the latest `HandoffMessage` while sharing message context (higher-level than Core pub-sub).

  **Anthropic Research:** handoffs to the **lead** use **compressed summaries**, never full subagent transcripts ([Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)). Same rule as LangChain’s “don’t dump internals.”

* **The Alternatives:**  

  | Pattern | UX | Engineering cost |
  |---------|----|------------------|
  | Middleware step machine | Smooth single persona morph | Careful step design; still one identity |
  | Peer agent transfer (`Command.PARENT`) | Explicit “I’m transferring you” | Message pairing; `active_agent` routing |
  | Supervisor always in the middle | Central policy | Extra latency **every** turn |
  | Agents-as-tools (no conversation transfer) | Clean isolation | Weaker shared chat continuity |
  | AutoGen topic delegate + Human Agent | Distributed; human sink | Pub-sub ops; protocol types to maintain |
  | OpenAI SDK `handoff()` | First-class tools + filters | Stays in one `Runner.run`; nested history still settling |
  | Human handoff | Trust | Staffing, SLA, **pause persistence** (persistence + HITL concepts) |
  | Full-history dump | Max context | Token burn; confusion; leakage |

  Tradeoff: handoff tools that also perform side effects (create ticket **and** transfer) blur semantics and make retries unsafe. Keep **pure routing** separate from **writes**. Prefer middleware for most cases; subgraphs only for bespoke workers.

* **Failure Modes:**  
  - Multi-agent systems that **never** transfer (wrong specialist answers) or transfer **without** valid tool-result pairing (API/history corruption).  
  - Unbounded peer transfers create **ping-pong**.  
  - Prompt-only “if needed, call transfer_*” with no state machine → infinite loops.  
  - Transfer tools with no `ToolMessage`; no transfer cap; no human sink.  
  - Mixing ticket creation into `transfer_to_sales`.  
  - Parallel tool calls in the same turn as a handoff without completing **every** call.

* **Average vs. Strong Engineer:**  
  **Average:** transfer tools with dangling `tool_calls`; no transfer cap; no human sink; side effects inside handoff tools.  
  **Strong:** explicit `active_agent` / `current_step` + end conditions (final AIMessage without tool calls → END); middleware for most cases; subgraphs only for bespoke workers; log every transfer; **cap transfers per session**; human agent as a first-class sink (AutoGen); `input_filter` / summaries; trajectory evals for handoff **edges** (Week 15); OpenAI `on_handoff` for audit metadata (`reason`, `priority`).

* **Worked Example:**  
  Deployment Copilot sales ↔ support ([LangChain handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)): `transfer_to_sales` builds `[last_ai_message, ToolMessage(tool_call_id=...)]`, sets `active_agent`, `goto="sales_agent"`, `graph=Command.PARENT`. Router: if last AIMessage has no tool calls → END; else active agent.

  OpenAI-shaped triage → billing/refund: `input_type` `{reason, priority}` logged in `on_handoff`; FAQ agent uses `remove_all_tools` filter ([OpenAI handoffs](https://openai.github.io/openai-agents-python/handoffs/)).

  AutoGen Core shape: triage/refund/sales/**human** topics; delegate tool publishes `UserTask` to refund topic ([AutoGen Core handoffs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html)).

  Middleware default for Deployment Copilot: one `create_agent`; `@wrap_model_call` swaps prompt/tools from `current_step`; handoff tools return `Command(update={...})` only — ticket creation is a **separate** write tool behind HITL.

* **Apply It:**  
  1. Decide peer transfer vs agents-as-tools: transfer only when the specialist must **talk to the user**.  
  2. Prefer middleware step machine; escalate to subgraphs when you need distinct nodes / `Command.PARENT`.  
  3. Always pair AIMessage tool call + ToolMessage; summarize, don’t dump internals.  
  4. Cap transfers per session; add a human sink for unhandleable cases.  
  5. Keep handoff tools pure routing — no side-effect writes in the same tool.  
  6. Log who/when/why (`input_type.reason`) and what context filter ran.

---

### Persistence and resumable state

* **Fundamentals:**  
  LangGraph persistence ([Persistence](https://docs.langchain.com/oss/python/langgraph/persistence); [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)):

  | System | Persists | Scope | Use |
  |--------|----------|-------|-----|
  | **Checkpointer** | Graph state snapshots (`StateSnapshot`) + per-task writes | Single **thread** (`thread_id`) | Conversation continuity, HITL, time travel, fault tolerance |
  | **Store** | App-defined key-value | Cross-thread | User preferences, facts, shared knowledge |

  Compile: `builder.compile(checkpointer=..., store=...)`. Invoke with `{"configurable": {"thread_id": "..."}}`. Same `thread_id` **resumes**; new id starts empty. **Without `thread_id`, a checkpointer cannot save or resume.**

  **Agent Server** can own persistence so you do not wire savers yourself.

  A **thread** is the primary key for checkpoint rows — accumulated state of a sequence of runs. A **checkpoint** is the snapshot at a **super-step boundary**. Time travel resumes **only** from those boundaries, not from mid-node.

  Docs example `START → node_a → node_b` with `InMemorySaver` produces **4** checkpoints: empty/next START; user input/next `node_a`; after `node_a`/next `node_b`; after `node_b`/no next. List reducers (`Annotated[list, add]`) accumulate across nodes.

  **Per-task writes:** as each node in a super-step finishes, outputs go to `checkpoint_writes` linked to the in-progress checkpoint. If a **sibling** node fails, successful writes are durable — resume does **not** re-run the successful nodes (**pending writes**). Those task writes are **not** full `StateSnapshot`s; replay/time travel still uses super-step checkpoints.

  **Checkpoint namespace (`checkpoint_ns`):**

  - `""` — parent/root graph.  
  - `"node_name:uuid"` — subgraph invoked as that node. Nested: `"outer:uuid|inner:uuid"`.  

  Read from a node via `config["configurable"]["checkpoint_ns"]`. Parent graphs may **not** see subgraph channel updates immediately — use Store or shared channels; see [Use subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs).

  **Inspect and mutate:**

  | API | Role |
  |-----|------|
  | `graph.get_state(config)` | Latest snapshot (or `checkpoint_id` for a specific one) |
  | `graph.get_state_history(config)` | Chronological list, **newest first** |
  | `graph.update_state(...)` | Fork / human edit (metadata `source` `"update"`) |
  | Replay | Invoke with a prior `checkpoint_id` — nodes **before** skipped; nodes **after** re-execute (including LLM and interrupts) |

  `StateSnapshot` fields (paraphrase of the checkpointer docs table): `values`, `next` (empty ⇒ complete), `config` (`thread_id`, `checkpoint_ns`, `checkpoint_id`), `metadata` (`source`: `"input"` / `"loop"` / `"update"`; `writes`; `step`), `created_at`, `parent_config`, `tasks` (id, name, error, interrupts, optional subgraph `state`).

  Find the interrupt checkpoint: history entry whose `tasks` have `interrupts`. Find forks: `metadata["source"] == "update"`.

  **Production notes from docs:**

  - `InMemorySaver` / `MemorySaver` — **RAM only**; process restart **wipes** threads.  
  - Durable: `PostgresSaver` / `AsyncPostgresSaver`, `SqliteSaver` (local file). Call `setup()` to create tables/indexes.  
  - Postgres `thread_id` column length — keep **< 255** chars; UUID or hash.  
  - Checkpoints **grow unboundedly** — prune / TTL cron (latency + storage).  
  - Serialize concurrent invokes **per `thread_id`** (two workers, one thread → torn state).  
  - Trace checkpointed resumes in **LangSmith**.

  Resumability enables: multi-day conversations, crash recovery mid-graph, HITL waits **without** holding a hot worker ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)). Nested `create_agent`: compile checkpointer **only on the outermost** graph so inner interrupts inherit the parent saver ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)).

* **The Alternatives:**  

  | Approach | Pros | Cons |
  |----------|------|------|
  | No persistence | Simple scripts | No resume / HITL / time travel |
  | In-memory checkpointer | Fast local | Dies with process |
  | Postgres checkpointer | Multi-instance workers | Ops + retention policy |
  | Sqlite file saver | Easy single-box | Not a multi-writer cluster story |
  | External session DB only | Familiar | Reimplement graph cursor + pending writes |
  | Provider conversation state | Less infra | Vendor lock; weaker custom graph control |
  | Temporal/Prefect for durability | Battle-tested long jobs | Dual orchestration brains |
  | Agent Server managed persistence | Less boilerplate | Platform coupling |

  Tradeoff: durable checkpoints are required for serious HITL; they are **not** a signed audit log of who approved what (application must add that). They **do** contain **PII** if messages do — retention is a legal issue. Syllabus: `InMemorySaver` locally with explicit documentation that production needs Postgres/Sqlite.

* **Failure Modes:**  
  - Cloud instance death mid-tool-call without checkpoint → **duplicate side effects** or abandoned tickets.  
  - Without Store, every thread re-learns preferences.  
  - Without `thread_id` discipline, “resume” silently starts a **new** empty graph.  
  - MemorySaver in notebooks; surprise empty state in prod.  
  - Unbounded checkpoint tables; `thread_id` = raw email (PII + length).  
  - Concurrent chatbot workers on one thread → torn state.  
  - Assuming parent `get_state` shows subgraph keys.  
  - Fan-out without understanding pending writes: re-charging a card a sibling node already charged.

* **Average vs. Strong Engineer:**  
  **Average:** MemorySaver-in-a-notebook; no kill-and-resume test; raw email as `thread_id`; no prune/TTL; dual workers on one thread.  
  **Strong:** Postgres-backed checkpointer behind a pool; stable `thread_id` (user × session / ticket UUID, hashed if needed, **< 255** chars); TTL/prune job; **Store** for long-term memory; serialize per thread (queue / lock); test resume after `kill -9`; document subgraph namespaces; `get_state_history` in debug runbooks; LangSmith on resume paths; separate signed approval log from checkpoint blobs.

* **Worked Example:**  
  Deployment Copilot refund email flow: compile with `PostgresSaver` (or `InMemorySaver` for local only). `thread_id="ticket-4821"` (or a UUID). Run until `stream.interrupted`. **Kill-test:** SIGKILL the worker; new process, same Postgres DSN + `thread_id`; `get_state` still shows interrupt tasks; `Command(resume=True)` continues. If this fails, you are not production-HITL.

  Inspect:

  ```python
  config = {"configurable": {"thread_id": "ticket-4821"}}
  snap = graph.get_state(config)
  # snap.next empty ⇒ complete; tasks[*].interrupts ⇒ paused for HITL
  history = list(graph.get_state_history(config))  # newest first
  ```

  Official persistence quickstart + troubleshooting (MemorySaver loss, unbounded checkpoints, `thread_id` length): [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence). Pending writes / `StateSnapshot`: [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers).

* **Apply It:**  
  1. Always pass `thread_id` when a checkpointer is attached; treat it as the resume cursor.  
  2. Use `InMemorySaver` only locally; document Postgres/Sqlite for production and call `setup()`.  
  3. Keep `thread_id` < 255 chars; prefer ticket UUID / hash over raw email.  
  4. Add prune/TTL; serialize concurrent invokes per thread.  
  5. Kill the process while interrupted; prove `get_state` + `Command(resume=…)` on restart.  
  6. Put cross-thread prefs in Store; do not assume parent `get_state` shows subgraph private channels.

---

### Human-in-the-loop checkpoints

* **Fundamentals:**  
  **Human-in-the-loop (HITL)** pauses automated execution for approval, edits, or extra input when models can take **irreversible** or high-blast actions.

  LangGraph **interrupts** ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts); [LangChain blog](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)):

  - Call `interrupt(payload)` **inside a node**. Payload must be **JSON-serializable** (string or object).  
  - Requires a **checkpointer** + `thread_id`. The thread id **is** the cursor.  
  - Graph saves state and waits **indefinitely** (storage, not CPU). Resume months later, **different machine**.  
  - Surface: `graph.stream_events(..., version="v3")` → `stream.interrupted`, `stream.interrupts`; or `invoke` → `result["__interrupt__"]`.  
  - Resume: **same** `thread_id`, `Command(resume=value)`. That value **is** the return of `interrupt()`.  
  - **Node restarts from the beginning** on resume. Code **before** `interrupt` runs again → **idempotent / no side effects**. Put writes **after** interrupt or in a **later node**.  
  - `Command(resume=…)` is the **only** Command intended as **invoke/stream input**. Do not pass `Command(update=…)` to continue a chat.

  This is the production analogue of Python `input()`: same DX, **not** a blocked CLI process ([blog](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)). Replit Agent (Michele Catasta, cited in that post) treated HITL as core design.

  **Patterns** (from interrupts docs):

  | Pattern | What the human does |
  |---------|---------------------|
  | **Approve / reject** | Gate API / DB / money; `Command(goto="proceed"|"cancel")` after resume |
  | **Review and edit** | `interrupt` returns **edited** text / tool args; node writes them into state |
  | **Validate input** | Pause until structured fields pass |
  | **Interrupt tool calls** | Review/edit proposed tool args **before** execution |
  | **Multiple interrupts** | Parallel nodes each `interrupt`; resume with **`{interrupt_id: value}`** map |
  | **Multi-turn in multi-agent** | Specialist nodes converse; human input is another interrupt/handoff (blog) |

  **Streaming HITL loop:** `while True`: `stream_events` → render `stream.messages` tokens → if not `interrupted` break; else `get_user_input(stream.interrupts[0].value)` → next input `Command(resume=...)`. Nested graphs: `stream.subgraphs[*].messages`.

  **Approve example payload** (docs): `{"question": "Approve this action?", "details": state["action_details"]}` with `"Transfer $500"` — this is the **syllabus high-stakes** shape.

  **Static vs dynamic interrupts:**

  | Mechanism | When |
  |-----------|------|
  | Dynamic `interrupt()` | Conditional logic (amount > $X, tool class, country) |
  | Compile `interrupt_before` / `interrupt_after` | Always pause those **nodes**; also usable as **debug breakpoints** |
  | Runtime `interrupt_before` on `invoke` | Per-run stepping |

  Prefer **dynamic** when the gate is risk-based. Never put irreversible side effects **before** a pause if you rely on `interrupt_after` (the side effect already happened). Docs: side effects **before** `interrupt()` must be idempotent; better: **after**, or **separate node**.

  **Nested agents:** `interrupt` inside a **subagent tool** bubbles through nested `create_agent` layers if **only the outermost** graph has the checkpointer ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)). Outer `invoke` still uses `thread_id`; callback resumes with `Command(resume=result)` — e.g. async enrichment job `job_id` in the interrupt payload.

  **Adjacent mechanisms (not substitutes):**

  - **AutoGen Human Agent** topic — escalation sink when AI cannot handle ([AutoGen handoffs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html)). Still need **durable** wait if the human is async.  
  - **MCP elicitation** (Week 12) — *tool server* asks the **host** for input. Graph interrupt is the **orchestrator** pausing the **app**.  
  - Chase: **reversible actions** + human correction + “agent inbox” of pending approvals lower **cost if wrong** ([AI Engineer talk](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents), [YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg)).

* **The Alternatives:**  

  | Mechanism | Fit | Caveat |
  |-----------|-----|--------|
  | LangGraph `interrupt()` | Graph-native pause/resume | Needs durable checkpointer; **node replay** |
  | Static breakpoints at compile | Simple always-pause nodes | Weak for conditional risk |
  | Approve inside tool `run()` | Works with SDK runners | Easy to forget persistence across restarts |
  | Out-of-band ticket / Slack queue | Familiar ops | Must wire resume **idempotently** + map ticket → `thread_id` |
  | Always-on human | Safest | Not scalable |
  | Prompt-only `confirm=True` | Cheap | Model may ignore; no audit |
  | LLM-as-judge instead of human | Cheap at scale | Rubber-stamp / reward-hacking (Week 17) |
  | Week 11 `while` + `input()` | Demo in a terminal | Blocks a process; unusable for async SLA |

  Tradeoff: too many interrupts destroy automation ROI; too few create blast-radius incidents. Gate **money, customer-visible send, prod writes, regulated advice**. Prefer dynamic `interrupt()` for risk-conditional gates.

* **Failure Modes:**  
  - Money movement, customer emails, prod DB writes, and regulated advice **without** HITL fail security review and FDE customer trust.  
  - HITL **without persistence** forces the HTTP request to stay open — unusable for “approve in three hours.”  
  - Node replay **without** idempotency **double-sends** email when the approver resumes.  
  - `interrupt_after` **after** a send is theater — the mail is gone.  
  - `input()` in a CLI demo called “HITL”; prompt-based confirmation; MemorySaver; side effects before `interrupt`.  
  - No timeout if the human never returns; rubber-stamp fatigue when interrupt volume is high.  
  - Treating MCP elicitation as a substitute for graph-level pause/resume.

* **Average vs. Strong Engineer:**  
  **Average:** CLI `input()` or prompt “please confirm”; MemorySaver; side effects before `interrupt`; static-only gates for dollar thresholds; no audit of who approved.  
  **Strong:** risk-based interrupts (dollar thresholds, irreversible tool classes); **durable** checkpointer; UI shows payload + tool args; approve / **edit** / reject paths; timeouts + escalation; **audit who approved** (separate from checkpoint blob); idempotent nodes; kill-and-resume tests; combine with tool allowlists; trajectory evals that try to **bypass** confirmation (Week 15); Agent Inbox-style queue of pending interrupts (Chase).

* **Worked Example:**  
  Deployment Copilot high-stakes path — refund or customer email — mirrors the docs `$500` transfer example ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)):

  ```python
  def approval_node(state: MailState) -> Command[Literal["send", "cancel"]]:
      decision = interrupt({
          "question": "Approve sending this customer email?",
          "to": state["to"],
          "subject": state["subject"],
          "body": state["body"],
          "irreversible": True,
      })
      # decision is Command(resume=…) value — bool or edited fields
      return Command(goto="send" if decision else "cancel")
  ```

  Drive: `stream_events(..., version="v3")` → assert `stream.interrupted` → human reviews `stream.interrupts[0].value` → `Command(resume=True)` or `resume={"approved": true, "amount_cents": 25000}` on the **same** `thread_id`. Side effect runs in `send_node` **only**, with an idempotency key. Checkpoint history (`get_state_history`) shows the interrupt task.

  Parallel fan-out: nodes `a` and `b` both interrupt; resume with `Command(resume={i.id: f"answer for {i.value}" for i in stream.interrupts})`.

  Ops UI (or LangGraph Studio / Agent inbox pattern from Chase’s talk) displays the payload. Approver edits the amount or rejects. Log: thread id, checkpoint id, who/what approved, tool name, before/after args.

* **Apply It:**  
  1. Gate one irreversible Deployment Copilot action (`send_customer_email` / `issue_refund` / prod calendar write) — not a read-only search.  
  2. Call `interrupt(payload)` **before** the side effect; keep pre-interrupt code side-effect-free.  
  3. Prefer dynamic `interrupt()` for risk thresholds; do not rely on `interrupt_after` for safety.  
  4. Compile with a durable checkpointer; resume only with `Command(resume=…)` on the same `thread_id`.  
  5. Prove kill-while-paused → restart → resume; add approve / edit / reject paths and an approval audit log.  
  6. Log the pause → decision → resume trace; that plus the gated tool name is the interview artifact.

When those steps are true, Week 13 is done in the syllabus sense: Deployment Copilot has a **resumable harness** with a real approval gate — not a notebook ReAct loop — and Week 14 can wrap a domain write in a safety envelope on top of this pause/resume cursor.


---

## Looking ahead

Week 14 is a **side-effecting domain agent** with a **safety envelope**: pick one real write (refund, ticket, or calendar create); split lookup / preview / propose / commit; wrapper-owned **idempotency keys**; gate irreversible commits with this week’s `interrupt()` (or a tokenized propose/commit); read back environment state as truth; append-only **audit**. Optional **A2A**: wrap the specialist as a peer Agent Card / Task when the write lives in another process or vendor — MCP remains agent-to-tool; A2A is agent-to-agent. The graph + HITL from this week does not go away; it is the harness those writes pause on. Interview artifact = one successful write + one non-duplicating retry + one rejected gate + an audit line.
