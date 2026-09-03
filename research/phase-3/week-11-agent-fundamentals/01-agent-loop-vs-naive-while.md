# 01 — Agent loop vs naive `while True`

> Week 11 — Agent fundamentals  
> Research notes (raw).

---

## Fundamentals

An **agent loop** is application-owned control flow around a **tool-calling model**. The model never executes tools. It emits a structured request; your process runs code; you append an observation; you call the model again. That is the entire mechanism. Frameworks are opinions about **when to stop**, **how to persist messages**, and **what to do on errors**.

### OpenAI: five steps, application continues

From the function-calling guide ([Function calling](https://developers.openai.com/api/docs/guides/function-calling)):

1. Make a request with tools the model could call.  
2. Receive a tool call (`function_call` items on Responses; `tool_calls` on Chat Completions).  
3. Execute application-side code.  
4. Second request with tool output (`function_call_output` / role `tool`), keyed by **`call_id`**.  
5. Final response **or more tool calls**.

The docs are explicit: *with Responses, continue for as many tool calls as the task requires*. They do **not** ship a `while True` for you. If you want packaged orchestration, they point at the **Agents SDK**. Parallel calls: multiple `function_call` items in one turn; you must return one output per `call_id`. `parallel_tool_calls: false` forces zero or one call. Built-in tools have extra rules (cannot sit in the same parallel batch as functions on some GPT-5+ paths).

### Anthropic: `stop_reason: tool_use` until it isn’t

Claude’s Messages API keeps tools inside the same `user` / `assistant` content arrays (no `role: tool`). Lifecycle ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)):

- Assistant message may mix `text` + one or more `tool_use` (`id`, `name`, `input`).  
- `stop_reason` is `"tool_use"` when you must run client tools.  
- Your next **user** message: `tool_result` blocks **first**, matching every `tool_use_id`, **immediately after** the assistant tool-use message (no interstitial messages). Text after results is allowed only when there is no unresolved **server** tool; otherwise 400.  
- Repeat until `stop_reason` is something else (`end_turn`, `max_tokens`, `refusal`, …).

**Tool runner** ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)): `client.beta.messages.toolRunner(...)` loops until Claude returns without tool use **or** `max_iterations`. You can `break` early. `generate_tool_call_response()` (Python) / `generateToolResponse()` (TS) lets you inspect errors before send. If you `append_messages()` yourself, *you* become responsible for pairing.

### LangGraph: the loop is edges, not a hidden while

Official mental model ([Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)): break the agent into **nodes**, connect them with **state**, route with **commands/conditional edges**. For tools: LLM-recoverable errors stay **in state** and `goto` the model node.

