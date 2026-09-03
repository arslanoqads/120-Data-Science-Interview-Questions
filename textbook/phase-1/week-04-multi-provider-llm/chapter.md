# Chapter 4 — Multi-Provider LLM Engineering

> **Phase 1 — LLM Application Engineering Core**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-1/week-04-multi-provider-llm/`  
> **Syllabus Build:** Ship a provider-agnostic LLM client wrapper that swaps Anthropic, OpenAI, and (via an optional gateway such as LiteLLM) other/local backends behind one interface, with structured-output validation and automatic retries on malformed or semantically invalid results.

---

## Chapter framing

Phase 0 proved packaging, HTTP, tests, and shippability. Week 4 opens Phase 1 by making Deployment Copilot talk to real model providers correctly. Hiring screens for AI Engineer and Forward Deployed Engineer roles often ask you to flip a feature flag from OpenAI to Anthropic without rewriting the agent loop—or to explain why a one-character system-prompt edit spiked the bill.

The five ideas below are one pipeline: assemble a cache-stable prompt → count tokens → call with tools and a structured format → stream and aggregate → validate → append tool results → repeat. Skip any step and you get wrong roles, truncated tool JSON, context-window 400s mid-loop, or a cold cache after a “harmless” prefix edit.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) growing a thin `LLMClient` port with OpenAI and Anthropic adapters—optionally fronted by LiteLLM for failover—not framework-as-core and not raw SDK calls in every route.

---

### API mechanics: streaming, tools, roles (OpenAI + Anthropic)

* **Fundamentals:**  
  Both OpenAI and Anthropic expose chat-style APIs built around **role-tagged messages**, optional **tools**, and optional **streaming**. The application owns the loop: send messages (and tools) → receive text and/or tool calls → execute tools locally → append results → repeat until a final answer or stop condition.

  **OpenAI roles.** Chat Completions historically used `system`, `user`, `assistant`, plus `tool` for tool results. Newer models introduce a **`developer`** role. OpenAI’s Model Spec treats authority as layered: platform/system (OpenAI) > developer > user. In API practice, the caller’s system/developer message is **developer-authority** guidance—persona, output rules, tool policy—not the Spec’s platform “System” level, which only OpenAI can write. Practical mapping: `developer` / legacy `system` for app instructions; `user` for the end-user request; `assistant` for prior model turns; `tool` (Chat Completions) for results keyed by `tool_call_id`. The Responses API uses typed items (`function_call` / `function_call_output`) and often injects `instructions` as developer. o-series / GPT-5-family prefer `developer`; older models may reject or auto-convert. Adapters must tolerate both.

  **Anthropic roles.** The Messages API primarily uses `user` and `assistant` inside `messages`. **System instructions** go in a top-level `system` parameter (string or content blocks)—not a classic `"system"` role in `messages`. Tool results return as `tool_result` content blocks inside a subsequent **`user`** message, keyed by `tool_use_id`. Newer Claude models also allow mid-conversation `"role": "system"` messages after a user turn (not as the first entry), which preserves earlier prompt-cache prefixes because new system text is appended rather than rewriting the top-level `system` field.

  **Tool / function calling.** Client sends tool definitions (JSON Schema for arguments). The model may emit one or more tool calls (`tool_calls` / `function_call` on OpenAI; `tool_use` content blocks on Anthropic). The application executes tools and returns results; the model continues with a final answer or more calls. OpenAI distinguishes function tools, custom tools (free-form text), and platform built-ins (web search, code execution, MCP, and similar). Anthropic distinguishes **client tools** (you execute) vs **server tools** (Anthropic executes). Both support `tool_choice` / forced selection; both support `strict: true` on tool defs for schema-guaranteed args. OpenAI docs note functions are injected into the system message under the hood—definitions **count against context and are billed as input**. Large tool catalogs need truncation, namespaces, or tool search on supporting models.

  **Streaming.** OpenAI Chat Completions: `stream: true`; text as `delta.content`; tool calls as incremental `delta.tool_calls[index]` fragments aggregated by index. OpenAI Responses: typed SSE events (`response.function_call_arguments.delta`, `.done`, `response.output_item.added/done`). Anthropic: SSE (`message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, `message_stop`); for tools, `input_json_delta` carries `partial_json`, and final `tool_use.input` is complete. Fine-grained tool streaming (`eager_input_streaming: true` per tool) streams parameter values without buffering each value server-side—accumulated JSON may be invalid until stop.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Chat Completions (OpenAI) | Ubiquitous; many SDKs/examples | Older message/tool shapes; migration pressure toward Responses | Legacy chat UIs; broad ecosystem demos |
  | Responses API (OpenAI) | Typed items; cleaner agent loops; `previous_response_id` | Different event model; ecosystem still catching up | New OpenAI agentic work |
  | Anthropic Messages | Clear top-level `system`; strong tool/cache story | Role mapping differs; adapters mandatory for multi-provider | Claude-first or dual-provider products |
  | Non-streaming | Simpler parsers | Higher TTFT; worse UX for long generations | Batch jobs, offline extractors |
  | Streaming + tools | Lower perceived latency; progressive UI | Complex aggregation; partial JSON invalid until done | Interactive support / chat agents |
  | Forced `tool_choice` | Guarantees structured side-effect or extraction | Can block natural language; conflicts with some thinking modes | Extraction / mandatory tool turns |
  | Multi-provider façade only (LiteLLM, etc.) | Portability | Lowest-common-denominator features; subtle role/tool mismatches | Gateways—not a substitute for understanding wire shapes |

  For Deployment Copilot, prefer **provider adapters that normalize roles, tools, and stream events** into an internal message type. Use Responses for new OpenAI agentic paths when appropriate; keep Chat Completions where legacy chat UIs demand it. Expose retrieval as tools (`search_chunks`, `get_doc`) rather than only stuffing RAG into the system prompt—keeps the agent loop honest and the system prefix cacheable (see Prompt caching).

