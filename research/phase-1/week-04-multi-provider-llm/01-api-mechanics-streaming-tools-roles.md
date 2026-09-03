# 01 — API mechanics: streaming, tools, roles (OpenAI + Anthropic)

> Week 4 concept research (deep). Legal sources only.

---

## Fundamentals

### Shared mental model
Both OpenAI and Anthropic expose chat-style APIs built around **role-tagged messages**, optional **tools**, and optional **streaming**. The application owns the loop: send messages (+ tools) → receive text and/or tool calls → execute tools locally → append results → repeat until a final answer or stop condition.

### OpenAI roles and instruction hierarchy
Chat Completions historically used `system`, `user`, `assistant`, plus `tool` for tool results. Newer models introduce a **`developer`** role. OpenAI’s Model Spec treats authority as layered: **platform/system (OpenAI) > developer > user**. In API practice, the caller’s system/developer message is **developer-authority** guidance (persona, output rules, tool policy)—not the Spec’s platform “System” level, which only OpenAI can write.

Practical mapping:

| Role | Purpose |
|------|---------|
| `developer` / legacy `system` | App instructions; tool policy; higher than user |
| `user` | End-user / product request |
| `assistant` | Prior model turns |
| `tool` (Chat Completions) | Tool result keyed by `tool_call_id` |
| Responses items | `function_call` / `function_call_output` typed items; `instructions` often inject as developer |

o-series / GPT-5-family prefer `developer`; older models may reject or auto-convert. Adapters must tolerate both.

### Anthropic roles
The Messages API primarily uses `user` and `assistant` inside `messages`. **System instructions** go in a top-level `system` parameter (string or content blocks)—not a `"system"` role in the classic pattern. Tool results return as `tool_result` content blocks inside a subsequent **`user`** message, keyed by `tool_use_id`. Newer Claude models also allow mid-conversation `"role": "system"` messages after a user turn (not as the first entry), which preserves earlier prompt-cache prefixes because new system text is appended rather than rewriting the top-level `system` field.

### Tool / function calling flow (both)
1. Client sends tool definitions (JSON Schema for arguments).  
2. Model may emit one or more tool calls (`tool_calls` / `function_call` on OpenAI; `tool_use` content blocks on Anthropic).  
3. Application executes tools and returns results.  
4. Model continues with a final answer or more tool calls.

OpenAI distinguishes **function tools** (JSON Schema args), **custom tools** (free-form text), and **platform built-ins** (web search, code execution, MCP, etc.). Anthropic distinguishes **client tools** (you execute) vs **server tools** (Anthropic executes, e.g. web search). Both support `tool_choice` / forced selection. OpenAI `strict: true` on tools enables schema-guaranteed args (see concept 02). Anthropic `strict: true` on tool defs is the parallel.

OpenAI docs note functions are injected into the system message under the hood—definitions **count against context and are billed as input**. Large tool catalogs need truncation, namespaces, or tool search (`tool_search` on gpt-5.4+).

