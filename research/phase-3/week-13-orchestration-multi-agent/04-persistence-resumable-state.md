# 04 — Persistence and resumable state

> Week 13 — Checkpointers, Store, `thread_id`, time travel  
> Research notes (raw).

---

## Fundamentals

LangGraph persistence ([Persistence](https://docs.langchain.com/oss/python/langgraph/persistence); [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)):

| System | Persists | Scope | Use |
|--------|----------|-------|-----|
| **Checkpointer** | Graph state snapshots (`StateSnapshot`) + per-task writes | Single **thread** (`thread_id`) | Conversation continuity, HITL, time travel, fault tolerance |
| **Store** | App-defined key-value | Cross-thread | User preferences, facts, shared knowledge |

Compile: `builder.compile(checkpointer=..., store=...)`. Invoke with `{"configurable": {"thread_id": "..."}}`. Same `thread_id` **resumes**; new id starts empty. **Without `thread_id`, a checkpointer cannot save or resume.**

**Agent Server** can own persistence so you do not wire savers yourself.

### Threads and checkpoints

A **thread** is the primary key for checkpoint rows — accumulated state of a sequence of runs. A **checkpoint** is the snapshot at a **super-step boundary**. Time travel resumes **only** from those boundaries, not from mid-node.

Docs example `START → node_a → node_b` with `InMemorySaver` produces **4** checkpoints: empty/next START; user input/next `node_a`; after `node_a`/next `node_b`; after `node_b`/no next. List reducers (`Annotated[list, add]`) accumulate across nodes.

**Per-task writes:** as each node in a super-step finishes, outputs go to `checkpoint_writes` linked to the in-progress checkpoint. If a **sibling** node fails, successful writes are durable — resume does **not** re-run the successful nodes (**pending writes**). Those task writes are **not** full `StateSnapshot`s; replay/time travel still uses super-step checkpoints.

**Checkpoint namespace (`checkpoint_ns`):**

- `""` — parent/root graph.  
- `"node_name:uuid"` — subgraph invoked as that node. Nested: `"outer:uuid|inner:uuid"`.  

Read from a node via `config["configurable"]["checkpoint_ns"]`. Parent graphs may **not** see subgraph channel updates immediately — use Store or shared channels; see [Use subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs).

### Inspect and mutate

| API | Role |
|-----|------|
| `graph.get_state(config)` | Latest snapshot (or `checkpoint_id` for a specific one) |
| `graph.get_state_history(config)` | Chronological list, **newest first** |
| `graph.update_state(...)` | Fork / human edit (metadata `source` `"update"`) |
| Replay | Invoke with a prior `checkpoint_id` — nodes **before** skipped; nodes **after** re-execute (including LLM and interrupts) |

`StateSnapshot` fields (paraphrase of the table in checkpointer docs): `values`, `next` (empty ⇒ complete), `config` (`thread_id`, `checkpoint_ns`, `checkpoint_id`), `metadata` (`source`: `"input"` / `"loop"` / `"update"`; `writes`; `step`), `created_at`, `parent_config`, `tasks` (id, name, error, interrupts, optional subgraph `state`).

Find the interrupt checkpoint: history entry whose `tasks` have `interrupts`. Find forks: `metadata["source"] == "update"`.

### Production notes from docs

- `InMemorySaver` / `MemorySaver` — **RAM only**; process restart **wipes** threads.  
- Durable: `PostgresSaver` / `AsyncPostgresSaver`, `SqliteSaver` (local file). Call `setup()` to create tables/indexes.  
- Postgres `thread_id` column length — keep **&lt; 255** chars; UUID or hash.  
- Checkpoints **grow unboundedly** — prune / TTL cron (latency + storage).  
- Serialize concurrent invokes **per `thread_id`** (two workers, one thread → torn state).  
- Trace checkpointed resumes in **LangSmith**.

Resumability enables: multi-day conversations, crash recovery mid-graph, HITL waits **without** holding a hot worker ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)).

Nested `create_agent`: compile checkpointer **only on the outermost** graph so inner interrupts inherit the parent saver ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)).

---

## Alternatives & Tradeoffs

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

Tradeoff: durable checkpoints are required for serious HITL; they are **not** a signed audit log of who approved what (application must add that). They **do** contain **PII** if messages do — retention is a legal issue.

---

## Necessity

Cloud instance death mid-tool-call without checkpoint → **duplicate side effects** or abandoned tickets. Without Store, every thread re-learns preferences. Without `thread_id` discipline, “resume” silently starts a **new** empty graph.

Interview signal: resume an interrupted approval after a **deploy**. MemorySaver-in-a-notebook fails that test.

Pending writes matter when you fan-out: one parallel node throws; you must not re-charge the card the other node already charged.

---

## Industry Practice

- **Common:** MemorySaver in notebooks; surprise empty state in prod; unbounded checkpoint tables; `thread_id` = raw email (PII + length); concurrent chatbot workers on one thread; assuming parent `get_state` shows subgraph keys.  
- **Senior:** Postgres-backed checkpointer behind a pool; stable `thread_id` (user × session / ticket UUID, hashed if needed); TTL/prune job; **Store** for long-term memory; serialize per thread (queue / lock); test resume after `kill -9`; document subgraph namespaces; `get_state_history` in debug runbooks; LangSmith on resume paths.

---

## Concrete Scenario

Official persistence quickstart + checkpointer vs store + troubleshooting (MemorySaver loss, unbounded checkpoints, `thread_id` length): https://docs.langchain.com/oss/python/langgraph/persistence  

Checkpointers conceptual guide (HITL, time travel, fault tolerance, super-step snapshots, pending writes, `StateSnapshot`): https://docs.langchain.com/oss/python/langgraph/checkpointers  

Interrupts: pause persists via checkpointer; resume with same `thread_id` + `Command(resume=...)`: https://docs.langchain.com/oss/python/langgraph/interrupts  

**Kill-test:** run until `stream.interrupted`; SIGKILL the worker; new process, same Postgres DSN + `thread_id`; `get_state` still shows interrupt tasks; `Command(resume=True)` continues. If this fails, you are not production-HITL.

---

## Open Questions

- What retention / PII policy applies to full graph checkpoints in regulated industries?  
- How to migrate checkpoint schemas when **node names** or **state keys** change?  
- How fine-grained should super-steps be (cost vs resume fidelity)?  
- When is Store vs stuffing prefs into thread state the right split?

---

## Sources

- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://docs.langchain.com/oss/python/langgraph/checkpointers  
- https://docs.langchain.com/oss/python/langgraph/interrupts  
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs  
- https://docs.langchain.com/oss/python/migrate/langgraph-supervisor  