* **Failure Modes:**  
  - Mapping Anthropic top-level `system` to OpenAI roles wrong (or stuffing OpenAI `developer` into Anthropic `messages`) → instruction hierarchy bugs and cache misses.  
  - Streaming without index / `partial_json` aggregation → truncated args → failed tools → agent thrash.  
  - Returning Anthropic tool results as OpenAI `role: tool` without remapping → 400s.  
  - Ignoring that tool schemas burn context → mysterious window overflows.  
  - Mixing OpenAI built-in tools with Anthropic server tools in “portable” agent code without a capability matrix.  
  - Executing tools on incomplete streamed JSON; buffering the entire stream then parsing with no progressive UX.

* **Average vs. Strong Engineer:**  
  **Average:** copy-paste OpenAI Chat Completions examples; bolt Anthropic later; one giant system string with no separation of policy vs user data; buffer the whole stream or fire tools on partial JSON.  
  **Strong:** adapters normalize `system`/`developer` ↔ Anthropic `system`, tool result shapes, and stream events; prefer strict tool schemas; validate args in app code before side effects; gate destructive tools on human approval; log full tool traces (call id, name, args, latency, result size); keep stable policy in Anthropic’s top-level `system` and use mid-conversation system only when instructions become relevant later and cache prefixes must stay intact. Treat tool **response format** as part of the agent-computer interface—JSON vs XML can flip reliability by model family (ACI mindset from Dougherty / AI Engineer Summit).

* **Worked Example:**  
  Deployment Copilot’s support turn—“What’s the weather in San Francisco?”—exercises the five-step tool loop on both providers behind one interface. With the OpenAI adapter, the weather tool uses Chat Completions or Responses function calling and returns results as `role: tool` keyed by `tool_call_id`. Flip config to the Anthropic adapter: the same agent code runs, but the adapter places policy in top-level `system`, emits `tool_use` blocks, aggregates `input_json_delta` / `partial_json` until `content_block_stop`, and wraps results as `tool_result` inside a **user** message keyed by `tool_use_id`. A golden unit test asserts the mapped outbound payload shapes without live keys.

* **Apply It:**  
  1. Define an internal message/tool/event model that can represent both providers without leaking SDK types into routes.  
  2. Implement role mapping: OpenAI `developer`/`system` ↔ Anthropic top-level `system`; tool results `role: tool` ↔ `tool_result` in user content.  
  3. Implement stream aggregators that join OpenAI `delta.tool_calls[index]` fragments and Anthropic `partial_json` before tool execution.  
  4. Prefer `strict: true` tool schemas; validate args in app code before side effects.  
  5. Log tool traces (id, name, args size, latency, result size)—not raw secrets.  
  6. Keep a capability matrix for built-in/server tools; do not pretend they are portable.

---

### Structured output enforcement

