# Week 11 — Agent fundamentals: loop, tools, selection, retries, stop conditions

> Phase 3 — Agentic Systems  
> Raw research notes (not textbook prose). Legal sources only; no pirated books.

---

## Concept: The agent loop (plan → act → observe → repeat) and why naive `while True` collapses

### Fundamentals
An **agent loop** is the multi-turn conversation between your application and a model in which the model may request tools, your code executes them, results are fed back, and the model continues until it produces a final answer (or a guardrail stops it). OpenAI documents this as a five-step flow: (1) request with tools, (2) receive tool call(s), (3) execute application-side code, (4) send tool output back, (5) receive final response **or more tool calls** — and “continue this flow for as many tool calls as the task requires” ([Function calling](https://developers.openai.com/api/docs/guides/function-calling)). Anthropic’s equivalent: Claude returns `stop_reason: "tool_use"` with `tool_use` blocks; your app runs the tool and replies with `tool_result` in a user message; repeat until Claude stops calling tools ([Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

The popular slogan **plan → act → observe → repeat** (ReAct-style) maps onto this API loop: “plan” is the model’s reasoning + tool choice, “act” is tool execution, “observe” is injecting `tool_result` / `function_call_output` into context. Anthropic’s SDK **tool runner** automates that cycle and stops when Claude returns without tool use, or when `max_iterations` is hit ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)).

A **naive `while True`** that only checks “did the model ask for a tool?” fails in production because:

1. **No iteration budget** — models can oscillate (retry same tool, tool thrashing, or endless “one more search”).
2. **No token / cost / wall-clock budget** — context grows every turn; each iteration is another billable completion.
3. **No typed stop reasons** — you must branch on `end_turn` / `stop` / `max_tokens` / `refusal` / etc., not only “no tool call.”
4. **Side-effect tools are not idempotent** — unbounded retries can double-charge, double-email, or corrupt state.
5. **Missing tool_result pairing** — Anthropic returns HTTP 400 if `tool_use` ids lack matching `tool_result` blocks immediately after ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).
6. **Partial / parallel / server-tool mixes** — Responses API and Claude both allow multiple calls per turn and hosted tools; a toy loop mishandles ordering and unresolved server tools.

### Alternatives & Tradeoffs
| Approach | Pros | Cons |
|----------|------|------|
| Manual message loop | Full control (HITL, logging, custom transport) | Easy to get pairing/ordering wrong; you own retries |
| SDK tool runner / Agents SDK | Handles loop, validation, iteration caps | Less transparent; beta APIs can change |
| Graph frameworks (LangGraph) | Explicit edges, recursion limit, checkpoints | Heavier than a single ReAct loop for simple tools |
| “Always one tool then stop” | Predictable cost | Cannot solve multi-step tasks |

Tradeoff: demos love unbounded ReAct; production needs **hard caps** (iterations, tokens, dollars, time) plus **semantic stop** (goal achieved / user asked to stop / policy deny).

### Necessity
Without an explicit loop contract, agents either hang (cost explosions), crash on 400s from unpaired tool results, or silently stop mid-task when `max_tokens` truncates a tool call. Anthropic’s cookbook notes that a production loop must handle token-capped turns, unknown tool names, and malformed args — not only the happy path ([Zoom tool cookbook](https://platform.claude.com/cookbook/multimodal-crop-tool)).

### Industry Practice
- **Common:** `while True` until no `tool_calls`; hope for the best; no metrics.
- **Senior:** max iterations (often 5–25 depending on domain); per-tool and global timeouts; structured stop taxonomy; trace each turn; use tool runner / Agents SDK when you don’t need custom control; escalate to graphs when branching/HITL/persistence matter. Anthropic documents preferring the tool runner for custom-tool agents and dropping to a manual loop only for transport/custom shapes ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)).

### Concrete Scenario
Anthropic’s multimodal “zoom” cookbook drives an agentic crop-tool loop via `client.beta.messages.toolRunner(..., max_iterations=20)` as an explicit guard against runaway loops, and shows the equivalent manual loop with dispatch-by-name and `is_error` recovery: https://platform.claude.com/cookbook/multimodal-crop-tool  
OpenAI’s function-calling guide’s multi-step flow (request → tool call → execute → tool output → continue): https://developers.openai.com/api/docs/guides/function-calling

### Open Questions
- When should “plan” be a separate LLM call (planner–executor) vs implicit in one ReAct model?
- Is `max_iterations` enough, or do production systems need budgeted **tool-call trees** with per-branch caps?
- How do hosted server tools (web search, code execution) change loop design when the provider owns part of the act/observe path?

### Sources
- https://developers.openai.com/api/docs/guides/function-calling
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner
- https://platform.claude.com/cookbook/multimodal-crop-tool

