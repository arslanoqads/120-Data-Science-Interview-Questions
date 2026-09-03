# 03 — Memory systems (short-term/session vs long-term/persistent)

> Week 25 — Context Engineering as a discipline  
> Research notes (raw).

---

## Fundamentals

**Memory** is how an agent retains information beyond a single model call. Context engineering cares because memory decides what *may* be selected into the window later. Two scopes dominate industry docs:

| Scope | Also called | Typical mechanism | Lifetime |
|-------|-------------|-------------------|----------|
| **Short-term / session** | Thread memory, working memory | Message list + checkpointed graph state | One conversation / thread |
| **Long-term / persistent** | Cross-session memory | Store / memory files / profiles / collections | Across threads & days |

### LangGraph: checkpointers vs stores

LangGraph’s persistence model (official docs):

- **Checkpointers** — persist a thread’s **graph state** as checkpoints. Short-term, **thread-scoped**. Enables conversation continuity, human-in-the-loop, time travel, fault tolerance. Access via `thread_id` in config.  
- **Stores** — persist application-defined key-value / JSON documents **outside** graph state. Long-term, **cross-thread**. Namespaces (e.g. `(user_id, context)`) + keys. Supports semantic search over memories when indexed.

Compile with both: `graph.compile(checkpointer=..., store=...)`.

Short-term updates on each invoke/step; long-term is read/written from nodes when application logic decides. Docs warn: long conversations exceed windows and degrade quality even when they fit — manage messages (trim, summarize, filter).

### Memory types (LangGraph / CoALA-inspired)

| Type | Stores | Agent example |
|------|--------|---------------|
| **Semantic** | Facts | User preferences, account attributes |
| **Episodic** | Experiences | Few-shot trajectories of successful tool use |
| **Procedural** | Instructions | Evolving system prompt / rules files |

Write timing:

- **Hot path** — agent decides to save during the user turn (transparent; adds latency; multitasking).  
- **Background** — async job / cron / “dreaming” fleet reviews transcripts and proposes memory updates (Mukta, Anthropic talk).

### Claude Managed Agents memory stores

Official docs: sessions start fresh by default; **memory stores** are workspace-scoped text document collections mounted at `/mnt/memory/{slug}/`. Agent reads/writes with normal file tools. Attach at session create via `resources[]`. Patterns:

- One store per end user (map your user IDs → store IDs).  
- Org standards as **read_only** + per-user **read_write**.  
- Injection risk: untrusted input + `read_write` can poison memory for future sessions — prefer `read_only` when possible.  
- Version history for audit/rollback.

Anthropic also describes **structured note-taking** inside a session (NOTES.md / TODO) as agentic memory that survives compaction better than raw transcripts.

### OpenAI patterns (public)

- Legacy **Assistants + Threads** — server-side message threads (API sunset path; migration docs point to Responses + Conversations).  
- **Responses API** — chain with `previous_response_id` or durable **Conversations** items; compaction for long runs (file 04).  
- Application-owned DB still common for true cross-product memory.

Chip Huyen (*Agents*): agents often exceed context limits; a memory system that supplements the window is essential — she flags a deeper memory post as future work, while treating knowledge-augmentation tools as the practical bridge today.

---

## Alternatives & Tradeoffs

| Design | Pros | Cons |
|--------|------|------|
| Checkpointer only | Simple resume; HITL | No cross-thread personalization |
| Store only | Durable facts | No automatic turn transcript |
| **Both** (LangGraph default advice) | Full coverage | Two systems to operate |
| Single profile JSON | Coherent user model | Patch errors as profile grows |
| Memory collection / files | High recall; easy append | Selection harder; over-insert |
| Provider-managed memory (ChatGPT-like) | UX magic | Opaque; surprise retrieval (Willison anecdote via LangChain) |
| Markdown files as memory (Claude) | Auditable; agent-native | Concurrent writers need versioning |

| Hot path vs background writes | |
|-------------------------------|--|
| Hot path | Immediate availability; user-visible “saved” |
| Background / dreaming | No latency tax; needs trigger policy & review |

---

## Necessity

Without separating session vs persistent memory:

- Restarting a worker process **wipes** “memory” that was only RAM messages — users see amnesia.  
- Putting all users in one store namespace → **cross-tenant leak** (isolation failure, file 05).  
- Writing every tool trace into long-term memory → **poisoning** and distraction forever.  
- Relying on the raw checkpoint message list as long-term truth → unbounded cost and Lost-in-the-Middle.  
- Security: prompt injection that says “remember the admin API key” persists if write path is unguarded (OWASP context poisoning; Anthropic read_only guidance).

---

## Industry Practice

- **Common:** client sends full history each call; “memory” is the chat sidebar; no namespaces.  
- **Strong:** Postgres/SQLite checkpointer in prod (not `InMemorySaver`); store namespaces include `tenant_id` + `user_id`; memory write tools require allowlists; evaluate memory *selection* precision/recall.  
- **FDE bar:** whiteboard checkpointer vs store in customer language (“this week’s ticket thread” vs “evergreen preference”); show mount paths / namespace keys; demonstrate read_only org memory; document retention & redact procedures via version APIs.

Claude Code / product agents: procedural memory in rules files always loaded; semantic memories selective. LangMem and similar libraries add abstractions on top of stores — treat as helpers, not substitutes for namespace design.

---

## Concrete Scenario

**LangGraph memory overview (checkpointer vs store)**  
https://docs.langchain.com/oss/python/concepts/memory  
https://docs.langchain.com/oss/python/langgraph/persistence  

Official distinction: short-term thread state via checkpointers; long-term cross-thread JSON memories via stores with namespaces. The add-memory guide shows production Postgres checkpointers and in-node `store.get` / `store.put` / semantic `store.search`.

**Claude Managed Agents — Using agent memory**  
https://platform.claude.com/docs/en/managed-agents/memory  

Filesystem-mounted stores, per-user mapping, read_only vs read_write, injection warning when agents process untrusted content.

**Talk:** Lamis Mukta (Anthropic), *Learning while you sleep: Beyond memory to dreaming* — https://www.youtube.com/watch?v=tTcxVv8HHNw — production memory as files + out-of-band dreaming for updates.

---

## Open Questions

- Can agents safely rewrite their own procedural prompts without eval gates?  
- Optimal dreaming cadence vs hot-path saves for support bots?  
- Should episodic few-shots live in LangSmith datasets (human curated) or automatic stores?  
- How to expire or decay memories (staleness) without surprising users?  
- Cross-product identity: one memory graph vs per-agent silos?

---

## Sources

- https://docs.langchain.com/oss/python/concepts/memory  
- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://docs.langchain.com/oss/python/langgraph/add-memory  
- https://docs.langchain.com/oss/python/langgraph/checkpointers  
- https://platform.claude.com/docs/en/managed-agents/memory  
- https://platform.claude.com/cookbook/managed-agents-cma-remember-user-preferences  
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
- https://developers.openai.com/api/docs/assistants/migration  
- https://developers.openai.com/api/docs/guides/compaction  
- https://huyenchip.com/2025/01/07/agents.html  
- https://www.youtube.com/watch?v=tTcxVv8HHNw  
- https://www.langchain.com/blog/context-engineering-for-agents  