* **Fundamentals:**  
  Downstream code needs typed objects—invoices, classifications, tool args, eval labels. Free-form generation routinely omits keys, invents enums, wraps JSON in markdown fences, or emits invalid JSON. Prompt-only “return JSON” is not an SLA.

  **OpenAI Structured Outputs** use constrained decoding via JSON Schema so the API generates responses that **adhere to the schema**—not merely valid JSON syntax. Chat Completions shape: `response_format` with `type: "json_schema"`, `strict: true`, and a named schema. Responses API uses `text.format` with `type: "json_schema"` and `strict: true`. This is distinct from older **JSON mode** (`type: "json_object"`), which guarantees JSON syntax but **not** schema adherence. Prefer Structured Outputs over JSON mode whenever available (gpt-4o snapshots and later; prefer current flagship for new work). Python/JS SDKs accept **Pydantic / Zod** via `.parse()` helpers that convert the model to a strict JSON Schema, call the API, and deserialize into a typed object (`message.parsed` / `output_parsed`). Docs call out reliable type-safety, fewer retries, and **explicit refusals** detectable separately from parse failures. Treat length / content_filter finish reasons as first-class failures, not silent empty parses.

  Two OpenAI surfaces for structure: Structured Outputs via **function/tool calling** (`strict` tools) when the model must call a tool or perform a side effect with typed args; Structured Outputs via **`json_schema` response format** when the model answers with a typed object (extraction, UI schema, chain-of-thought scaffolding).

  **Anthropic** offers complementary features: **JSON outputs** via `output_config.format` with `type: "json_schema"` (legacy/beta: `output_format`; SDKs may still accept the old name on `messages.parse()` and translate), and **strict tool use** (`strict: true` on tool definitions) guaranteeing tool names/inputs match schemas. Constrained decoding guarantees schema-compliant text/tool inputs. SDKs may transform unsupported schema constraints into description text and validate against the original schema. Older pattern: force a single extraction tool with `tool_choice` when native structured outputs were unavailable.

  **Pydantic / Zod as the contract.** Schema-as-code keeps API schema and application types synchronized. Field descriptions become soft guidance to the model; validators (`Field`, custom validators) enforce **business rules** after (or instead of) model-side constraints. One model per task; generate provider schemas from it—never hand-maintain divergent JSON Schema copies.

  **Retry-on-malformed (fallback path).** Classic pattern: prompt for JSON → `json.loads` → Pydantic validate → on failure, re-prompt with the error (“fix these fields…”) up to N times. Still needed when the model/provider lacks strict structured outputs, when using JSON mode only, when **semantic** validators fail even though syntax/schema pass (`end_date >= start_date`), or when output is truncated (`finish_reason: length` / `max_tokens`). With true structured outputs, syntax/schema retries largely disappear; semantic retries and refusal handling remain.

* **The Alternatives:**  

  | Technique | Guarantee | Cost / latency | When it fits |
  |-----------|-----------|----------------|--------------|
  | Prompt-only “return JSON” | None | Cheap | Throwaway exploration only |
  | JSON mode | Valid JSON | Low | Legacy; no schema adherence |
  | Structured Outputs / constrained decoding | Schema adherence | Slight overhead; schema compile/cache | Preferred when available |
  | Forced tool for extraction | Tool-arg shape | Extra tool machinery | Good fallback; mix with agent tools carefully |
  | Client retry + repair prompt | Best-effort | Multiplies cost | Semantic failures; unsupported providers/models |
  | Grammar / outlines (local models) | Strong local control | Infra complexity | Self-hosted path |

  Unsupported schema features vary by provider (numeric ranges, complex `oneOf`, deep recursion)—check each docs’ limitations list before designing contracts. `[NEEDS MORE RESEARCH]` for a durable cross-provider matrix of unsupported schema features and for when constrained decoding conflicts with extended thinking / high reasoning effort.

* **Failure Modes:**  
  - Markdown-fenced JSON breaks `json.loads` in CI only sometimes.  
  - Missing required keys → null pointer / silent default in business logic.  
  - Invented enum values → invalid state machine transitions.  
  - Agent tool args that “look right” but fail server validation → infinite retry loops.  
  - Eval labels / golden-set extractors that drift week to week → false eval progress.  
  - No distinction among refusal, truncation, and parse error.  
  - Duplicate hand-written JSON Schema in OpenAI and Anthropic configs that drift apart.

* **Average vs. Strong Engineer:**  
  **Average:** “Respond with JSON only” in the system prompt; strip fences with regex; hand-copy schemas per provider; treat empty parse as success.  
  **Strong:** one Pydantic/Zod model per task; generate OpenAI/Anthropic schemas from it; prefer strict structured outputs when supported; keep retry+repair for unsupported models and for semantic checks; treat refusals and length truncation as first-class outcomes; for agents use structured outputs for final answers and **strict tools** for side effects; log raw text + validation errors for offline improvement; version schemas (`schema_version` field or package version) so cached prompts and clients stay compatible.

