# Week 4 — Multi-Provider LLM APIs
> Phase 1 — LLM Application Engineering Core
> Raw research notes.

## Concept: Anthropic and OpenAI API mechanics (streaming, function/tool calling, system vs user vs assistant roles)

### Fundamentals

Both OpenAI and Anthropic expose chat-style APIs built around role-tagged messages, optional tools, and optional streaming. The shared mental model is an application-orchestrated loop: send messages (+ tools), receive text and/or tool calls, execute tools locally, append results, repeat.

**OpenAI roles and instruction hierarchy.** Chat Completions historically used `system`, `user`, and `assistant` (plus `tool` for tool results). Newer models introduce a `developer` role; OpenAI’s Model Spec treats authority as layered (platform system > developer > user). In API practice, the caller’s “system/developer” message is developer-authority guidance (persona, output rules, tool policy). User messages carry the end-user request at lower authority. Assistant messages are prior model turns; tool results are returned as `role: "tool"` (Chat Completions) or `function_call_output` items (Responses API). See OpenAI function-calling guide and community/Model Spec discussions of system vs developer.

**Anthropic roles.** The Messages API primarily uses `user` and `assistant` inside `messages`. System instructions go in a top-level `system` parameter (not a `"system"` role in the classic API). Tool results are returned as `tool_result` content blocks inside a subsequent `user` message, keyed by `tool_use_id`. Newer Claude models additionally allow mid-conversation `"role": "system"` messages after a user turn (not as the first entry), which preserves earlier prompt-cache prefixes because the new system text is appended rather than rewriting the top-level system field.

**Tool / function calling flow (both).**
1. Client sends tool definitions (JSON Schema for arguments).
2. Model may emit one or more tool calls (`tool_calls` / `function_call` on OpenAI; `tool_use` content blocks on Anthropic).
3. Application executes tools and returns results.
4. Model continues with a final answer or more tool calls.

OpenAI distinguishes function tools (JSON Schema args), custom tools (free-form text), and platform built-ins (web search, code execution, MCP, etc.). Anthropic distinguishes client tools (you execute) vs server tools (Anthropic executes, e.g. web search). Both support `tool_choice` / forced tool selection.

