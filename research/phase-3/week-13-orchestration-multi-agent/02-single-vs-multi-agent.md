# 02 — Single agent with many tools vs multiple specialized agents

> Week 13 — Partition context and permissions, do not multiply logos  
> Research notes (raw).

---

## Fundamentals

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

1. **Context pollution** — subtask dumps &gt;~1k tokens that the main task does not need (example: full order history vs a 50–100 token summary).  
2. **Parallelizable work** — independent facets (research). Wall-clock cuts (their write-up: up to ~90% on complex research) come from concurrency, not from more logos.  
3. **Specialization** — different tools/policies (PII vs public search; math vs web).

Otherwise **coordination cost dominates**. In testing, multi-agent often uses **3–10×** tokens vs single-agent for equivalent tasks (duplicate context, coordination messages, summaries). Teams spent months on planner/executor/reviewer graphs and found **better single-agent prompting** matched results. Decompose by **context boundaries**, not arbitrary “researcher vs writer” labels.

**CrewAI (use cautiously):** `Crew` = agents + tasks + process (`sequential` / hierarchical manager) ([Crews](https://docs.crewai.com/en/concepts/crews)). Convenient role/backstory/goal metaphors; treat as a **prototyping layer**. Verify persistence, evals, and side-effect controls yourself.

**A2A** is a different axis: interoperability between **opaque** agents across vendors — complementary to MCP tools, **Week 14** for implementation ([A2A Protocol](https://a2a-protocol.org/latest/)). This week: in-process topology only.

---

## Alternatives & Tradeoffs

| Design | Pros | Cons |
|--------|------|------|
| Monolith agent | Easy to ship; one memory | Tool confusion; giant context; hard permissions |
| Supervisor → workers (subagents-as-tools) | Clear roles; isolates worker context; simple API | Extra LLM hops; cost multiplier; supervisor SPOF |
| Peer handoffs (file 03) | Natural “transfer to sales” UX | Context engineering; ping-pong loops |
| Subgraphs as nodes | Shared channels; per-tier checkpoints | Heavier; parent may not see child state |
| Middleware “one agent, many configs” | Simpler than multi-graph | Still one model identity |
| CrewAI sequential/hierarchical crew | Fast demos; role clarity | Ops/HITL/idempotency not solved for you |
| Always multi-agent “for scale” | Slide-friendly | 3–15× tokens; lost context at each hop |

Tradeoff: multi-agent is **context and permission partitioning**, not automatic intelligence. Wrong partition → handoff thrash and duplicated work.

---

## Necessity

Dozens of overlapping tools on one agent degrade tool choice (Week 11 file 03) and raise accidental **high-privilege** calls. Domains with different policies (PII vs public search) need separate agents **or** separate MCP servers (Week 12) with host consent.

Premature multi-agent adds latency, token burn, and “who owns the user reply?” ambiguity. Anthropic: start **single-agent**; split when evals show systematic confusion, pollution, or blast-radius differences.

Without **task briefs**, parallel subagents duplicate searches. Without **compressed summaries**, the lead’s context dies (same paper).

---

## Industry Practice

- **Common:** “multi-agent” slide; actually one agent; or CrewAI demo with no evals; still depending on `create_supervisor`.  
- **Senior:** start single-agent; wrap workers as **tools** first; escalate to subgraphs for bespoke graphs; measure **handoff rate**, loopbacks, and **$/task vs single-agent baseline** (15× research cost is a **warning**, not a goal); compile checkpointer only on the outer graph so HITL still works; flatten nested supervisors unless intermediate coordination is real.

---

## Concrete Scenario

**Anthropic Research:** lead agent plans, spawns 3–5 parallel subagents with explicit objectives/tools/boundaries, synthesizes compressed summaries — parallelization cut complex research wall-clock by up to ~90% in their write-up: https://www.anthropic.com/engineering/multi-agent-research-system  

**When *not* to:** support bot that looks up an order then debugs a login — use a **lookup subagent that returns a summary**, or even a single agent with a tight tool, rather than planner + researcher + writer + critic: https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them  

**LangChain migration:** `create_agent` + tool-wrapped `research_expert` / `math_expert` replacing `create_supervisor`: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor  

---

## Open Questions

- Is “agents as tools” strictly preferable to peer handoffs for enterprise support bots?  
- How should cost be attributed across supervisor + workers for customer billing?  
- Can a **verification-only** subagent pay for itself on every write path?  
- As models’ context windows grow, does the pollution argument shrink faster than the parallel-search argument?

---

## Sources

- https://www.anthropic.com/engineering/multi-agent-research-system  
- https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://docs.langchain.com/oss/python/migrate/langgraph-supervisor  
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs  
- https://docs.crewai.com/en/concepts/crews  
- https://a2a-protocol.org/latest/  