* **Worked Example:**  
  A second Deployment Copilot path extracts a calendar event (`name`, `date`, `participants`) via structured outputs. The OpenAI adapter calls `responses.parse` / `chat.completions.parse` with a shared Pydantic schema—no manual `json.loads`. The Anthropic adapter uses `output_config.format` / `messages.parse()` for schema-guaranteed JSON text. On schema success, domain validators run (`end_date >= start_date` if present). On semantic failure, the client retries once with the validation error in the repair prompt; otherwise the result is dead-lettered. Side-effect tools (`create_ticket`, `deploy_action`) use `strict: true` tool defs, not free-form JSON in the same turn as unconstrained prose.

* **Apply It:**  
  1. Define one Pydantic (or Zod) model per extraction/classification task in the package domain layer.  
  2. Generate provider schemas from that model; ban divergent hand-maintained copies.  
  3. Wire strict Structured Outputs / strict tools in both adapters when the model supports them.  
  4. Implement retry-on-malformed for semantic validators and for models without strict mode (cap N; log each attempt).  
  5. Treat refusal and length truncation as distinct outcomes from parse failure.  
  6. Version schemas and log validation errors with raw text for offline improvement.

---

### Token counting and context windows

* **Fundamentals:**  
  Models consume **tokens**, not characters. Context windows are hard caps on (input + output) tokens; exceeding them fails the request or truncates. Pricing and rate limits are also token-based. Accurate **pre-flight counting** is required for budgeting, truncation, and `max_tokens` / `max_completion_tokens` planning.

  **OpenAI / tiktoken.** OpenAI’s open-source **tiktoken** mirrors BPE used by GPT models. Use `tiktoken.encoding_for_model(name)`. Typical encodings: `o200k_base` (gpt-4o / gpt-4o-mini family), `cl100k_base` (gpt-4, gpt-3.5-turbo, text-embedding-3-*), `p50k_base` / `r50k_base` (legacy Codex / GPT-3). Raw `len(encode(text))` **undercounts** chat calls: message framing adds overhead (`tokens_per_message`, name tokens, priming tokens). The OpenAI Cookbook’s `num_tokens_from_messages` estimates Chat Completions usage; tool definitions add further overhead (`num_tokens_for_tools`). Cookbook notes counts are **estimates** and may drift by snapshot—verify against live `usage.prompt_tokens` when calibrating. `[NEEDS MORE RESEARCH]` for a durable public formula for Responses API / GPT-5-family message framing overhead.

  **Anthropic token counting.** Prefer the official `POST /v1/messages/count_tokens` endpoint with the same payload shape as Messages (system, tools, images, PDFs, thinking config). Returns `input_tokens` without running inference; separate rate limits; generally free of message-creation charges. Tokenizer differs by model family—**re-count when migrating**. Claude 4.7+ / newer families: Anthropic documents ~**30% more tokens** for the same text vs earlier tokenizers on some workloads. Tool use adds system-side tokens for tool instructions; server tool counts apply specially on first sampling call.

  **Context management strategies** (combine in production): (1) **priority ordering**—system/policy first; then high-value reference; then history; then current user turn; (2) **sliding window**—last N turns or last K tokens of dialogue; (3) **summarization / compaction**—compress older turns (trades fidelity for space; can bust prompt caches); (4) **truncation**—hard drop from the middle or oldest non-critical content as backstop; (5) **retrieval**—keep a thin prompt; pull docs on demand outside the permanent window (agent tools). Reserve output budget: `available_output ≈ context_limit − input_tokens − safety_margin`. Set `max_tokens` / `max_completion_tokens` from that remainder—not a fixed 4096 on every call.

  **Long-context tradeoffs.** Huge windows (100K–1M+) reduce engineering pressure but raise cost, latency, and **lost-in-the-middle** risk. Retrieval + small window often beats stuffing a 200K context on both quality and cost for RAG. Multimodal tokens (images, PDFs, audio) dominate budgets—always count with provider-native tools, not character heuristics.

* **The Alternatives:**  

  | Method | Accuracy | Offline? | When it fits |
  |--------|----------|----------|--------------|
  | Character/word heuristics | Poor | Yes | Never for production budgets |
  | tiktoken local | High for OpenAI text | Yes | OpenAI adapter pre-flight (still estimate chat/tool overhead) |
  | Anthropic `count_tokens` | Highest for Claude payloads | Network | Anthropic adapter pre-flight |
  | Post-hoc `usage` from response | Exact billed | After call | Calibration—too late to prevent overflow |
  | Aggressive summarization | Saves tokens | — | When fidelity loss and cache invalidation are acceptable |
  | Huge context models only | Simple | — | Short-term prototypes; watch cost/latency/lost-in-the-middle |