### Streaming
- **OpenAI Chat Completions:** `stream: true`; text as `delta.content`; tool calls as incremental `delta.tool_calls[index]` fragments aggregated by index.  
- **OpenAI Responses:** typed SSE events (`response.function_call_arguments.delta`, `.done`, `response.output_item.added/done`).  
- **Anthropic:** `stream: true` yields SSE (`message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, `message_stop`). For tools, `input_json_delta` carries `partial_json`; final `tool_use.input` is complete. Fine-grained tool streaming (`eager_input_streaming: true` per tool) streams parameter values without buffering each value server-side—accumulated JSON may be invalid until stop.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
| --- | --- | --- |
| Chat Completions (OpenAI) | Ubiquitous; many SDKs/examples | Older message/tool shapes; migration pressure toward Responses |
| Responses API (OpenAI) | Typed items, cleaner agent loops, `previous_response_id` | Different event model; ecosystem still catching up |
| Anthropic Messages | Clear top-level `system`; strong tool/cache story | Role mapping differs; adapters mandatory for multi-provider |
| Non-streaming | Simpler parsers | Higher TTFT; worse UX for long generations |
| Streaming + tools | Lower perceived latency; progressive UI | Complex aggregation; partial JSON invalid until done |
| Forced `tool_choice` | Guarantees structured side-effect or extraction | Can block natural language; conflicts with some thinking modes |
| Multi-provider abstraction (LiteLLM, etc.) | Portability | LCD features; subtle role/tool mismatches |

---

## Necessity

Production LLM apps almost always need: (1) correct role placement so instructions outrank user text, (2) a reliable tool loop for external data/actions, and (3) streaming for interactive products.

Failure modes if skipped:

1. Mapping Anthropic top-level `system` to OpenAI roles wrong (or stuffing OpenAI `developer` into Anthropic `messages`) → hierarchy and cache bugs.  
2. Streaming without index/`partial_json` aggregation → truncated args → failed tools → agent thrash.  
3. Returning Anthropic tool results as OpenAI `role: tool` without remapping → 400s.  
4. Ignoring that tool schemas burn context → mysterious window overflows.  
5. Mixing OpenAI built-in tools with Anthropic server tools in “portable” agent code without a capability matrix.

---

## Industry Practice

### Common (weak)
- Copy-paste OpenAI Chat Completions examples; bolt Anthropic later.  
- Buffer entire stream then parse; or execute tools on incomplete JSON.  
- One giant system string with no separation of policy vs user data.

### Strong / senior
- **Provider adapters** normalize roles (`system`/`developer` ↔ Anthropic `system`), tools, and stream events into an internal message type.  
- Prefer **strict tool schemas**; validate args in app code before side effects; gate destructive tools on human approval.  
- Use Responses API / Agents SDK for new OpenAI agentic work; keep Chat Completions for legacy chat UIs.  
- Anthropic: stable policy in top-level `system`; mid-conversation system only when instructions become relevant later and cache prefixes must stay intact.  
- Log full tool traces (call id, name, args, latency, result size).  
- ACI mindset (Dougherty): tool **response format** is part of the interface—JSON vs XML can flip reliability by model family.

### RAG / agent application
Expose retrieval as tools (`search_chunks`, `get_doc`) rather than only stuffing RAG into the system prompt—keeps the agent loop honest and the system prefix cacheable (see concept 04).

---

## Concrete Scenario

A support agent answers “What’s the weather in San Francisco?” with a live tool. OpenAI’s function-calling guide documents the five-step loop (request with tools → tool call → execute → return output → final answer). Anthropic’s Messages streaming docs show the same weather tool under SSE with `input_json_delta` aggregation. Implementing both behind one interface teaches role/tool/stream divergences that multi-provider gateways must absorb.

URL: https://developers.openai.com/api/docs/guides/function-calling  
Companion: https://docs.anthropic.com/en/api/messages-streaming  
Fine-grained tools: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/fine-grained-tool-streaming  
Talk: https://www.youtube.com/watch?v=7MiFIhlkBoE (Patrick Dougherty, AI Engineer Summit)

---

## Open Questions

1. When should multi-provider apps standardize on OpenAI’s Responses item model vs keep provider-native shapes?  
2. How durable is OpenAI `system` vs `developer` equivalence across model generations?  
3. Do fine-grained Anthropic tool streams reduce end-to-end latency enough to justify partial-JSON parsers in every client?  
4. How should adapters treat OpenAI built-in tools vs Anthropic server tools for portable agent code?  
5. Is `tool_search` / deferred tool loading the long-term answer to giant MCP catalogs?

---

## Sources

- https://developers.openai.com/api/docs/guides/function-calling  
- https://docs.anthropic.com/en/api/messages-streaming  
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/fine-grained-tool-streaming  
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use  
- https://platform.claude.com/docs/en/build-with-claude/working-with-messages  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works.md  
- https://github.com/openai/openai-node/blob/master/examples/tool-calls-stream.ts  
- https://community.openai.com/t/how-is-developer-message-better-than-system-prompt/1062784  
- https://ai.engineer/talks/how-to-build-ai-agents-that-actually-work  
- https://www.youtube.com/watch?v=7MiFIhlkBoE  
