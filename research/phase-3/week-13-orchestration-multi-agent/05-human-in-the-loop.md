# 05 — Human-in-the-loop checkpoints

> Week 13 — Pause before irreversible work; resume with `Command`  
> Research notes (raw).

---

## Fundamentals

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

### Patterns (from interrupts docs)

| Pattern | What the human does |
|---------|---------------------|
| **Approve / reject** | Gate API / DB / money; `Command(goto="proceed"|"cancel")` after resume |
| **Review and edit** | `interrupt` returns **edited** text / tool args; node writes them into state |
| **Validate input** | Pause until structured fields pass |
| **Interrupt tool calls** | Review/edit proposed tool args **before** execution |
| **Multiple interrupts** | Parallel nodes each `interrupt`; resume with **`{interrupt_id: value}`** map |
| **Multi-turn in multi-agent** | Specialist nodes converse; human input is another interrupt/handoff (blog) |

**Streaming HITL loop:** `while True`: `stream_events` → render `stream.messages` tokens → if not `interrupted` break; else `get_user_input(stream.interrupts[0].value)` → next input `Command(resume=...)`. Nested graphs: `stream.subgraphs[*].messages`.

**Approve example payload** (docs): `{"question": "Approve this action?", "details": state["action_details"]}` with `"Transfer $500"` — this is the **syllabus high-stakes** shape (overview file 00).

### Static vs dynamic interrupts

| Mechanism | When |
|-----------|------|
| Dynamic `interrupt()` | Conditional logic (amount &gt; $X, tool class, country) |
| Compile `interrupt_before` / `interrupt_after` | Always pause those **nodes**; also usable as **debug breakpoints** |
| Runtime `interrupt_before` on `invoke` | Per-run stepping |

Prefer **dynamic** when the gate is risk-based. Never put irreversible side effects **before** a pause if you rely on `interrupt_after` (the side effect already happened). Docs: side effects **before** `interrupt()` must be idempotent; better: **after**, or **separate node**.

### Nested agents

`interrupt` inside a **subagent tool** bubbles through nested `create_agent` layers if **only the outermost** graph has the checkpointer ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)). Outer `invoke` still uses `thread_id`; callback resumes with `Command(resume=result)` — e.g. async enrichment job `job_id` in the interrupt payload.

### Adjacent mechanisms (not substitutes)

- **AutoGen Human Agent** topic — escalation sink when AI cannot handle ([AutoGen handoffs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html)). Still need **durable** wait if the human is async.  
- **MCP elicitation** (Week 12) — *tool server* asks the **host** for input. Graph interrupt is the **orchestrator** pausing the **app**.  
- Chase: **reversible actions** + human correction + “agent inbox” of pending approvals lower **cost if wrong** ([AI Engineer talk](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents), [YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg)).

---

## Alternatives & Tradeoffs

| Mechanism | Fit | Caveat |
|-----------|-----|--------|
| LangGraph `interrupt()` | Graph-native pause/resume | Needs durable checkpointer; **node replay** |
| Static breakpoints at compile | Simple always-pause nodes | Weak for conditional risk |
| Approve inside tool `run()` | Works with SDK runners | Easy to forget persistence across restarts |
| Out-of-band ticket / Slack queue | Familiar ops | Must wire resume **idempotently** + map ticket → `thread_id` |
| Always-on human | Safest | Not scalable |
| Prompt-only `confirm=True` | Cheap | Model may ignore; no audit |
| LLM-as-judge instead of human | Cheap at scale | Rubber-stamp / reward-hacking (Week 17) |

Tradeoff: too many interrupts destroy automation ROI; too few create blast-radius incidents. Gate **money, customer-visible send, prod writes, regulated advice**.

---

## Necessity

Money movement, customer emails, prod DB writes, and regulated advice **without** HITL fail security review and FDE customer trust. HITL **without persistence** forces the HTTP request to stay open — unusable for “approve in three hours.”

Node replay **without** idempotency **double-sends** email when the approver resumes. `interrupt_after` **after** a send is theater — the mail is gone.

---

## Industry Practice

- **Common:** `input()` in a CLI demo called “HITL”; prompt-based confirmation; MemorySaver; side effects before `interrupt`; no timeout if the human never returns.  
- **Senior:** risk-based interrupts (dollar thresholds, irreversible tool classes); **durable** checkpointer; UI shows payload + tool args; approve / **edit** / reject paths; timeouts + escalation; **audit who approved** (separate from checkpoint blob); idempotent nodes; kill-and-resume tests; combine with tool allowlists; trajectory evals that try to **bypass** confirmation (Week 15); Agent Inbox-style queue of pending interrupts (Chase).

---

## Concrete Scenario

LangGraph interrupts guide — `interrupt("Do you approve this action?")`, detect via `stream.interrupted` / `stream.interrupts`, resume `Command(resume=True)` on the same thread; full `$500` transfer example with `proceed` / `cancel` nodes: https://docs.langchain.com/oss/python/langgraph/interrupts  

Parallel fan-out: nodes `a` and `b` both interrupt; resume with `Command(resume={i.id: f"answer for {i.value}" for i in stream.interrupts})`.

LangChain announcement of `interrupt` DX (vs blocking `input()`; pause as scratchpad for human/agent collaboration): https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt  

AI Engineer Europe multi-agent + MCP workshop (orchestration **surface**, not a checkpointer tutorial): https://www.youtube.com/watch?v=mYSRn6PC1mc  

Chase on reversible actions + human intervention: https://www.youtube.com/watch?v=kTnfJszFxCg  

---

## Open Questions

- Should approval UIs be host-native (Agent Server / inbox) or customer IAM ticketing with webhook resume?  
- How to prevent rubber-stamp fatigue when interrupt volume is high (batching, thresholds, sampled review)?  
- Can LLM-as-judge replace *some* HITL without recreating rubber-stamp risk?  
- Who owns the SLA if the graph waits indefinitely — product, ops, or the customer’s approver role?

---

## Sources

- https://docs.langchain.com/oss/python/langgraph/interrupts  
- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://docs.langchain.com/oss/python/langgraph/checkpointers  
- https://docs.langchain.com/oss/python/migrate/langgraph-supervisor  
- https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt  
- https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://www.youtube.com/watch?v=mYSRn6PC1mc  
- https://www.youtube.com/@aidotengineer  