* **Failure Modes:**  
  - Agent succeeds for 8 turns then dies when tool JSON history exceeds the window.  
  - `max_tokens` set too high → provider rejects or silently truncates mid-JSON (breaks structured outs).  
  - Switching Claude generations without recount → ~30% budget error.  
  - Image/PDF turns counted as “one message” → massive undercount.  
  - Summarization that rewrites the prompt prefix → destroys cache hit rates while “saving” tokens.  
  - Dropping system instructions first when over budget.  
  - Trusting UI “context %” or `len(prompt)//4`.

* **Average vs. Strong Engineer:**  
  **Average:** character heuristics; never reserve output budget; structured JSON truncates at the closing brace; no `count_tokens` on the client interface.  
  **Strong:** pre-flight count every request that can approach the window; fail soft with “context too large” UX; allocate budgets explicitly (e.g. system 10–20%, tools+schema fixed, retrieved docs capped, history residual, output reserved); prefer **drop or summarize tool results** before dropping system instructions; monitor p95 prompt tokens and cache hit rates together; re-benchmark when switching models; expose provider-agnostic `count_tokens(request) -> int` on the LLM port (OpenAI: tiktoken + overhead tables; Anthropic: `count_tokens` API). Cap retrieved chunk tokens separately from chat history; prefer tool-based retrieval over stuffing top-k forever; log `prompt_tokens`, `completion_tokens`, and cache fields on every span.

* **Worked Example:**  
  Before each Deployment Copilot completion, the port’s `count_tokens` runs. OpenAI path uses tiktoken plus Cookbook-style message/tool overhead estimates, calibrated occasionally against live `usage.prompt_tokens`. Anthropic path calls `count_tokens` with the same system + messages (+ tools/images) shape as `messages.create`. If over budget, the service summarizes oldest tool-result turns (not the system prefix), recounts, then streams with `max_tokens = window − input − margin`. Cap retrieved chunk tokens separately from chat history so RAG growth does not silently eat the reply budget.

* **Apply It:**  
  1. Add `count_tokens` to the `LLMClient` Protocol; implement per adapter.  
  2. Pre-flight count before calls that can approach the window; surface a clear client error when over budget.  
  3. Derive `max_tokens` / `max_completion_tokens` from remaining budget, not a fixed constant.  
  4. Prefer dropping/summarizing tool results before system instructions.  
  5. Cap retrieved-doc tokens separately from dialogue history.  
  6. Log usage fields on every call; re-count when migrating model families.

---

### Prompt caching

* **Fundamentals:**  
  Prompt caching stores **KV / prefix computation** for a reusable prompt prefix so later requests with a **byte-identical prefix** avoid recomputing it—lowering input cost and TTFT. Caches are typically **organization-scoped**, machine-local, and TTL-bound. Matching is exact-prefix: any change at position N invalidates everything after N.

  **What is cacheable (both providers, in spirit):** stable system/developer instructions, tool definitions, structured-output schemas, static few-shot blocks, large reference documents, and prior conversation turns that remain unchanged. Dynamic timestamps, per-user PII at the front, reordered tools, reshuffled few-shots, and compaction that rewrites history are **not** cache-friendly.

  **Anthropic.** Enable via top-level `cache_control: { type: "ephemeral" }` (**automatic** breakpoint on last cacheable block, advances as history grows) or per-block `cache_control` for **explicit** breakpoints. Prompt order for prefixes: **`tools` → `system` → `messages`** up to and including the breakpoint. Default TTL ~**5 minutes**, refreshed on use at no extra write cost; **1-hour** TTL available (`ttl: "1h"`) at higher write multipliers (~2× base input). Usage fields: `cache_creation_input_tokens`, `cache_read_input_tokens`, regular `input_tokens`. Published economics: cache write ≈ **1.25×** base input (5-min TTL); cache read ≈ **0.1×** (some newer models advertise even lower, e.g. 0.025×). Break-even often ~2 reads for 5-min writes. Announced latency cuts up to ~85% and cost cuts up to ~90% on long reused prompts. Minimum token thresholds are **model-dependent** (commonly 1,024–4,096; some newer families 512). Below minimum → silently no cache (both creation and read usage stay 0). Explicit breakpoints: writes happen **only at** your breakpoint; reads look backward (Claude API lookback window ~20 blocks). Place breakpoint on the **last shared stable block**, not on a per-request timestamp/user message. Max ~4 breakpoints. Automatic caching trap: if the last block changes every request, automatic mode writes useless unique prefixes—use explicit breakpoint on the static prefix instead.

  **OpenAI.** Enabled by default for supported models; monitor via Prompt Caching Dashboard. Cache stores **KV tensors**, not raw tokens. Full rendered context includes OpenAI-provided instructions, developer messages, tools, history, images/docs/audio where supported. Minimum cacheable length: **1,024** tokens for GPT-5.6+, **2,048** for many earlier models (hidden platform system tokens do **not** count toward minimum). Older reporting often rounds `cached_tokens` down to multiples of **128**. **GPT-5.6+:** optional **explicit** mode via `prompt_cache_options.mode` and per-block `prompt_cache_breakpoint`; writes **1.25×**, reads **0.1×**; TTL via `prompt_cache_options.ttl` (e.g. `30m`). Implicit mode places an end-of-latest-message breakpoint. Multiple explicit breakpoints (up to four writes) isolate stable vs volatile sections. Earlier models: implicit only; often no separate write surcharge; `cached_tokens` in usage; retention `in_memory` (~5–10 min idle) or extended `24h` where supported. Routing: caches live on machines; traffic >~**15 RPM** risks overflow. `prompt_cache_key` improves stickiness—keys influence routing; they do not pin or guarantee hits.

  **Few-shot placement.** Exact prefix matching means: static few-shots early (after tools/system) → high shared hit rate and stable style; dynamic per-request examples **after** the breakpoint → preserve hits on system+tools, pay for examples each time; dynamic examples **before** the breakpoint → destroy shared cache for everyone. Week 5 deepens selection policy; Week 4 owns the **layout constraint**: never insert volatile examples into the shared prefix without accepting a cold cache.

  **Not cache-friendly:** dynamic timestamps, per-user PII at the front of the prompt, reordered tools, reshuffled few-shots, compaction that rewrites history, changing `reasoning.effort` / structured schema / `parallel_tool_calls` / `tool_choice` settings that alter rendered instructions.

