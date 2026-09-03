# 99 — Week 13 master source map

> Consolidated index of official docs, talks, YouTube. Legal sources only; no pirate book sites.

**Deep-pass date:** 2026-09-03. LangGraph / LangChain OSS docs URLs under `https://docs.langchain.com/oss/python/...` move as the stack is renamed (`create_react_agent` → `create_agent`, `langgraph-supervisor` unmaintained). Re-fetch before shipping.

---

## LangGraph — graphs, workflows, agents (primary)

| Topic | URL |
|-------|-----|
| Graph API (state, reducers, nodes, edges, super-steps, compile, `Command`, schemas/streaming) | https://docs.langchain.com/oss/python/langgraph/graph-api |
| Workflows and agents (chaining, routing, parallelization, orchestrator–worker, evaluator–optimizer, agent loops) | https://docs.langchain.com/oss/python/langgraph/workflows-agents |
| LangGraph overview | https://docs.langchain.com/oss/python/langgraph/overview |
| Use subgraphs (namespaces, parent/child state, interrupts through subgraphs) | https://docs.langchain.com/oss/python/langgraph/use-subgraphs |
| Docs index (`llms.txt`) | https://docs.langchain.com/llms.txt |

---

## LangGraph — persistence, checkpointers, interrupts

| Topic | URL |
|-------|-----|
| Persistence (checkpointer vs Store; MemorySaver loss; unbounded checkpoints; `thread_id` length; subgraph visibility) | https://docs.langchain.com/oss/python/langgraph/persistence |
| Checkpointers (`StateSnapshot`, super-steps, pending writes, time travel, `get_state` / history) | https://docs.langchain.com/oss/python/langgraph/checkpointers |
| Interrupts (`interrupt()`, `Command(resume=…)`, node replay, approve/edit, multi-interrupt map, static breakpoints) | https://docs.langchain.com/oss/python/langgraph/interrupts |
| HITL DX blog (`interrupt` vs `input()`, Replit Agent) | https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt |

---

## LangChain — multi-agent handoffs & supervisor migration

| Topic | URL |
|-------|-----|
| Handoffs (middleware vs subgraphs, `Command.PARENT`, ToolMessage pairing, `active_agent`) | https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs |
| Migrate from `langgraph-supervisor` (subagents-as-tools, interrupt bubbling, outermost checkpointer) | https://docs.langchain.com/oss/python/migrate/langgraph-supervisor |

---

## OpenAI — Agents SDK handoffs

| Topic | URL |
|-------|-----|
| Handoffs (`transfer_to_*`, `handoff()`, `input_type`, `input_filter`, `on_handoff`, recommended prompt prefix) | https://openai.github.io/openai-agents-python/handoffs/ |

---

## Microsoft AutoGen

| Topic | URL |
|-------|-----|
| Core design pattern: handoffs (pub-sub, delegate tools, Human Agent, `UserTask`) | https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html |
| AgentChat Swarm (`HandoffMessage`, next speaker) | https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html |

---

## Anthropic — workflows, agents, multi-agent

| Topic | URL |
|-------|-----|
| Building effective agents (workflows vs agents; start simple; framework caution) | https://www.anthropic.com/engineering/building-effective-agents |
| How we built our multi-agent research system (orchestrator–worker, ~15× tokens, briefs, summaries) | https://www.anthropic.com/engineering/multi-agent-research-system |
| When to use multi-agent (pollution, parallel, specialization; 3–10× token overhead) | https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them |

---

## Adjacent (legal, mention-only this week)

| Topic | URL |
|-------|-----|
| CrewAI crews (prototype; not your persistence story) | https://docs.crewai.com/en/concepts/crews |
| A2A protocol (agent-to-agent interoperability — **implement in Week 14**) | https://a2a-protocol.org/latest/ |
| AI Engineer `llms.txt` | https://www.ai.engineer/llms.md |

---

## YouTube / conference

| Topic | URL |
|-------|-----|
| **Harrison Chase (LangChain)** — 3 ingredients for building reliable enterprise agents (LangGraph + HITL / reversibility + LangSmith) | https://www.youtube.com/watch?v=kTnfJszFxCg |
| Same talk, AI Engineer page | https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents |
| Talk id variant | https://ai.engineer/talks/kTnfJszFxCg-3-ingredients-building-reliable-enterprise-agents |
| **AI Engineer Europe** — multi-MCP / FastMCP workshop (orchestration + tools surface) | https://www.youtube.com/watch?v=mYSRn6PC1mc |
| Workshop companion repo | https://github.com/samtalasila/ai-engineer-europe |
| AI Engineer channel | https://www.youtube.com/@aidotengineer |

---

## Mapping: concept file → sources

| File | Must-cite |
|------|-----------|
| 00 overview + graph + HITL artifact | Graph API; workflows-agents; persistence; interrupts; Chase talk + YouTube; HITL blog |
| 01 graph vs chains | Graph API; workflows-agents; overview; Anthropic building-effective-agents; Chase |
| 02 single vs multi | Anthropic research system; when-to-use-multi-agent; migrate-langgraph-supervisor; subgraphs; CrewAI (cautious); A2A mention |
| 03 handoffs | LangChain handoffs; OpenAI Agents handoffs; AutoGen Core handoffs + Swarm; Anthropic research summaries |
| 04 persistence | Persistence; checkpointers; interrupts; subgraphs; supervisor migration (outer checkpointer) |
| 05 HITL | Interrupts; persistence; checkpointers; HITL blog; AutoGen human agent; Chase + Europe YouTube |

---

## Out of scope (do not pull into Week 13)

| Topic | Week |
|-------|------|
| Agent loop, pairing IDs, retries, stop reasons | 11 |
| MCP protocol, Desktop/Code attach | 12 |
| A2A **implementation** and side-effect safety catalogs | 14 |
| Trajectory eval | 15 |

Week 13 **mentions** A2A and MCP elicitation only as “not this week’s harness.” Do not write an A2A or MCP corpus here.

---

## Prior single-file week

Expanded from `phase-3/week-13-orchestration-multi-agent.md` (removed after this deep pass). Do not resurrect a thin single file for Week 13.
