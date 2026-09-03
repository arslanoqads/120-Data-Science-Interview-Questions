# 00 — Week overview & syllabus mapping

> Week 13 — Graph orchestration + HITL checkpoint for a high-stakes action  
> Research notes (raw). Phase 3 week after MCP (Week 12).

---

## Fundamentals

Week 13 is the **harness** week of Phase 3. Week 11 taught the **loop contract** (plan → act → observe, pairing IDs, stop reasons). Week 12 taught how tools **show up at a host boundary** (MCP). This week does **not** replace either. It is how you **schedule work over time**: shared state, branches, cycles, crash recovery, and a human pause that can last hours without holding a hot worker.

LangGraph models that harness as a **graph** ([Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)):

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

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| **StateGraph + checkpointer + `interrupt`** (syllabus) | Resume hours later; inspect payload; kill-safe | Learning curve; recursion limits; checkpoint ops |
| **LCEL / linear chain only** | Fast ETL-ish LLM pipes | No cycles, no native HITL pause, no time travel |
| **Week 11 `while` + `input()`** | Demo in a terminal | Blocks a process; unusable for async SLA |
| **Prompt “please confirm”** | Cheap | Model may skip; no audit; no durable cursor |
| **Static `interrupt_before=["send"]` only** | Always pause that node | Awkward for *conditional* dollar thresholds |
| **Temporal / Prefect as the only orchestrator** | Multi-day job durability | Two brains unless LLM patterns are thin |
| **CrewAI crew as production harness** | Fast role demos | You still own persistence, HITL, idempotency |
| **AutoGen distributed runtime** | Pub-sub / scale-out agents | Different mental model; still need a human sink |

Tradeoff: **too many** interrupts destroy ROI (rubber stamps). **Too few** fail security review. Gate **irreversible / high-blast** tools; let reads run.

Anthropic: start with API loops; add frameworks when you understand the prompts underneath ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)). Graphs are justified here because **pause/resume and shared state** are the product, not decoration.

---

## Necessity

If Week 13 is a linear chain labeled “agent”:

- You cannot express “call tools until done” **and** “wait for legal to approve the email.”  
- Instance death mid-tool duplicates refunds or abandons tickets.  
- Parallel nodes **clobber** state without reducers.  
- Cyclic graphs **hang** without `recursion_limit` (Week 11 stop conditions still apply).  
- Multi-agent without handoff discipline ping-pongs or corrupts tool-call pairing.  
- FDE interviews ask: *resume an approval after a deploy.* MemorySaver-in-a-notebook is a fail.

MCP elicitation (Week 12) is **complementary**: a *tool server* asking the host for input. Graph `interrupt` is the **orchestrator** asking the **application** to wait. Do not conflate them.

---

## Industry Practice

- **Common:** LCEL demo as “LangGraph”; `MemorySaver`; `input()` called HITL; CrewAI slide; “multi-agent” that is one prompt with 40 tools; `langgraph-supervisor` copy-paste after the package is unmaintained.  
- **Senior:** workflow vs agent chosen on purpose; typed state + reducers; compile once; `thread_id` strategy (user × ticket); Postgres checkpointer + prune/TTL; `interrupt` **before** writes; node replay tests; subagents as **tools** first ([Migrate from langgraph-supervisor](https://docs.langchain.com/oss/python/migrate/langgraph-supervisor)); subgraphs only when you need namespaces / shared keys; LangSmith per node; transfer caps; human as a first-class sink (AutoGen Human Agent).

AI Engineer Europe workshop (orchestration + MCP servers attached to Code/Cursor): useful as **compose** context, not a substitute for a checkpointer ([YouTube](https://www.youtube.com/watch?v=mYSRn6PC1mc)).

---

## Concrete Scenario

**Refund email must not send until a human says so.**

1. Agent drafts `to` / `subject` / `body` (or a tool proposes `issue_refund(amount_cents=50000)`).  
2. `approval` node `interrupt`s with the full payload. Stream shows `interrupted=True`.  
3. Ops UI (or LangGraph Studio / Agent inbox pattern from Chase’s talk) displays the payload. Approver edits the amount or rejects.  
4. `Command(resume=True)` or `resume={"approved": true, "amount_cents": 25000}`.  
5. `send` / `refund` node runs **once** with an idempotency key. Checkpoint history (`get_state_history`) shows the interrupt task.

Canonical docs walkthrough: approve/reject + `$500` transfer ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)). Persistence troubleshooting: MemorySaver loss, unbounded checkpoints, Postgres `thread_id` &lt; 255 chars ([Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)).

LangChain blog: `interrupt` is the production analogue of `input()` — pause, persist, resume on another machine months later ([Making HITL easier with interrupt](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)). Replit Agent (cited there) treated HITL as **design**, not a bolt-on.

---

## Open Questions

- Should approval UIs be host-native (Agent Server / Agent Inbox) or customer IAM ticketing with a webhook resume?  
- When does `create_agent` hide too much graph structure for FDE debugging?  
- Will MCP + host runtimes shrink app-level graphs, or will graphs wrap MCP tools?  
- Checkpoint PII retention vs “full state is the audit log” (it is **not** a signed approval log unless you add one).  
- Can LLM-as-judge replace *some* HITL without recreating rubber-stamp risk (Week 17)?  

---

## Sources

- https://docs.langchain.com/oss/python/langgraph/graph-api  
- https://docs.langchain.com/oss/python/langgraph/workflows-agents  
- https://docs.langchain.com/oss/python/langgraph/overview  
- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://docs.langchain.com/oss/python/langgraph/checkpointers  
- https://docs.langchain.com/oss/python/langgraph/interrupts  
- https://docs.langchain.com/oss/python/migrate/langgraph-supervisor  
- https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://www.youtube.com/watch?v=mYSRn6PC1mc  
- https://www.youtube.com/@aidotengineer  