* **The Alternatives:**  

  | Strategy | When it wins | When it loses |
  |----------|--------------|---------------|
  | Automatic / implicit caching | Multi-turn chat; low ops burden | Uncontrolled writes of volatile tails (especially if writes cost extra) |
  | Explicit breakpoints | Stable prefix + volatile suffix; cost control | More instrumentation; easy to misplace breakpoints |
  | No caching | Tiny prompts; highly unique inputs | Leaves money/latency on the table for long shared prefixes |
  | Prompt shortening instead | Below min cache size; rare reuse | May hurt quality more than caching would save |
  | Extended TTL / 24h retention | Bursty traffic with long gaps | Higher write cost or retention policy constraints (ZDR) — `[NEEDS MORE RESEARCH]` for ZDR / data-residency interaction details in regulated industries |

* **Failure Modes:**  
  - “Caching enabled” but breakpoint after unique user message → pay write premium every time, zero shared hits.  
  - One-character system-prompt deploy → org-wide cold start and cost spike.  
  - Per-tenant PII in system → no cross-tenant reuse; privacy OK but economics wrong for shared policy.  
  - Summarization rewriting early history every N turns → perpetual misses.  
  - Too many `prompt_cache_key` values → fragmented routing / overflow misses.  
  - Automatic mode writing a unique prefix every turn because the last block always changes.  
  - Never inspecting `cache_read_*` / `cached_tokens` in dashboards.

* **Average vs. Strong Engineer:**  
  **Average:** flip caching on; leave prompt order random; put `Date.now()` in the system prompt for “freshness”; ignore cache usage fields.  
  **Strong:** structure prompts **stable → semi-stable → dynamic** (system + tools + static few-shots + docs, then user-specific, then latest user turn); put cache breakpoints **after** the last stable block; never after a unique user message if writes are billed; monitor hit rate dashboards and alert on miss spikes after prompt deploys; use `prompt_cache_key` (OpenAI) per product surface carefully—too many keys fragment routing, too few cause overflow contention; coordinate prompt versioning with caching (treat system-prompt edits as intentional cold-cache events); keep static few-shots early for hits and dynamic selection after the breakpoint when quality needs it. For RAG: cache system policy + tool schemas + static style examples; do **not** put per-query retrieved chunks in the shared prefix—fetch via tools or place after the breakpoint; keep tenant IDs out of the shared prefix hash unless isolation is required.

* **Worked Example:**  
  A third Deployment Copilot path loads a long system + tools + static few-shot prefix and proves cache hits on follow-ups. The Anthropic adapter sets an explicit `cache_control` breakpoint on the last stable system/tools block; the first request shows `cache_creation_input_tokens`, subsequent questions within TTL show `cache_read_input_tokens` at ~0.1× input rate. The OpenAI adapter keeps tools and developer instructions byte-stable, uses `prompt_cache_key` for the product surface (not per-user), and on GPT-5.6+ places an explicit breakpoint so volatile tool outputs do not force expensive writes. Retrieved chunks and the current user turn sit **after** the breakpoint. Usage logging normalizes Anthropic `cache_read_input_tokens` / `cache_creation_input_tokens` and OpenAI `cached_tokens` into one internal usage record.

