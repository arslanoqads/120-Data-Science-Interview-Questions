# Week 11 Research Corpus — Agent fundamentals

> Phase 3 — Agentic Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal sources only; no pirated books.

This directory is the Week 11 research repository. Read concept files in order, then the source map. **Do not start Week 12 (MCP) from this corpus** — MCP is a *distribution* of tools, not the loop itself.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Phase 3 entry: loop contract + three starter tools (calendar, doc search, structured query) |
| 01 | [01-agent-loop-vs-naive-while.md](01-agent-loop-vs-naive-while.md) | Plan → act → observe vs naive `while True`; OpenAI 5-step flow; Anthropic tool runner; LangGraph graph loop |
| 02 | [02-tool-function-calling-schemas.md](02-tool-function-calling-schemas.md) | OpenAI function tools vs Anthropic `input_schema`; strict mode; pairing `call_id` / `tool_use_id` |
| 03 | [03-tool-selection-disambiguation.md](03-tool-selection-disambiguation.md) | Description hygiene, `tool_choice`, namespaces, deferred tool search, palette size |
| 04 | [04-tool-error-retry.md](04-tool-error-retry.md) | Executor retries vs model self-repair; `is_error`; idempotency; untrusted `tool_result` |
| 05 | [05-stopping-conditions-loop-limits.md](05-stopping-conditions-loop-limits.md) | `max_iterations`, LangGraph `recursion_limit` / `RemainingSteps`, budgets, stop taxonomy |
| — | [99-source-map.md](99-source-map.md) | Master URL / cookbook / YouTube index |

## Completeness checklist (Week 11)

- [x] All syllabus Week 11 concepts covered with **7 required fields**  
- [x] **Agent loop** vs naive `while True` (OpenAI 5-step flow; Anthropic `tool_use` / `tool_result`; LangGraph llm↔tools cycle)  
- [x] **Tool / function calling schemas** for **both OpenAI and Anthropic** (`parameters` vs `input_schema`; `strict`; pairing IDs)  
- [x] **Tool selection / disambiguation** (descriptions, `tool_choice`, parallel disable, tool search / `defer_loading`, namespaces)  
- [x] **Error handling and retry** (`is_error` vs error-in-output; retryable vs not; no retry of mutating tools without idempotency)  
- [x] **Stopping conditions / loop limits** (model-natural stop, `max_iterations`, LangGraph `recursion_limit` + `RemainingSteps`, resource + policy stops)  
- [x] Overview includes **2–3 real tools**: calendar, doc search, structured query (schemas + when-to-use)  
- [x] Anthropic tool use + handle-tool-calls + tool runner cited  
- [x] OpenAI function calling + tool search + Agents SDK tools cited  
- [x] LangGraph / agent-loop docs cited (Graph API, workflows-and-agents, thinking-in-langgraph, `GRAPH_RECURSION_LIMIT`)  
- [x] YouTube / **AI Engineer** talks cited (Mahesh Murag MCP workshop; Harrison Chase enterprise agents; channel)  
- [x] ReAct paper (Yao et al., arXiv:2210.03629) cited as the *slogan* source, not a pirate book  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 11)

Ship a **single-agent tool loop** (not MCP, not multi-agent):

1. Define **three client tools** with strict JSON Schema: `calendar_list_events` / `calendar_create_event`, `docs_search`, `structured_query`.  
2. Implement a **bounded loop**: OpenAI Responses `function_call` ↔ `function_call_output` **or** Anthropic Messages `tool_use` ↔ `tool_result` (one primary provider, the other as a mapping table).  
3. Enforce **pairing** (every `call_id` / `tool_use_id` gets a result immediately after), **iteration cap**, **per-tool timeout**, and a typed **stop reason** (`end_turn` | `max_iterations` | `max_tokens` | `tool_budget` | `policy_deny` | `user_cancel`).  
4. Convert tool exceptions into **error observations** (never crash mid-`tool_use`). Classify retryable (429/5xx inside the executor, capped) vs model-visible (`is_error` / error string).  
5. Log a **turn trace**: model stop reason, tool name(s), latency, error class, remaining budget.

Do **not** skip this week for “we’ll wrap LangChain AgentExecutor and ship.” You cannot debug MCP (Week 12), graphs/HITL (Week 13), or side effects (Week 14) if the **loop contract** is implicit.

## Default path (synthesis)

1. Prefer **SDK tool runner / Agents SDK** when you do not need custom transport; drop to a **manual loop** when you own HITL, streaming UX, or mixed server+client tools.  
2. Prefer **LangGraph** (explicit `llm_call` → `tool_node` → `llm_call` + `recursion_limit`) when you already know you need checkpoints, branches, or HITL next week — but still treat Week 11 as *one ReAct cycle*, not a multi-agent graph.  
3. Keep the tool palette **small and mutually exclusive** (calendar vs docs vs SQL). Add tool search only after ~20–30 tools.  
4. Reads may auto-retry; **writes require idempotency keys** or HITL (Week 13/14).  
5. Interview artifact = **trace of a multi-step task** (search docs → query structured store → propose calendar event) with a **named stop reason**, not “the agent just worked.”
