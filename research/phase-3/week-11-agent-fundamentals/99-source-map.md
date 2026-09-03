# 99 — Week 11 master source map

> Consolidated index of official docs, papers, talks. Legal sources only; no pirate book sites.

**Deep-pass date:** 2026-09-03. Provider URLs move (`platform.openai.com` → `developers.openai.com`, `docs.anthropic.com` → `platform.claude.com`); prefer the URLs below as fetched this pass.

---

## Anthropic — tool use (primary)

| Topic | URL |
|-------|-----|
| Tool use overview (`input_schema`, client vs server tools, `tool_choice`, `disable_parallel_tool_use`) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview |
| Handle tool calls (`tool_use` / `tool_result` pairing, `is_error`, untrusted results, invalid args 2–3 retries, strict) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls |
| Tool runner (`max_iterations`, `generate_tool_call_response`, early `break`) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner |
| Multimodal crop / zoom cookbook (manual loop + `max_iterations=20` + `is_error` recovery + truncated turns) | https://platform.claude.com/cookbook/multimodal-crop-tool |

---

## OpenAI — function calling & agents (primary)

| Topic | URL |
|-------|-----|
| Function calling (five-step flow, `strict`, `call_id` / `function_call_output`, parallel, custom tools) | https://developers.openai.com/api/docs/guides/function-calling |
| Migrate to Responses | https://developers.openai.com/api/docs/guides/migrate-to-responses |
| Tool search (`defer_loading`, gpt-5.4+) | https://developers.openai.com/api/docs/guides/tools-tool-search |
| Agents SDK — tools (`tool_namespace`, `ToolSearchTool`, defer_loading rules) | https://openai.github.io/openai-agents-python/tools/ |
| Agents SDK — agents (`tool_choice`, `reset_tool_choice`, `tool_use_behavior`, `StopAtTools`) | https://openai.github.io/openai-agents-python/agents/ |

---

## LangGraph / LangChain — agent loop & limits (primary)

| Topic | URL |
|-------|-----|
| Thinking in LangGraph (nodes, state, LLM-recoverable tool errors → loop back) | https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph |
| Quickstart (ReAct `llm_call` / `tool_node` / `should_continue`; Functional API `while True` + break) | https://docs.langchain.com/oss/python/langgraph/quickstart |
| Graph API overview (`recursion_limit` default 1000 as of 1.0.6, `RemainingSteps`, `langgraph_step`) | https://docs.langchain.com/oss/python/langgraph/graph-api |
| Use the graph API (loops, termination edges, `GraphRecursionError`, remaining-steps wrap-up) | https://docs.langchain.com/oss/python/langgraph/use-graph-api |
| `GRAPH_RECURSION_LIMIT` error reference | https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT |
| Workflows and agents (JS) (`ToolNode`, shouldContinue, ReAct cycle) | https://docs.langchain.com/oss/javascript/langgraph/workflows-agents |
| Agentic RAG (bind_tools + route on `tool_calls`) | https://docs.langchain.com/oss/python/langgraph/agentic-rag |

---

## Papers (open access)

| Topic | URL |
|-------|-----|
| Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models* (arXiv:2210.03629) — slogan source for plan/act/observe | https://arxiv.org/abs/2210.03629 |

---

## YouTube / AI Engineer talks

| Topic | URL |
|-------|-----|
| **Mahesh Murag (Anthropic)** — Building Agents with MCP, AI Engineer Summit (tool surfaces + agents; MCP itself is Week 12) | https://youtu.be/kQmXtrmQ5Zg |
| **Harrison Chase (LangChain/LangGraph)** — 3 ingredients for building reliable enterprise agents, AI Engineer World’s Fair (control flow, observability, cost-if-wrong) | https://www.youtube.com/watch?v=kTnfJszFxCg |
| Same talk — AI Engineer official talk page | https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents |
| AI Engineer channel (index more agent/tool talks) | https://www.youtube.com/@aidotengineer |

---

## Mapping: concept file → sources

| File | Must-cite |
|------|-----------|
| 00 overview + triad tools | OpenAI function calling; Anthropic overview; LangGraph quickstart/thinking; Chase + Murag talks; ReAct arXiv |
| 01 loop vs while | OpenAI five steps; Anthropic handle + tool runner; LangGraph quickstart + graph API; Agents `reset_tool_choice` |
| 02 schemas | OpenAI function calling + migrate; Anthropic overview + handle (`input_schema`, `strict`, pairing) |
| 03 selection | OpenAI tool search + Agents tools/agents; Anthropic overview/handle; both talks |
| 04 errors/retries | Anthropic handle + runner + zoom cookbook; OpenAI function calling; LangGraph thinking-in-langgraph |
| 05 stops | Tool runner + zoom; OpenAI function calling; LangGraph graph-api + GRAPH_RECURSION_LIMIT + use-graph-api; Chase talk |

---

## Out of scope (do not pull into Week 11)

| Topic | Week |
|-------|------|
| MCP protocol, transports, resources/prompts | 12 |
| Multi-agent, handoffs, checkpoints as *product*, HITL UX | 13 |
| A2A, irreversible side-effect policy beyond calendar idempotency | 14 |
| Trajectory eval harness | 15 |

---

## Syllabus shopping reminder

Phase 3 primary sources (curriculum README): **Anthropic MCP + Claude Agent SDK; LangGraph docs** — this week uses the **tool-use / agent-loop slice** of that list, plus **OpenAI function calling** (required by the Week 11 syllabus). MCP pages are linked from talks only as *preview*, not as this week’s corpus.