**Streaming.**
- OpenAI Chat Completions: `stream: true`; text arrives as `delta.content`; tool calls arrive as incremental `delta.tool_calls[index]` fragments that must be aggregated by index. Responses API uses typed SSE events (`response.function_call_arguments.delta`, `.done`, `response.output_item.added/done`).
- Anthropic: `stream: true` yields SSE events (`message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, `message_stop`). For tools, `input_json_delta` events carry `partial_json` fragments; final `tool_use.input` is a complete object. Fine-grained tool streaming (`eager_input_streaming: true` per tool) streams parameter values without buffering each value server-side.

### Alternatives & Tradeoffs

| Approach | Pros | Cons |
| --- | --- | --- |
| Chat Completions (OpenAI) | Ubiquitous; many SDKs/examples | Older message/tool shapes; migration pressure toward Responses |
| Responses API (OpenAI) | Typed items, cleaner agent loops, `previous_response_id` | Different event model; ecosystem still catching up |
| Anthropic Messages | Clear system top-level; strong tool/cache story | Role mapping differs from OpenAI; adapters needed for multi-provider |
| Non-streaming | Simpler parsers | Higher TTFT; worse UX for long generations |
| Streaming + tools | Lower perceived latency; progressive UI | Complex aggregation; partial JSON may be invalid until done |
| Forced `tool_choice` | Guarantees structured side-effect or extraction | Can block natural language answers; conflicts with some thinking modes |
| Multi-provider abstraction (LiteLLM, etc.) | Portability | Lowest-common-denominator features; subtle role/tool mismatches |

### Necessity

Production LLM apps almost always need: (1) correct role placement so instructions outrank user text, (2) a reliable tool loop for external data/actions, and (3) streaming for interactive products. Mis-mapping Anthropic’s top-level `system` to an OpenAI-style system message role (or vice versa) is a common integration bug. Tool streaming without aggregation causes truncated arguments and failed tool executions.

### Industry Practice

- Separate **provider adapters** that normalize roles (`system`/`developer` ↔ Anthropic `system`), tools, and stream events into an internal message type.
- Prefer **strict tool schemas** and validate arguments in application code before executing side effects; gate destructive tools on human approval.
- Use Responses API / Agents SDK for new OpenAI agentic work; keep Chat Completions for legacy chat UIs.
- Anthropic: put stable policy in top-level `system`; use mid-conversation system only when instructions become relevant later and cache prefixes must stay intact.
- Log full tool traces (call id, name, args, latency, result size) for debugging agent loops.

### Concrete Scenario

A support agent must answer “What’s the weather in San Francisco?” with a live tool. OpenAI’s function-calling guide documents the five-step loop (request with tools → tool call → execute → return output → final answer). Anthropic’s Messages streaming docs show the same weather tool under SSE with `input_json_delta` aggregation. Implementing both behind one interface teaches role/tool/stream divergences that multi-provider gateways must absorb.

URL: https://developers.openai.com/api/docs/guides/function-calling  
Companion: https://docs.anthropic.com/en/api/messages-streaming

### Open Questions

- When should multi-provider apps standardize on OpenAI’s Responses item model vs keep provider-native shapes?
- How durable is OpenAI `system` vs `developer` equivalence across model generations?
- Do fine-grained Anthropic tool streams reduce end-to-end latency enough to justify partial-JSON parsers in every client?
- How should adapters treat OpenAI built-in tools vs Anthropic server tools for portable agent code?

### Sources

- https://developers.openai.com/api/docs/guides/function-calling
- https://docs.anthropic.com/en/api/messages-streaming
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/fine-grained-tool-streaming
- https://platform.claude.com/docs/en/build-with-claude/working-with-messages
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works.md
- https://github.com/openai/openai-node/blob/master/examples/tool-calls-stream.ts
- https://ai.engineer/talks/how-to-build-ai-agents-that-actually-work (Patrick Dougherty, AI Engineer Summit 2025 — ACI / JSON vs XML tool payloads by model)


## Concept: Structured output enforcement (JSON schema, Pydantic-validated responses, retry-on-malformed)

### Fundamentals

**Problem.** Downstream code needs typed objects (invoices, classifications, tool args). Free-form generation routinely omits keys, invents enums, or emits invalid JSON.

**OpenAI Structured Outputs.** With `response_format: { type: "json_schema", json_schema: { strict: true, schema: ... } }`, the API uses constrained decoding so generations adhere to the schema (not merely “valid JSON”). Distinct from older JSON mode (`type: "json_object"`), which guarantees JSON syntax but not schema adherence. Python/JS SDKs accept Pydantic/Zod models via `.parse()` helpers that (1) convert the model to a strict JSON Schema, (2) call the API, (3) deserialize into a typed object (`message.parsed`). Refusals are detectable separately from parse failures.

**Anthropic Structured Outputs.** Two complementary features: (1) JSON outputs via `output_config.format` with `type: "json_schema"` (SDK helpers may still accept `output_format`); (2) strict tool use (`strict: true` on tool definitions) guaranteeing tool names/inputs match schemas. SDKs may transform unsupported schema constraints into description text and validate against the original schema. Older pattern: force a single extraction tool with `tool_choice` when native structured outputs were unavailable.

**Pydantic / Zod as the contract.** Schema-as-code keeps API schema and application types synchronized. Field descriptions become soft guidance to the model; validators (`Field`, custom validators) enforce business rules after (or instead of) model-side constraints.

**Retry-on-malformed (pre-structured / fallback path).** Classic pattern: prompt for JSON → `json.loads` → Pydantic validate → on failure, re-prompt with the error (“fix these fields: …”) up to N times. Still needed when: model/provider lacks strict structured outputs; using JSON mode only; semantic validators fail even when syntax/schema pass; or output is truncated (`finish_reason: length`). With true structured outputs, syntax/schema retries largely disappear; semantic retries and refusal handling remain.

### Alternatives & Tradeoffs

| Technique | Guarantee | Cost / latency | Notes |
| --- | --- | --- | --- |
| Prompt-only “return JSON” | None | Cheap | Production-fragile |
| JSON mode | Valid JSON | Low | No schema adherence |
| Structured Outputs / constrained decoding | Schema adherence | Slight overhead; schema compile/cache | Preferred when available |
| Forced tool for extraction | Tool-arg shape | Extra tool machinery | Good fallback; mixes with agent tools carefully |
| Client retry + repair prompt | Best-effort | Multiplies cost | Keep for semantic validation failures |
| Grammar / outlines (local models) | Strong local control | Infra complexity | Self-hosted path |

### Necessity

Any pipeline that writes to a database, triggers workflows, or feeds another agent step needs machine-checkable outputs. Prompt-only formatting is insufficient for SLAs. Structured Outputs reduce retry loops and simplify prompts (“Extract the event” vs long JSON recipes).

### Industry Practice

- Define **one Pydantic/Zod model per task**; generate OpenAI/Anthropic schemas from it; never hand-maintain divergent JSON Schema copies.
- Prefer **strict structured outputs** when the model supports them; keep a **retry+repair** path for providers/models that don’t, and for semantic checks (e.g., `end_date >= start_date`).
- Treat refusals and length truncation as first-class outcomes (OpenAI `.parse()` raises on length/content_filter finish reasons).
- For agents: use structured outputs for final answers; use strict tools for side effects; avoid asking the model to free-form JSON in the same turn as unconstrained prose.
- Log raw text + validation errors for offline prompt/schema improvement.

### Concrete Scenario

OpenAI’s Structured Outputs guide shows extracting a calendar event (`name`, `date`, `participants`) via `chat.completions.parse` with a Zod/Pydantic schema—no manual `json.loads`. Anthropic’s structured outputs docs show the parallel `output_config.format` / `messages.parse()` path for schema-guaranteed JSON text. A production extraction service would: call parse → on schema success run domain validators → on semantic failure retry once with the validation error → else dead-letter.

URL: https://developers.openai.com/api/docs/guides/structured-outputs  
Companion: https://platform.claude.com/docs/en/build-with-claude/structured-outputs

### Open Questions

- Which schema features remain unsupported across providers (numeric ranges, complex `oneOf`, recursive types)?
- When do constrained decoding and extended thinking / high reasoning effort conflict?
- Is repair-prompting still worth it once strict mode is on, or only for semantic validators?
- How to version schemas so cached prompts and client types stay compatible?

### Sources

- https://developers.openai.com/api/docs/guides/structured-outputs
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://github.com/openai/openai-python/blob/main/helpers.md
- https://dida.do/blog/structured-outputs-with-openai-and-pydantic
- https://thomas-wiegold.com/blog/claude-api-structured-output/
- https://claudecertificationguide.com/learn/4-prompt-engineering/4-3-structured-output


## Concept: Token counting and context window management

### Fundamentals

Models consume **tokens**, not characters. Context windows are hard caps on (input + output) tokens; exceeding them fails the request or truncates. Pricing and rate limits are also token-based. Accurate pre-flight counting is required for budgeting, truncation, and `max_tokens` / `max_completion_tokens` planning.

**OpenAI / tiktoken.** OpenAI’s open-source `tiktoken` mirrors BPE used by GPT models. Use `tiktoken.encoding_for_model(name)` (e.g. `o200k_base` for gpt-4o family, `cl100k_base` for gpt-4/3.5). Raw `len(encode(text))` undercounts chat calls: message framing adds overhead (`tokens_per_message`, name tokens, priming tokens). The OpenAI Cookbook’s `num_tokens_from_messages` estimates Chat Completions usage; tool definitions add further overhead (`num_tokens_for_tools`). Cookbook notes counts are estimates and may drift by snapshot.

**Anthropic token counting.** Prefer the official `POST /v1/messages/count_tokens` endpoint with the same payload shape as Messages (system, tools, images, PDFs, thinking config). Returns `input_tokens` without running inference; separate rate limits; generally free of message-creation charges. Tokenizer differs by model family—re-count when migrating. Tool use adds system-side tokens for tool instructions.

**Context management strategies (combined in production):**
1. **Priority ordering** — system/policy first; then high-value reference; then history; then current user turn.
2. **Sliding window** — keep last N turns or last K tokens of dialogue.
3. **Summarization / compaction** — compress older turns into a summary (trades fidelity for space; can bust prompt caches).
4. **Truncation** — hard drop from the middle or oldest non-critical content as backstop.
5. **Retrieval** — keep a thin prompt; pull docs on demand outside the permanent window.

Reserve output budget: `available_output ≈ context_limit − input_tokens − safety_margin`.

### Alternatives & Tradeoffs

| Method | Accuracy | Offline? | Notes |
| --- | --- | --- | --- |
| Character/word heuristics | Poor | Yes | Overflows easily |
| tiktoken local | High for OpenAI text | Yes | Chat/tool overhead still estimated |
| Anthropic `count_tokens` | Highest for Claude payloads | Network | Includes tools/images/PDFs |
| Post-hoc `usage` from response | Exact billed | After call | Too late to prevent overflow |
| Aggressive summarization | Saves tokens | — | Loses detail; cache invalidation |
| Huge context models only | Simple | — | Cost/latency; “lost in the middle” |

### Necessity

Without counting: surprise 400s, truncated answers, runaway cost, and broken agent loops when tool transcripts grow unbounded. Multi-turn agents and RAG pipelines are especially sensitive.

### Industry Practice

- Pre-flight count every request that can approach the window; fail soft with “context too large” UX.
- Allocate budgets explicitly (e.g. ~system 10–20%, tools+schema fixed, retrieved docs capped, history residual, output reserved).
- Prefer **drop or summarize tool results** before dropping system instructions.
- Monitor p95 prompt tokens and cache hit rates together—summarization that rewrites prefixes kills caching savings.
- When switching models, re-benchmark token counts (Anthropic docs note ~30% tokenizer shifts across some generations).

### Concrete Scenario

OpenAI Cookbook “How to count tokens with Tiktoken” verifies `num_tokens_from_messages` against live `usage.prompt_tokens` for chat messages (and a second recipe for tools). Anthropic’s token-counting guide shows `count_tokens` with system + messages (+ tools/images) returning `input_tokens` before `messages.create`. A chat backend can: count → if over budget, summarize oldest turns → recount → stream completion with `max_tokens = window − input − margin`.

URL: https://developers.openai.com/cookbook/examples/how_to_count_tokens_with_tiktoken  
Companion: https://platform.claude.com/docs/en/build-with-claude/token-counting

### Open Questions

- What is the durable public formula for Responses API / GPT-5-family message framing overhead?
- How should compaction APIs expose “cache-safe” summaries that preserve prefix hashes?
- Best practice for counting multimodal tokens (images, audio, PDFs) across providers in one gateway?
- When does retrieval+small-window outperform stuffing a 200K context on quality and cost?

### Sources

- https://developers.openai.com/cookbook/examples/how_to_count_tokens_with_tiktoken
- https://platform.claude.com/docs/en/build-with-claude/token-counting
- https://github.com/openai/tiktoken
- https://galileo.ai/blog/tiktoken-guide-production-ai
- https://sureprompts.com/blog/context-window-management-strategies


## Concept: Prompt caching mechanics (what's cacheable, cache-hit economics)

### Fundamentals

Prompt caching stores **KV / prefix computation** for a reusable prompt prefix so later requests with a **byte-identical prefix** avoid recomputing it—lowering input cost and TTFT. Caches are typically **organization-scoped**, machine-local, and TTL-bound. Matching is exact-prefix: any change at position N invalidates everything after N.

**Anthropic.**
- Enable via top-level `cache_control: { type: "ephemeral" }` (automatic breakpoint on last cacheable block, advances as history grows) or per-block `cache_control` for explicit breakpoints.
- Cacheable: system prompts, large documents/context, tool definitions, stable few-shot blocks, prior turns—anything in the rendered prefix up to the breakpoint.
- Default TTL ~5 minutes, refreshed on use at no extra write cost; longer TTLs (e.g. 1-hour) available with higher write multipliers.
- Usage fields: `cache_creation_input_tokens`, `cache_read_input_tokens`, regular `input_tokens`.
- Economics (classic published rates): cache write ≈ **1.25×** base input (5-min TTL); cache read ≈ **0.1×** base input (some newer models advertise even lower read rates). Break-even often ~2 reads for 5-min TTL writes. Announced latency cuts up to ~85% and cost cuts up to ~90% on long reused prompts.
- Minimum token thresholds apply (model-dependent); tools/system order matters for prefix stability.

**OpenAI.**
- Automatic for eligible models (`gpt-4o` and newer historically); prefix must meet minimum length (commonly **1,024** visible tokens for GPT-5.6+, **2,048** for many earlier models), with hits in **128-token** increments on older reporting.
- Cacheable rendered context includes developer/system messages, tools, structured-output schemas, conversation history, images/audio where supported. Hidden platform system tokens may not count toward the minimum.
- GPT-5.6+: optional **explicit** mode via `prompt_cache_options.mode` and per-block `prompt_cache_breakpoint`; writes charged **1.25×**, reads **0.1×**; TTL via `prompt_cache_options.ttl` (e.g. `30m`). Implicit mode still places an end-of-latest-message breakpoint.
- Earlier models: implicit only; often no separate write surcharge; `cached_tokens` in usage; retention `in_memory` (~5–10 min idle) or extended `24h` where supported.
- Routing: caches live on machines; `prompt_cache_key` improves stickiness under load (>~15 RPM overflow risk). Prefix hash of early tokens (+ tools) drives routing.

**What’s NOT cache-friendly.** Dynamic timestamps, per-user PII at the front of the prompt, reordered tools, reshuffled few-shots, compaction that rewrites history, changing `reasoning.effort` / structured schema / parallel_tool_calls settings that alter rendered instructions.

### Alternatives & Tradeoffs

| Strategy | When it wins | When it loses |
| --- | --- | --- |
| Automatic / implicit caching | Multi-turn chat; low ops burden | Uncontrolled writes of volatile tails (esp. if writes cost extra) |
| Explicit breakpoints | Stable prefix + volatile suffix; cost control | More instrumentation; easy to misplace breakpoints |
| No caching | Tiny prompts; highly unique inputs | Leaves money/latency on table for long shared prefixes |
| Prompt shortening instead | Below min cache size; rare reuse | May hurt quality more than caching would save |
| Extended TTL / 24h retention | Bursty traffic with long gaps | Higher write cost or retention policy constraints (ZDR) |

### Necessity

Long system prompts, RAG corpora in-context, tool catalogs, and multi-turn agents make uncached input the dominant bill. Caching is often the highest-ROI infra change after choosing the right model size—**if** prefixes are designed for stability.

### Industry Practice

- Structure prompts as **stable → semi-stable → dynamic** (system + tools + static few-shots + docs, then user-specific, then latest user turn).
- Put cache breakpoints **after** the last stable block; never after a unique user message if writes are billed.
- Monitor hit rate dashboards (`cached_tokens` / Anthropic cache read vs creation). Alert on sudden miss spikes after prompt deploys.
- Use `prompt_cache_key` (OpenAI) per product surface or tenant shard carefully—too many keys fragment routing; too few cause overflow contention.
- Coordinate prompt versioning with caching: a one-character system-prompt change is a full cold start for that prefix.
- Few-shot examples: keep them static and early for hits; dynamic example selection trades quality for cache misses (see Week 5).

### Concrete Scenario

Anthropic’s prompt-caching launch post and docs describe caching a large literary-analysis system prompt: first request pays cache write; subsequent theme questions within TTL pay cache read (~10% input rate) with large latency drops. OpenAI’s prompt-caching guide and Cookbook “Prompt Caching 201” emphasize exact prefix match, 1024+ tokens, preserving history, stable tools, and `prompt_cache_key` for routing—plus GPT-5.6 explicit breakpoints so volatile tool outputs don’t force expensive writes.

URL: https://platform.claude.com/docs/en/build-with-claude/prompt-caching  
Companions: https://developers.openai.com/api/docs/guides/prompt-caching · https://www.anthropic.com/news/prompt-caching · https://openai.com/index/api-prompt-caching/ · https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb

### Open Questions

- How should multi-tenant SaaS choose `prompt_cache_key` granularity without fragmenting hit rates?
- Best pattern for “keep-alive” refreshes vs paying longer TTL write premiums?
- Can explicit breakpoints fully isolate per-user RAG chunks without sacrificing shared system+tool cache?
- How do providers’ ZDR / data-residency policies interact with extended cache retention in regulated industries?

### Sources

- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://www.anthropic.com/news/prompt-caching
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://openai.com/index/api-prompt-caching/
- https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb
- https://github.com/anthropics/skills/blob/main/skills/claude-api/shared/prompt-caching.md
- https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html