Canonical ReAct graph ([LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart), [Workflows and agents](https://docs.langchain.com/oss/javascript/langgraph/workflows-agents)):

- Node `llm_call`: bind tools, invoke model, append AI message.  
- Node `tool_node` / `ToolNode`: execute, append `ToolMessage`s (parallel execution is a `ToolNode` feature).  
- Conditional edge `should_continue`: if last message has `tool_calls` → tools, else `END`.  
- Edge tools → `llm_call`.

The graph API loop guide says a two-node cycle with a termination predicate is “similar to a ReAct agent” ([Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)). The **Functional API** example is literally `while True: if not tool_calls: break` — which is correct **only** with an outer recursion limit / step budget (file 05).

**ReAct paper vs API loop:** Yao et al. (arXiv:2210.03629) interleave *Thought / Action / Observation* in generated text. Native tool calling **replaces** brittle action-string parsing with JSON Schema. Keep the *interleaving* idea; do not keep 2022 prompt formats as production.

### Why naive `while True` collapses

A loop that only checks “did the model ask for a tool?” fails because:

1. **No iteration budget** — oscillation (same search, tool thrashing, “one more lookup”).  
2. **No token / $ / wall-clock budget** — each turn is a billable completion; context grows.  
3. **No typed stop reasons** — you must branch on `end_turn` / `stop` / `max_tokens` / `refusal` / `content_filter`, not only “no tool call.” Truncated tool JSON is not “the model is done.”  
4. **Side-effect tools are not idempotent** — unbounded retries double-book calendar, double-email, double-charge.  
5. **Missing pairing** — Anthropic 400 if `tool_use` ids lack matching `tool_result` immediately after; OpenAI will not make sense of orphan `call_id`s.  
6. **Partial / parallel / server-tool mixes** — multiple calls per turn; hosted web search / code execution; computer-use `toolset_name` echo rules. Toy loops drop unresolved server tools or reorder `tool_result` after prose.  
7. **Forced `tool_choice`** — OpenAI Agents SDK documents an **infinite loop** if you keep `tool_choice` pinned to a tool after the result is sent; the SDK **resets to `auto`** by default (`reset_tool_choice`) ([Agents](https://openai.github.io/openai-agents-python/agents/)). A naive while with `tool_choice: required` never naturally stops.  
8. **Exceptions escape the loop** — conversation left in illegal state (assistant tool_use with no result).

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| Manual OpenAI/Anthropic loop | HITL, custom transport, mixed hosted+client tools | You will get pairing/order wrong at least once; tests must cover 400s |
| Anthropic tool runner | Caps, formatting, iteration; intercept results | Beta; taking over a turn means you own history |
| OpenAI Agents SDK | `tool_use_behavior`, `reset_tool_choice`, hosted+function mix | Responses-centric features (tool search) do not port to Chat Completions |
| LangGraph StateGraph | Visible cycle; `recursion_limit`; checkpoints; Week 13 path | Two-node ReAct is still a loop — graphs do not magically add stop semantics |
| LangGraph Functional `while True` | Readable | Identical to naive while unless you add caps and error-as-message |
| “Always one tool then stop” | Bounded | Cannot compose docs + SQL + calendar |

Tradeoff: demos love unbounded ReAct. Production needs **hard caps** (iterations, tokens, dollars, time) plus **semantic stop** (goal achieved / user stop / policy deny). Chase (AI Engineer): required sequences belong in **control flow**; the loop is that control flow.

---

## Necessity

Without an explicit loop contract:

- **Cost incidents** — workers spinning on “one more search.”  
- **Hard API errors** — unpaired Anthropic tool_use; OpenAI missing `function_call_output`.  
- **Silent mid-task stop** — `max_tokens` on a tool call interpreted as final answer.  
- **Duplicate side effects** — retry of `calendar_create_event`.  
- **Un-debuggable traces** — no turn index, no stop reason, Week 15 eval impossible.

Anthropic’s zoom cookbook states a production loop must handle **token-capped turns**, **unknown tool names**, and **malformed args** — not only the happy path ([Zoom tool cookbook](https://platform.claude.com/cookbook/multimodal-crop-tool)).

---

## Industry Practice

- **Common:** `while True` until no `tool_calls`; no metrics; `except: raise`; copy `get_weather`.  
- **Senior:**  
  - Prefer tool runner / Agents SDK unless you need custom control.  
  - If manual: a `run_agent()` with `for i in range(max_iterations)` — not `while True`.  
  - Switch on **provider stop reason** every turn.  
  - Execute parallel client tools concurrently **only if** all are read-only or have idempotency keys.  
  - Log `{turn, stop_reason, tool_names, tokens, latency_ms, error_class}`.  
  - LangGraph: set `recursion_limit` **explicitly** (Graph API: default **1000** as of 1.0.6; older blog posts still say 25 — **do not assume**).  
- **FDE interview:** draw OpenAI’s five boxes and Anthropic’s pairing constraint on a whiteboard; then draw LangGraph’s two nodes + `END`.

---

## Concrete Scenario

**Naive loop (fails):** ops copilot, user asks to “find the incident runbook and page the on-call.” Model calls `docs_search`, then `calendar_create_event` (wrong tool — meant pager), HTTP 500, `except` bubbles, process dies. Client retries the whole request; search is fine, **create runs twice** if you “fixed” the exception by retrying the whole loop.

**Correct loop (documented patterns):**

1. OpenAI five-step continue-until-done: https://developers.openai.com/api/docs/guides/function-calling  
2. Anthropic tool runner `max_iterations=20` **or** manual dispatch + `is_error`: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner + https://platform.claude.com/cookbook/multimodal-crop-tool  
3. LangGraph: `should_continue` + `ToolNode`; errors as `Tool error: …` back to agent: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph  
4. Harrison Chase, putting reliability in LangGraph control flow: https://www.youtube.com/watch?v=kTnfJszFxCg  

**Week 11 lab assertion:** after N turns, either a final assistant text **or** a structured `AgentStopped(reason=..., turn=N)` — never a hung worker.

---

## Open Questions

- Planner–executor (two models) vs single ReAct model: extra latency vs inspectable plans.  
- Hosted server tools: who increments *your* iteration counter when Anthropic/OpenAI runs web search internally?  
- Should parallel tool execution be opt-in per tool annotation (`read_only`, `idempotent`) rather than a global flag?  
- Is the Functional API `while True` a footgun in official quickstarts that FDEs copy into production?

---

## Sources

- https://developers.openai.com/api/docs/guides/function-calling  
- https://openai.github.io/openai-agents-python/agents/  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner  
- https://platform.claude.com/cookbook/multimodal-crop-tool  
- https://docs.langchain.com/oss/python/langgraph/quickstart  
- https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph  
- https://docs.langchain.com/oss/python/langgraph/use-graph-api  
- https://docs.langchain.com/oss/python/langgraph/graph-api  
- https://docs.langchain.com/oss/javascript/langgraph/workflows-agents  
- https://arxiv.org/abs/2210.03629  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://youtu.be/kQmXtrmQ5Zg  
