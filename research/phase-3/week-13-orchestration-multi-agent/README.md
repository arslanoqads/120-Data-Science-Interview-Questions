# Week 13 Research Corpus — Orchestration frameworks and multi-agent design

> Phase 3 — Agentic Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 13 research repository. Read concept files in order, then the source map. **Do not start Week 14 (A2A / domain side effects) from this corpus** — this week is graphs, handoffs, persistence, and HITL *inside one process/runtime*. Side-effect safety catalogs and A2A protocol implementation belong next week.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Graph orchestration + HITL checkpoint before a **high-stakes** action |
| 01 | [01-graph-vs-chains.md](01-graph-vs-chains.md) | LangGraph `StateGraph` vs simple chains (LCEL / linear DAGs) |
| 02 | [02-single-vs-multi-agent.md](02-single-vs-multi-agent.md) | One agent + many tools vs specialized agents (subagents-as-tools) |
| 03 | [03-agent-handoffs.md](03-agent-handoffs.md) | Handoff tools, middleware vs subgraphs, AutoGen / OpenAI Swarm lineage |
| 04 | [04-persistence-resumable-state.md](04-persistence-resumable-state.md) | Checkpointers vs Store; `thread_id`; time travel; pending writes |
| 05 | [05-human-in-the-loop.md](05-human-in-the-loop.md) | `interrupt()` / `Command(resume=…)`; node replay; approval gates |
| — | [99-source-map.md](99-source-map.md) | Master URL / docs / YouTube index |

## Completeness checklist (Week 13)

- [x] All syllabus Week 13 concepts covered with **7 required fields**  
- [x] **Graph-based stateful orchestration** (LangGraph vs simple chains; workflows vs agents)  
- [x] **Single agent vs multi-agent** (subagents-as-tools; when *not* to split)  
- [x] **Agent handoff patterns** (LangChain `Command` / `active_agent`; OpenAI Agents SDK; AutoGen pub-sub)  
- [x] **Persistence and resumable state** (checkpointers, Store, `thread_id`, super-step snapshots)  
- [x] **Human-in-the-loop checkpoints** (`interrupt`, durable checkpointer, high-stakes approval)  
- [x] Overview includes **graph orchestration + HITL gate for a high-stakes action** (not CLI `input()`)  
- [x] LangGraph Graph API, workflows-and-agents, persistence, checkpointers, interrupts cited  
- [x] LangChain multi-agent handoffs + migrate-from-langgraph-supervisor cited  
- [x] AutoGen Core handoffs + Swarm cited  
- [x] Anthropic building-effective-agents + multi-agent research + when-to-use-multi-agent cited  
- [x] YouTube / **AI Engineer** talks cited (Harrison Chase enterprise agents; Europe MCP/orchestration workshop; channel)  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 13)

Ship a **stateful graph** with a **durable pause** before an irreversible (or expensive) write — not a notebook ReAct loop and not Week 14’s full safety catalog:

1. Model the task as a **`StateGraph`**: typed state + reducers, at least one **cycle** (LLM ↔ tools) *or* a deterministic workflow with a **conditional edge** into an approval node. Compile once; invoke with `{"configurable": {"thread_id": "…"}}`.  
2. Put **one high-stakes action** behind HITL (examples: send customer email, issue refund, write to prod calendar, `DROP`/mutate warehouse). The node calls `interrupt(payload)` **before** the side effect. Payload must be JSON-serializable (question + tool args + blast radius).  
3. Compile with a **checkpointer**. `InMemorySaver` is fine locally; document that production needs `PostgresSaver` / `SqliteSaver`. Same `thread_id` on resume.  
4. Drive with `stream_events(..., version="v3")` (or `invoke` + `__interrupt__`). Detect `stream.interrupted` / `stream.interrupts`. Resume with **`Command(resume=…)`** — approve, reject, or edited args.  
5. Prove **node replay**: code **before** `interrupt` is idempotent (or has no side effects). Kill the process while paused; restart; resume the same thread.  
6. Log: thread id, checkpoint id, who/what approved, tool name, before/after args.

Do **not** skip this week for “we’ll add `interrupt_before` later.” You cannot debug Week 14 side effects or Week 15 trajectories if the **cursor** (`thread_id`) and **approval gate** are implicit.

## Default path (synthesis)

1. Prefer a **single agent + middleware** (or subagents wrapped as **tools**) until evals show context pollution, parallel search, or permission partitions ([When to use multi-agent](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)).  
2. Prefer **LangGraph** when you need cycles, HITL, time travel, or multi-actor routing. Prefer **LCEL / a linear chain** when the path is a fixed DAG with no pause.  
3. Prefer **dynamic `interrupt()`** over only static `interrupt_before`/`interrupt_after` when the gate is risk-conditional (dollar threshold, tool class).  
4. Compile **only the outermost** graph with a checkpointer when nesting `create_agent` subagents so `interrupt` can bubble ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)).  
5. Interview artifact = **trace of pause → human decision → resume** on a durable thread, plus a **named high-stakes tool that did not run until approved**.