* **Apply It:**  
  1. Layout prompts as stable → semi-stable → dynamic; document the declared cache breakpoint.  
  2. Pass cache-control / breakpoint fields through the LLM port (do not bury them only in one SDK call site).  
  3. Prefer explicit breakpoints when the last message changes every turn and writes are billed.  
  4. Keep retrieved chunks and per-user PII after the breakpoint (or via tools).  
  5. Normalize and log cache read/write usage on every span; alert on miss spikes after prompt deploys.  
  6. Treat system-prompt edits as intentional cold-cache events in the deploy checklist.

---

### Provider-agnostic client / wrapper interface

* **Fundamentals:**  
  Product code should not import `openai` and `anthropic` at every call site. Roles, tool result shapes, stream events, structured-output knobs, token counting, and cache fields all diverge (concepts above). A **provider-agnostic client** is the port that: (1) accepts a stable internal request (messages, tools, response schema, stream flag, cache hints); (2) adapts to OpenAI (Chat Completions and/or Responses) or Anthropic Messages; (3) emits a stable internal response (text, tool calls, usage including cache, finish reason); (4) is mockable in Week 2-style pytest without live keys.

  This is the Week 4 **syllabus build**: implement the port so mechanics, structured outs, tokens, and caching become shippable code—even when the bullet list names those topics separately.

  **Hand-rolled ports (recommended core).** Define a small Protocol / ABC, for example:

  ```python
  class LLMClient(Protocol):
      async def complete(self, req: LLMRequest) -> LLMResponse: ...
      async def stream(self, req: LLMRequest) -> AsyncIterator[LLMEvent]: ...
      async def count_tokens(self, req: LLMRequest) -> int: ...
  ```

  Implement `OpenAIAdapter` and `AnthropicAdapter` that map `developer`/`system` ↔ Anthropic top-level `system`; map tool results (`role: tool` ↔ `tool_result` in user content); aggregate streaming tool-arg deltas; attach structured-output / strict-tool flags; normalize usage (`cached_tokens` vs `cache_read_input_tokens`). Keep the internal type **minimal**—enough for your product—not a clone of either provider’s entire surface.

  **LiteLLM (library + gateway).** LiteLLM unifies 100+ providers behind the **OpenAI Chat Completions shape**: SDK `litellm.completion(model="anthropic/...", messages=..., tools=..., stream=True)`; responses always look like OpenAI `chat.completion` / chunks; maps provider exceptions to OpenAI exception types; **Router** for retries, fallbacks, load balancing; **Proxy / AI Gateway** for virtual keys, budgets, spend tracking, admin UI, OpenAI-compatible `base_url`. LiteLLM also documents function calling translation, streaming, and cross-provider prompt caching helpers—useful, but still an OpenAI-shaped façade over Anthropic semantics. That façade is the grounded path for routing to additional or **local** backends without inventing a third native adapter in this chapter—`[NEEDS MORE RESEARCH]` for Deployment Copilot–specific local model (ollama/vLLM/etc.) adapter semantics beyond LiteLLM’s OpenAI-compatible target.

  **What “agnostic” does not mean.** You cannot pretend OpenAI built-in tools ≡ Anthropic server tools, or that Responses item state ≡ Messages content blocks, without a capability matrix. Agnostic means: **one call site**, explicit feature flags, honest degradation—not infinite compatibility.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Hand-rolled Protocol + 2 adapters | Full control; clear semantics; easy to mock | You maintain stream/role edge cases | Syllabus default; product core |
  | LiteLLM SDK in-process | Fast multi-provider; fallbacks; cost callbacks | Dependency; LCD quirks; upgrade coupling | Prototypes; many providers / local via OpenAI shape |
  | LiteLLM Proxy gateway | Central keys/budgets/UI; any OpenAI client works | Ops surface; another hop; debugging transforms | Platform / multi-team |
  | OpenAI SDK only + Anthropic later | Speed | Lock-in; rewrite | Throwaway demos |
  | Heavy framework (LangChain, etc.) | Batteries | Opaque adapters; hard eval/debug | Only if the team already standardized |

  Hybrid common in industry: **hand-rolled port for app semantics** + optional LiteLLM/proxy for failover and spend controls. Week 5 (prompts) and Week 11+ (agents) assume you already understand the wire protocol—framework-as-core hides it.