---

## Concept: Tool / function calling schemas

### Fundamentals
A **tool schema** is a machine-readable contract telling the model (1) what tools exist, (2) when to use them (natural-language `description`), and (3) what JSON arguments are allowed (`parameters` / `input_schema`, typically JSON Schema).

**OpenAI (Responses API):** tools are flat function definitions with `type: "function"`, `name`, `description`, `parameters` (JSON Schema object), and often `strict: true` so arguments match the schema. Tool calls appear as `function_call` output items; you return `function_call_output` correlated by `call_id` ([Function calling](https://developers.openai.com/api/docs/guides/function-calling), [Migrate to Responses](https://developers.openai.com/api/docs/guides/migrate-to-responses)).

**Anthropic (Messages API):** tools take `name`, `description`, and `input_schema`. Claude emits `tool_use` content blocks (`id`, `name`, `input`); you reply with `tool_result` (`tool_use_id`, `content`, optional `is_error`). Client tools run in your app; server tools (`web_search`, `code_execution`, `tool_search`, …) run on Anthropic’s infra ([Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)). `strict: true` guarantees schema-valid inputs ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

**Schema design levers:** required vs optional fields; enums; `additionalProperties: false`; clear parameter descriptions; whether to allow parallel tool use (`disable_parallel_tool_use` on Claude; parallel function calls on OpenAI).

### Alternatives & Tradeoffs
- **Loose schema + post-validation:** flexible; model invents args; more repair loops.
- **Strict schema:** fewer invalid calls; harder for optional/complex unions; may need schema redesign.
- **Custom / free-form tools (OpenAI):** free text in/out when JSON Schema is a poor fit; less structure for deterministic executors.
- **Hosted / built-in tools:** less code; less control over execution environment and data residency.
- **MCP-wrapped tools:** same JSON-Schema-ish surface, but discovery/transport standardized (Week 12).

Tradeoff: richer schemas improve disambiguation but consume prompt tokens and can confuse the model when many near-duplicate tools share similar parameter names.

### Necessity
Without a precise schema + description, the model hallucinates parameters, omits required fields, or never calls the tool. Anthropic: invalid/missing params → Claude retries 2–3 times then apologizes; strict mode eliminates that class of failure ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). Unpaired or misordered results are hard API errors, not soft model mistakes.

### Industry Practice
- **Common:** copy `get_weather` examples; vague descriptions (“gets data”); no `strict`.
- **Senior:** description encodes **when to use / when not to use**; parameter docs include formats and examples; `strict`/Structured Outputs where supported; version tool names; keep schemas in code next to executors; treat tool results as **untrusted** (indirect prompt injection) — keep them in `tool_result` blocks, not system prompts ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

### Concrete Scenario
OpenAI’s end-to-end `get_horoscope` example: define function tool with JSON Schema + `strict: true`, execute locally, return `function_call_output` with matching `call_id`, then get the final natural-language answer: https://developers.openai.com/api/docs/guides/function-calling  
Anthropic’s `get_weather` client-tool round trip with `input_schema` and `tool_result`: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

### Open Questions
- Will “programmatic tool calling” (model writes a script that calls tools inside a sandbox) displace per-turn JSON tool calls for high-churn workflows?
- How much schema complexity can models reliably follow before tool-search / deferred loading becomes mandatory?

### Sources
- https://developers.openai.com/api/docs/guides/function-calling
- https://developers.openai.com/api/docs/guides/migrate-to-responses
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls

---

## Concept: Tool selection and disambiguation when many tools look similar

### Fundamentals
**Tool selection** is the model’s decision of which named capability to invoke given the user goal and the tool list in context. Failures look like: calling the wrong twin tool (`search_tickets` vs `search_kb`), calling none when one is needed, or calling many overlapping tools in parallel.

Disambiguation techniques documented by vendors:

1. **Better descriptions** — Anthropic’s guidance when Claude picks wrong tools: improve `description` specificity ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) → “Define tools”).
2. **Fewer tools in context** — large catalogs dilute attention and burn tokens.
3. **Tool search / deferred loading** — OpenAI `tool_search` (gpt-5.4+): mark functions/MCP with `defer_loading: true`; model searches and loads only needed tools; hosted or client-executed search ([Tool search](https://developers.openai.com/api/docs/guides/tools-tool-search)). Anthropic similarly exposes server-side `tool_search`.
4. **Namespaces / grouping** — OpenAI Agents SDK: `tool_namespace()` and defer_loading on function tools ([Agents SDK tools](https://openai.github.io/openai-agents-python/tools/)).
5. **Router / multi-agent** — instead of 80 tools on one agent, specialize agents (Week 13) so each sees a small palette.
6. **`tool_choice` constraints** — force a tool, force “any tool,” or auto; Claude can disable parallel use to reduce shotgun calling ([Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)).

### Alternatives & Tradeoffs
| Strategy | When it helps | Cost |
|----------|---------------|------|
| Rewrite descriptions | Near-duplicate names | Human curation time |
| Deferred tool search | 20–100+ tools | Extra latency; model/version requirements |
| Multi-agent split | Distinct domains (billing vs search) | Orchestration complexity |
| Always `tool_choice: required` | Forms / known workflows | Breaks chitchat / refusal paths |
| Embeddings over tool docs | Dynamic enterprise catalogs | Custom infra; not first-party |

Tradeoff: one mega-agent is simpler to ship; selection quality collapses as tools grow — the industry response is **retrieval over tools**, not infinite prompt stuffing.

### Necessity
Ambiguous tools → wrong side effects (refund vs cancel), wasted API calls, and user-visible thrashing. With deferred loading, wrong search queries can still load an irrelevant subset — selection quality becomes a product of both the search index and the descriptions.

### Industry Practice
- **Common:** dump all CRM/Jira/Slack tools into one agent; debug with “please use X” prompt hacks.
- **Senior:** inventory tools; merge duplicates; encode mutual exclusion in descriptions; adopt tool_search past ~20–30 tools; route by intent to specialized agents; eval tool-choice accuracy on golden prompts (Phase 3 Week 15).

### Concrete Scenario
OpenAI Tool search docs: add `tool_search`, set `defer_loading: true` on rarely used functions/MCP servers so definitions are not all loaded up front — reducing tokens and improving selection among large inventories: https://developers.openai.com/api/docs/guides/tools-tool-search  
AI Engineer Summit MCP workshop (Anthropic) discusses MCP + agents and ecosystem tooling surfaces: https://youtu.be/kQmXtrmQ5Zg

### Open Questions
- Is tool search “RAG for tools” enough, or do enterprises need typed capability registries with auth scopes?
- Should disambiguation be model-side (better LLMs) or system-side (routers, allowlists per tenant)?

### Sources
- https://developers.openai.com/api/docs/guides/tools-tool-search
- https://openai.github.io/openai-agents-python/tools/
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
- https://youtu.be/kQmXtrmQ5Zg

---

## Concept: Error handling and retry logic for tool failures

### Fundamentals
Tool failures fall into classes:

1. **Execution errors** — network, 5xx, timeouts, business-rule rejects.
2. **Invalid model arguments** — missing fields, wrong types (less common with `strict`).
3. **Unknown tool name** — model hallucinated a tool.
4. **Provider/server-tool errors** — handled inside the hosted tool path.

**Anthropic pattern:** always return a `tool_result` for every `tool_use_id`. On failure set `"is_error": true` and put an **instructive** message in `content` (what failed + what to try next). Claude incorporates the error; for invalid/missing params it typically retries 2–3 times with corrections before apologizing. Do **not** crash the loop on tool exceptions — convert to error results ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

**OpenAI pattern:** no `is_error` flag on function outputs — put the error text in `function_call_output` / tool message content; the model reads it as the observation and may retry. Still must correlate `call_id` and answer every call ([Function calling](https://developers.openai.com/api/docs/guides/function-calling)).

**Application-level retries** (distinct from model self-repair):

- Transient HTTP: exponential backoff + jitter **inside** the tool executor (before returning to the model), with a max attempt count.
- Non-transient / auth / validation: return error to the model immediately; don’t burn retries.
- Dangerous side effects: **no automatic retry** without idempotency keys.
- Consecutive identical failures: circuit-break the loop even if `max_iterations` remains.

Security: tool results are untrusted; strip secrets/stack traces from messages returned to the model ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

### Alternatives & Tradeoffs
| Layer | Retry here? | Notes |
|-------|-------------|-------|
| HTTP client in tool | Yes for 429/5xx | Cap attempts; don’t leak credentials |
| Model self-repair via error result | Yes for bad args | Needs clear error text |
| Outer agent loop | Cap only | Avoid infinite “try again” |
| Human escalation | For irreversible actions | HITL (Week 13) |

Tradeoff: silent executor retries hide outages from the model (good for flaky networks) but can inflate latency; always-forwarding errors to the model increases tokens and may cause thrashing.

### Necessity
Crash-on-exception aborts the conversation mid-`tool_use` and leaves the API state illegal (missing results). Generic `"failed"` errors cause useless retries. Unbounded executor retries + unbounded model retries multiply cost and duplicate side effects.

### Industry Practice
- **Common:** `try/except: raise` in tools; agent dies; user refreshes.
- **Senior:** map exceptions → structured error results; classify retryable vs not; idempotency keys on writes; timeout per tool; log `tool_name`, latency, error class; use SDK hooks (Anthropic `generate_tool_call_response` / equivalent) to inspect errors before send ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)).

### Concrete Scenario
Anthropic docs show returning `is_error: true` with `ConnectionError: the weather service API is not available (HTTP 500)` so Claude can apologize or adapt — and separately show `Error: Missing required 'location' parameter` triggering correction retries: https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
Cookbook manual loop: unknown tool names and `TypeError` on args become `is_error` results so the model recovers instead of crashing: https://platform.claude.com/cookbook/multimodal-crop-tool

### Open Questions
- Should frameworks standardize a cross-provider `ToolError` shape (code, retry_after, user_safe_message)?
- How many model-visible retries are optimal before escalating to a human?

### Sources
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner
- https://platform.claude.com/cookbook/multimodal-crop-tool
- https://developers.openai.com/api/docs/guides/function-calling

---

## Concept: Stopping conditions and loop-limit guardrails

### Fundamentals
**Stopping conditions** are the rules that end the agent loop. Categories:

1. **Model-natural stop** — OpenAI final message with no further `function_call`; Anthropic `stop_reason` other than `tool_use` (e.g. `end_turn`, `max_tokens`, `refusal`, `stop_sequence`).
2. **Explicit iteration cap** — Anthropic tool runner `max_iterations`; cookbook defaults like 20 ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner), [Zoom cookbook](https://platform.claude.com/cookbook/multimodal-crop-tool)).
3. **Graph recursion limit** — LangGraph runtime recursion / step counters for cyclic graphs (Week 13).
4. **Resource budgets** — max tokens, max $ spend, wall-clock deadline, max tool invocations per tool (`max_uses` style limits appear on some server tools).
5. **Policy / product stop** — user cancel, safety classifier deny, approval rejected.
6. **Goal predicates** — structured “done” output schema; verifier agent says pass.

Guardrails should be **defense in depth**: model stop *and* hard caps. Token-capped mid-tool-call turns need special handling (resume / error result / ask model to answer without tools) ([Zoom cookbook](https://platform.claude.com/cookbook/multimodal-crop-tool)).

### Alternatives & Tradeoffs
| Guardrail | Strength | Weakness |
|-----------|----------|----------|
| `max_iterations` only | Simple | May stop mid-task with no user-facing explanation |
| Token/cost budget | Aligns with billing | Hard to estimate per task |
| Time deadline | UX-friendly | Flaky under load |
| Structured “DONE” token | Clear semantic end | Model may claim done early |
| Recursion limit (graphs) | Handles cycles | Need proactive handling near limit |

Tradeoff: tight caps protect spend but increase “I ran out of steps” failures; loose caps invite runaway agents.

### Necessity
Unlimited loops are a production outage waiting to happen (cost, rate limits, stuck workers). Caps without a **user-visible fallback** look like silent failure. Ignoring `max_tokens` / truncated tool JSON leads to corrupted state.

### Industry Practice
- **Common:** infinite loop until client timeout (504).
- **Senior:** configurable caps per agent profile; emit structured `AgentStopped` reason to UI/logs; near-limit prompts (“wrap up”); separate limits for read-only vs mutating tools; combine with HITL for high-impact actions.

### Concrete Scenario
Anthropic Tool Runner docs: the runner “loops until Claude returns a message without a tool use, or until it reaches `max_iterations` if you set it”; you can `break` early when iterating messages: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner  
OpenAI documents continuing the tool-calling flow only as long as the task requires — implying application ownership of when to stop requesting more tools: https://developers.openai.com/api/docs/guides/function-calling

### Open Questions
- Should stop reasons be standardized across providers for observability platforms?
- Is “budget left” something the model should see as a tool/observation to plan within limits?

### Sources
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner
- https://platform.claude.com/cookbook/multimodal-crop-tool
- https://developers.openai.com/api/docs/guides/function-calling
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls

---

## Week 11 cross-cutting sources

- Anthropic tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
- Anthropic handle tool calls: https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
- Anthropic tool runner: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner  
- OpenAI function calling: https://developers.openai.com/api/docs/guides/function-calling  
- OpenAI tool search: https://developers.openai.com/api/docs/guides/tools-tool-search  
- OpenAI Agents SDK tools: https://openai.github.io/openai-agents-python/tools/  
- AI Engineer Summit — Building Agents with MCP (Mahesh Murag, Anthropic): https://youtu.be/kQmXtrmQ5Zg  
- AI Engineer channel: https://www.youtube.com/@aidotengineer  
