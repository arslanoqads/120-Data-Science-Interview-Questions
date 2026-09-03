# 01 — Graph-based orchestration vs simple chains

> Week 13 — LangGraph `StateGraph` vs LCEL / linear DAGs  
> Research notes (raw).

---

## Fundamentals

**Simple chain:** a directed **acyclic** pipeline. Each step’s output is the next step’s input. LangChain LCEL (`prompt | model | parser`) and “retrieve → generate → format” RAG pipes are this shape. Great when the **control flow is known at authoring time** and you do not need to pause, loop, or fan-out with merge semantics.

**Graph (LangGraph):** a **state machine** over a shared snapshot ([Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)).

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

---

## Alternatives & Tradeoffs

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

---

## Necessity

Naive chains cannot express:

- “Call tools until the model stops” (cycle).  
- Approval gates that outlive an HTTP request.  
- Crash recovery mid-task (super-step checkpoints + pending writes).  
- Parallel workers writing the **same** list key (reducers).  

Without recursion limits, cyclic graphs loop until cost explodes. Production incidents look like “it hung” because the loop lived only in prompt text. Without compile-time graph checks, you ship orphan nodes and surprise `END`.

Interview signal: draw **nodes and edges** for “research then email with approval,” not a single box labeled LangChain.

---

## Industry Practice

- **Common:** LCEL demo branded LangGraph; recursion limit unset; `stream_mode` dumping private channels to the client; one mega-node that is a hidden `while`.  
- **Senior:** choose workflow vs agent **deliberately**; typed state + reducers on list/message channels; set recursion limits; stream for UX (`stream_events` v3); compile **once**, invoke with `thread_id`; LangSmith traces **per node**; subgraphs for specialized skills; `output_keys` so UIs don’t leak private channels; document `Command` vs plain input.

Official workflow walkthrough order: chaining → routing → parallelization → orchestrator–worker → evaluator–optimizer → agent loops ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)).

---

## Concrete Scenario

**Joke pipeline vs support agent.** LangGraph’s chaining example: `generate_joke` → gate `check_punchline` → maybe `improve_joke` → `polish_joke` — a **workflow** with a gate, still a DAG ([Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)). A support bot that **must** call `docs_search` then maybe `send_customer_email` needs a **cycle** plus an interrupt (file 05). Using the joke DAG for the support bot drops the loop; using an unbounded agent loop for “translate this paragraph” wastes tokens.

Harrison Chase, AI Engineer — “3 ingredients for building reliable enterprise agents”: high-value longer-running work; middle ground of autonomy + **deterministic workflows via LangGraph**; observability/evals; reversible actions + human correction — [talk](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents), [YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg).

Graph API (state/nodes/edges/super-steps/`Command`): https://docs.langchain.com/oss/python/langgraph/graph-api

---

## Open Questions

- When does `create_agent` hide too much graph structure for FDE debugging?  
- Graph DSL vs code-defined graphs for enterprise change control?  
- Will host-native agent runtimes (Claude Code, Agent Server) make app-level `StateGraph`s thinner wrappers around MCP tools?  
- How fine-grained should nodes be (one LLM call per node vs fat nodes) for trace quality vs overhead?

---

## Sources

- https://docs.langchain.com/oss/python/langgraph/workflows-agents  
- https://docs.langchain.com/oss/python/langgraph/graph-api  
- https://docs.langchain.com/oss/python/langgraph/overview  
- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://www.youtube.com/@aidotengineer  