* **Failure Modes:**  
  - Feature flags for model choice touch every service file.  
  - Unit tests need live keys or duplicated mocks per SDK.  
  - Streaming/tool bugs get fixed in one provider path only.  
  - Prompt-cache and token helpers diverge → cost regressions.  
  - Take-homes fail the “swap Anthropic under the hood” interview ask.  
  - LiteLLM used as a black box with no tests of role remapping.  
  - No `count_tokens` on the interface; no normalized usage logging.

* **Average vs. Strong Engineer:**  
  **Average:** `if provider == "openai": ... else: ...` sprinkled in route handlers; LiteLLM as an untested black box; product code imports SDKs directly.  
  **Strong:** Protocol in `src/<pkg>/llm/port.py`; adapters in `.../adapters/`; dependency-injected into FastAPI (Week 2 `dependency_overrides`); golden tests—same internal request → assert mapped Anthropic/OpenAI payloads (snapshot or contract); capability flags (`supports_structured_outputs`, `supports_prompt_cache_explicit`, `supports_server_tools`); usage normalized to `{input, output, cache_read, cache_write, model, provider}`; when adding a third model family, fix the **tool response format** in the adapter, not only the system prompt; treat a gateway as org enablement while keeping agent-loop ownership in your code.

* **Worked Example:**  
  Build `WeatherAgent` (and the calendar extraction path) behind `LLMClient`. With `OPENAI_ADAPTER`, weather uses Chat Completions/Responses function calling and `role: tool` results; structured extraction uses `.parse()` / `json_schema`. Flip config to `ANTHROPIC_ADAPTER`: same agent code; adapter places policy in top-level `system`, wraps tool results as `tool_result` user blocks, aggregates `partial_json`, and applies `output_config.format` / strict tools. Pre-flight `count_tokens` and cache breakpoint fields pass through on both paths. Pytest mocks the Protocol—never live keys in unit CI. Optionally point an adapter’s HTTP target at a LiteLLM proxy for spend limits and local/OpenAI-compatible backends without changing the Protocol.

  Syllabus build checklist mapped to this chapter:

  1. `LLMRequest` / `LLMResponse` / `ToolCall` dataclasses or Pydantic models.  
  2. OpenAI + Anthropic adapters with streaming aggregation.  
  3. Structured-output path wired to shared schemas + retry-on-malformed for semantic failures.  
  4. `count_tokens` pre-flight.  
  5. Cache-control / breakpoint fields pass-through.  
  6. Pytest mocks the Protocol—never live keys in unit CI.

* **Apply It:**  
  1. Add `LLMRequest` / `LLMResponse` / `ToolCall` / `LLMEvent` models and an `LLMClient` Protocol under `src/<package>/llm/`.  
  2. Implement OpenAI and Anthropic adapters with role, tool, stream, structured-output, token, and cache normalization.  
  3. Inject the client into FastAPI; swap adapters by config/feature flag.  
  4. Add golden/contract tests for mapped outbound payloads on both providers.  
  5. Normalize usage including cache fields; expose capability flags for honest degradation.  
  6. Optionally add a LiteLLM-backed adapter or proxy target for failover / local OpenAI-compatible backends—without moving agent-loop ownership into the gateway.

---

## Week 4 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Port:** Define `LLMClient` with `complete` / `stream` / `count_tokens` and minimal internal request/response types.  
2. **Roles & tools:** Map OpenAI ↔ Anthropic roles and tool-result shapes; aggregate streaming tool-arg deltas before execution.  
3. **Structured outs:** One Pydantic schema per task; strict provider modes when available; retry+repair for semantic failures and unsupported models.  
4. **Tokens:** Pre-flight count; budget output; truncate/summarize tool history before system instructions; log usage.  
5. **Caching:** Layout prompts stable → semi-stable → dynamic; pass breakpoints; log cache read/write; keep RAG chunks out of the shared prefix.  
6. **Swap:** Config-select OpenAI vs Anthropic adapters (optional LiteLLM gateway for failover/local OpenAI-compatible targets); pytest mocks the Protocol with no live keys.

When those six steps are true, Week 4 is done in the syllabus sense: Deployment Copilot can change providers under a feature flag, validate structured results, and explain every adapter choice with the wire-protocol facts above.

---

## Compilation notes

- All concept sections above are grounded in `research/phase-1/week-04-multi-provider-llm/` (`00`–`05`, README, `99-source-map`).  
- `[NEEDS MORE RESEARCH]` flags appear where research left open questions: durable cross-provider unsupported-schema matrix and constrained-decoding vs extended-thinking conflicts; durable Responses/GPT-5-family framing overhead formula; ZDR / data-residency interaction with extended cache retention; Deployment Copilot–specific local-model adapter semantics beyond LiteLLM’s OpenAI-compatible façade.  
- Outside URLs from research are not required reading to understand this chapter; operational detail was inlined from the notes.
