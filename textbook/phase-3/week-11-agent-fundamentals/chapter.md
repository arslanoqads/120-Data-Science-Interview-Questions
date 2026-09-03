# Chapter 11 — Agent fundamentals

> **Phase 3 — Agentic Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-3/week-11-agent-fundamentals/`  
> **Syllabus Build:** Ship a **single-agent tool loop** (not MCP, not multi-agent): (1) define **three client tools** with strict JSON Schema — `docs_search`, `structured_query`, and calendar **read/write split** (`calendar_list_events` / `calendar_create_event`); (2) implement a **bounded loop** — OpenAI Responses `function_call` ↔ `function_call_output` **or** Anthropic Messages `tool_use` ↔ `tool_result` (one primary provider, the other as a mapping table); (3) enforce **pairing** (every `call_id` / `tool_use_id` gets a result immediately after), **iteration cap**, **per-tool timeout**, and a typed **stop reason** (`end_turn` | `max_iterations` | `max_tokens` | `tool_budget` | `policy_deny` | `user_cancel`); (4) convert tool exceptions into **error observations** (never crash mid-`tool_use`); classify retryable (429/5xx inside the executor, capped) vs model-visible (`is_error` / error string); (5) log a **turn trace**: model stop reason, tool name(s), latency, error class, remaining budget. Interview artifact = trace of a multi-step task with a **named stop reason**.

---

## Chapter framing

Week 11 is the **loop contract** week of Phase 3. Weeks 4–5 taught how to call models with tools as a *single round trip*. This week makes that round trip **repeat until done**, under budgets, with typed observations and typed stops. MCP (Week 12) is how tools are *discovered and transported*. Graphs, multi-agent, and HITL (Week 13) are how loops *branch and persist*. Side-effect safety (Week 14) assumes you already know when a tool ran and whether it will run again. Evaluation (Week 15) scores **trajectories** — which do not exist if the loop is a hidden `while True`.

**What an agent is this week (vendor, not slogan):** a multi-turn conversation in which the model may request tools, *your application* executes them, results are fed back, and the model continues until it produces a final answer **or a guardrail stops it**.

OpenAI names a **five-step flow** and says the application can continue for as many tool calls as the task requires: request with tools → receive tool call(s) → execute application-side code → send tool output (`function_call_output`, correlated by `call_id`) → receive a final response **or more tool calls**. Anthropic’s equivalent: Claude returns `stop_reason: "tool_use"` with `tool_use` blocks; the app replies with a **user** message of `tool_result` blocks (`tool_use_id`, `content`, optional `is_error`); repeat until Claude stops calling tools. The SDK **tool runner** automates that cycle and stops when Claude returns without tool use, or when `max_iterations` is hit. LangGraph makes the same cycle a **graph**: `START → llm_call → (conditional: tools?) → tool_node → llm_call → … → END`.

The slogan **plan → act → observe → repeat** is Yao et al., *ReAct* (arXiv:2210.03629). In current APIs, “plan” is the model’s reasoning + tool choice, “act” is *your* executor, “observe” is injecting `tool_result` / `function_call_output` / `ToolMessage`. Do not implement ReAct as unbounded free-text thought–action traces; use native tool calling.

Harrison Chase (AI Engineer World’s Fair): enterprise adoption is **value if right × P(success) − cost if wrong**. LangGraph exists to put **required behavior in control flow** (not only in the prompt). Week 11’s contribution is **P(success) of a single ReAct cycle** and **cost if the loop never stops**.

**This week’s artifact is a bounded loop + three tools + a stop taxonomy**, not a framework logo. Do **not** skip this week for “we’ll wrap LangChain AgentExecutor and ship.” You cannot debug MCP (Week 12), graphs/HITL (Week 13), or side effects (Week 14) if the **loop contract** is implicit.

### Starter tool palette (calendar, doc search, structured query)

Use **three mutually exclusive capabilities** so Week 11 practices *selection* without a 40-tool CRM dump:

| Tool | Side effects | When to use | When **not** to use |
|------|----------------|-------------|---------------------|
| **`docs_search`** | Read-only | Policies, runbooks, product docs, “what does the handbook say” | Exact row/metric from a warehouse; “put it on my calendar” |
| **`structured_query`** | Read-only (default) | Filters, counts, joins against a typed store (tickets, orders, employees) with a constrained query object | Keyword search over PDFs; creating meetings |
| **`calendar_list_events`** | Read-only | “Am I free Tuesday?”, “what’s on the team calendar” | Searching the knowledge base |
| **`calendar_create_event`** | **Write** | User explicitly asked to schedule; you have title, start, end, timezone | Model “helpfully” booking after a search; never auto-retry without `idempotency_key` |

**Canonical multi-step task for traces:** “Find the PTO policy snippet, check how many PTO tickets Alice has open, and propose (do not silently create) a 30-minute calendar block to review them.” Expected trajectory: `docs_search` → `structured_query` → `calendar_list_events` → **final text proposal** (create is HITL / Week 13 unless the user said “book it”).

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) growing an **internal ops** tool loop — docs corpus from Weeks 6–10, a constrained ticket/order store, and calendar read/write — not a weather toy and not MCP yet.

**Default path (synthesis):**

1. Prefer **SDK tool runner / Agents SDK** when you do not need custom transport; drop to a **manual loop** when you own HITL, streaming UX, or mixed server+client tools.  
2. Prefer **LangGraph** (explicit `llm_call` → `tool_node` → `llm_call` + `recursion_limit`) when you already know you need checkpoints, branches, or HITL next week — but still treat Week 11 as *one ReAct cycle*, not a multi-agent graph.  
3. Keep the tool palette **small and mutually exclusive** (calendar vs docs vs SQL). Add tool search only after ~20–30 tools.  
4. Reads may auto-retry; **writes require idempotency keys** or HITL (Week 13/14).  
5. Interview artifact = **trace of a multi-step task** with a **named stop reason**, not “the agent just worked.”

---

### Agent loop vs naive `while True`

* **Fundamentals:**  
  An **agent loop** is application-owned control flow around a **tool-calling model**. The model never executes tools. It emits a structured request; your process runs code; you append an observation; you call the model again. That is the entire mechanism. Frameworks are opinions about **when to stop**, **how to persist messages**, and **what to do on errors**.

  **OpenAI — five steps, application continues** ([Function calling](https://developers.openai.com/api/docs/guides/function-calling)):

  1. Make a request with tools the model could call.  
  2. Receive a tool call (`function_call` items on Responses; `tool_calls` on Chat Completions).  
  3. Execute application-side code.  
  4. Second request with tool output (`function_call_output` / role `tool`), keyed by **`call_id`**.  
  5. Final response **or more tool calls**.

  The docs do **not** ship a `while True` for you. If you want packaged orchestration, they point at the **Agents SDK**. Parallel calls: multiple `function_call` items in one turn; you must return one output per `call_id`. `parallel_tool_calls: false` forces zero or one call.

  **Anthropic — `stop_reason: tool_use` until it isn’t** ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)):

  - Assistant message may mix `text` + one or more `tool_use` (`id`, `name`, `input`).  
  - `stop_reason` is `"tool_use"` when you must run client tools.  
  - Your next **user** message: `tool_result` blocks **first**, matching every `tool_use_id`, **immediately after** the assistant tool-use message (no interstitial messages).  
  - Repeat until `stop_reason` is something else (`end_turn`, `max_tokens`, `refusal`, …).

  **Tool runner** ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)): `client.beta.messages.toolRunner(...)` loops until Claude returns without tool use **or** `max_iterations`. You can `break` early. If you `append_messages()` yourself, *you* become responsible for pairing.

  **LangGraph — the loop is edges, not a hidden while** ([Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph), [quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)):

  - Node `llm_call`: bind tools, invoke model, append AI message.  
  - Node `tool_node` / `ToolNode`: execute, append `ToolMessage`s.  
  - Conditional edge `should_continue`: if last message has `tool_calls` → tools, else `END`.  
  - Edge tools → `llm_call`.

  The **Functional API** example is literally `while True: if not tool_calls: break` — which is correct **only** with an outer recursion limit / step budget.

  **ReAct paper vs API loop:** Yao et al. (arXiv:2210.03629) interleave *Thought / Action / Observation* in generated text. Native tool calling **replaces** brittle action-string parsing with JSON Schema. Keep the *interleaving* idea; do not keep 2022 prompt formats as production.

  A loop that only checks “did the model ask for a tool?” fails because: no iteration / token / $ / wall-clock budget; no typed stop reasons (truncated tool JSON is not “done”); side-effect tools are not idempotent; missing pairing (Anthropic 400; OpenAI orphan `call_id`s); partial / parallel / server-tool mixes; forced `tool_choice` that never resets (Agents SDK documents an **infinite loop** if you keep `tool_choice` pinned after the result — the SDK resets to `auto` by default); exceptions that escape and leave the conversation illegal.

* **The Alternatives:**  

  | Approach | What you gain | What it costs | When it fits |
  |----------|---------------|---------------|--------------|
  | Manual OpenAI/Anthropic loop | HITL, custom transport, mixed hosted+client tools | Easy to get pairing/order wrong; you own retries and caps | Custom streaming UX; Week 13 HITL path |
  | Anthropic tool runner | Caps, formatting, iteration; intercept results | Beta; taking over a turn means you own history | Default when Anthropic is primary and transport is stock |
  | OpenAI Agents SDK | `tool_use_behavior`, `reset_tool_choice`, hosted+function mix | Responses-centric features (tool search) do not port to Chat Completions | Default when OpenAI is primary and orchestration is stock |
  | LangGraph StateGraph | Visible cycle; `recursion_limit`; checkpoints; Week 13 path | Two-node ReAct is still a loop — graphs do not magically add stop semantics | You already know you need branches / HITL next |
  | LangGraph Functional `while True` | Readable application-shaped code | Identical to naive while unless you add caps and error-as-message | Prototypes — wrap with a counter or graph runtime limit |
  | Always one tool then stop | Predictable cost | Cannot compose docs + SQL + calendar | Single-lookup demos only |

  Tradeoff: demos love unbounded ReAct. Production needs **hard caps** (iterations, tokens, dollars, time) plus **semantic stop** (goal achieved / user stop / policy deny). Chase: required sequences belong in **control flow**; the loop *is* that control flow.

* **Failure Modes:**  
  - Cost incidents — workers spinning on “one more search.”  
  - Hard API errors — unpaired Anthropic `tool_use`; OpenAI missing `function_call_output`.  
  - Silent mid-task stop — `max_tokens` on a tool call interpreted as final answer.  
  - Duplicate side effects — retry of `calendar_create_event`.  
  - Un-debuggable traces — no turn index, no stop reason → Week 15 eval impossible.  
  - `tool_choice: required` / named force never reset → infinite paid loop.  
  - Exception escapes mid-`tool_use` → conversation left in illegal state.

* **Average vs. Strong Engineer:**  
  **Average:** `while True` until no `tool_calls`; no metrics; `except: raise`; copy `get_weather`; one calendar tool that both lists and creates.  
  **Strong:** prefer tool runner / Agents SDK unless custom control is needed; if manual, `for i in range(max_iterations)` — not `while True`; switch on **provider stop reason** every turn; execute parallel client tools concurrently **only if** all are read-only or have idempotency keys; log `{turn, stop_reason, tool_names, tokens, latency_ms, error_class}`; LangGraph: set `recursion_limit` **explicitly** (Graph API default **1000** as of 1.0.6 — do not inherit a demo 25 vs 1000 surprise).  
  **FDE bar:** draw OpenAI’s five boxes and Anthropic’s pairing constraint on a whiteboard; then draw LangGraph’s two nodes + `END`.

* **Worked Example:**  
  **Naive loop (fails):** Deployment Copilot ops path — user asks to “find the incident runbook and page the on-call.” Model calls `docs_search`, then `calendar_create_event` (wrong tool — meant pager), HTTP 500, `except` bubbles, process dies. Client retries the whole request; search is fine, **create runs twice** if you “fixed” the exception by retrying the whole loop.

  **Correct loop (documented patterns):**

  1. OpenAI five-step continue-until-done with one output per `call_id`.  
  2. Anthropic tool runner `max_iterations=20` **or** manual dispatch + `is_error` (zoom cookbook pattern).  
  3. LangGraph: `should_continue` + `ToolNode`; errors as `Tool error: …` back to agent.  

  **Week 11 lab assertion:** after N turns, either a final assistant text **or** a structured `AgentStopped(reason=..., turn=N)` — never a hung worker.

* **Apply It:**  
  1. Choose one primary provider loop (OpenAI Responses or Anthropic Messages); keep a mapping table for the other.  
  2. Implement `run_agent()` as `for i in range(max_iterations)` (or tool runner / Agents SDK) — ban bare `while True` without caps.  
  3. Enforce pairing: every `call_id` / `tool_use_id` gets a result **immediately after** the tool-use turn.  
  4. Branch on provider stop reason every turn (`end_turn` / `tool_use` / `max_tokens` / `refusal` / …).  
  5. Log `{turn, stop_reason, tool_names, tokens, latency_ms, error_class}` on every iteration.  
  6. Assert the lab invariant: final text **or** typed `AgentStopped` — never a hung worker.

---

### Tool / function calling schemas (OpenAI + Anthropic)

* **Fundamentals:**  
  A **tool schema** is a machine-readable contract: (1) **what** tools exist (`name`), (2) **when** to use them (natural-language `description`), (3) **what JSON is allowed** (`parameters` / `input_schema`, JSON Schema). The model does not “call a function” in-process. It emits a structured object your executor must validate, authorize, and run.

  **OpenAI (Responses + Chat Completions)** — function tools:

  | Field | Role |
  |-------|------|
  | `type: "function"` | Distinguishes from hosted tools (`web_search`, MCP, etc.) |
  | `name` | Dispatch key; stable, versioned (`docs_search` not `search2`) |
  | `description` | Selection signal |
  | `parameters` | JSON Schema object |
  | `strict` | Recommended `true`: arguments must match schema via Structured Outputs |

  Call / result pairing: model emits `function_call` with `call_id`, `name`, `arguments` (**JSON string** — parse it). You return `function_call_output` with the **same** `call_id` and a **string** output. Chat Completions uses `role: "tool"` + `tool_call_id` — same pairing idea, different envelope.

  **Strict mode constraints:** enabling `strict: true` uses Structured Outputs and **rejects** incompatible schemas (typically `additionalProperties: false`, all properties in `required`, limited union/optional patterns). OpenAI recommends always enabling strict mode despite limitations.

  **Anthropic (Messages API)** — client tools:

  | Field | Role |
  |-------|------|
  | `name` | Dispatch key |
  | `description` | Selection signal |
  | `input_schema` | JSON Schema (not named `parameters`) |
  | `strict: true` | Inputs guaranteed to match schema |

  Call / result pairing: `tool_use` block (`id` like `toolu_…`, `name`, `input` as **object**, not string). Reply `tool_result` with `tool_use_id`, `content`, optional `is_error`. Unlike OpenAI: no `role: tool`. History is still `user`/`assistant` with mixed content blocks. Formatting bugs look like application bugs (400), not model quality.

  **Schema design levers (both):** required vs optional (strict modes often force every listed property required — model “optional” via enums like `"unspecified"` or split tools); enums (`entity: ticket|order|employee`); `additionalProperties: false`; parameter descriptions (formats, units); **read vs write split**; versioned names (`docs_search_v2`); token cost (every schema is prompt tokens every turn unless deferred).

  Map Week 4 structured outputs onto tools: **tool args are structured outputs**. Pydantic on the executor is defense in depth even with `strict`.

  **Untrusted results:** Anthropic — treat tool results as **untrusted** (indirect prompt injection). Keep them in `tool_result` blocks, **not** concatenated into `system` or naked user text. Same rule for OpenAI `function_call_output` strings: delimit, don’t merge into developer instructions.

  Provider mapping cheat sheet:

  | Concern | OpenAI | Anthropic |
  |---------|--------|-----------|
  | Schema field | `parameters` | `input_schema` |
  | Args on the wire | JSON **string** | JSON **object** |
  | Call id | `call_id` | `tool_use.id` |
  | Result envelope | `function_call_output` / `role: tool` | `tool_result` in **user** message |
  | Error flag | Put text in output (no standard `is_error`) | `is_error: true` |
  | Force tools | `tool_choice` / Agents `ModelSettings` | `tool_choice` |
  | Parallel off | `parallel_tool_calls: false` | `disable_parallel_tool_use: true` |

* **The Alternatives:**  

  | Choice | What you gain | What it costs | When it fits |
  |--------|---------------|---------------|--------------|
  | Loose schema + post-validation | Flexible; easy to start | Model invents args; repair loops (Anthropic: 2–3 retries then apology) | Exploration only |
  | `strict: true` | Fewer invalid calls | Schema subset; optional fields awkward; request rejected if schema illegal | Default for Week 11 triad |
  | Custom/free-form OpenAI tools | Good for messy text I/O | Weak executor contracts | Rare; not the syllabus default |
  | Hosted / built-in tools | Less code | Data residency, less control, mixed-loop complexity | When provider owns act/observe |
  | MCP-wrapped tools (Week 12) | Discovery/transport standard | Same JSON-Schema-ish surface; **not** a substitute for schema hygiene | After the loop contract exists |
  | One fat tool with an `action` enum | Fewer names | Giant schema; worse selection; harder authz | Avoid |

  Tradeoff: richer schemas improve disambiguation **and** burn tokens; near-duplicate parameter names across tools confuse selection.

* **Failure Modes:**  
  - Hallucinated parameters, omitted required fields, never-called tools.  
  - Anthropic: invalid/missing params → retries 2–3 times then apology; **strict** eliminates that class when the schema is compatible.  
  - Unpaired/misordered results → **hard API errors**.  
  - `structured_query` without enums → model-authored SQL → data incident.  
  - Calendar create without `idempotency_key` in schema → unsafe retry.  
  - Stuffing search snippets into the system prompt → malicious doc jailbreaks the agent.  
  - `strict: true` + incompatible schema → HTTP error with constraint details (not an LLM mystery).

* **Average vs. Strong Engineer:**  
  **Average:** copy `get_weather`; description “gets data”; no `strict`; args printed as Python dicts into the next user message (breaks Anthropic pairing).  
  **Strong:** description encodes **when to use / when not to use**; parameter docs include formats; enums for closed sets; `strict` / Structured Outputs where supported; **Pydantic validate** anyway; schemas live **next to executors** (one module per tool); version tool names; treat results as untrusted; OpenAI: parse `arguments` with `json.loads` in try/except → error output, don’t crash.  
  **FDE bar:** whiteboard both envelopes; explain why Anthropic `tool_result` must be first and immediately after `tool_use`; mention `strict` schema subset failures as a **release blocker**.

* **Worked Example:**  
  Week 11 triad for Deployment Copilot (implement these, not weather):

  **`docs_search` (OpenAI-shaped):**

  ```json
  {
    "type": "function",
    "name": "docs_search",
    "description": "Keyword/semantic search over the internal document corpus (policies, runbooks, product docs). Use when the user needs quoted or cited handbook text. Do not use for warehouse metrics, ticket IDs, or calendar availability.",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "query": { "type": "string", "description": "User intent in search terms, not a full chat transcript." },
        "k": { "type": "integer", "description": "Max chunks to return (1–8). Always pass k." }
      },
      "required": ["query", "k"],
      "additionalProperties": false
    }
  }
  ```

  Result JSON stays inside the tool payload: `{hits: [{doc_id, score, snippet, url}]}`.

  **`structured_query` (Anthropic-shaped):** constrained object the executor compiles (allowlisted tables, parameterized filters) — *not* free-form SQL from the model:

  ```json
  {
    "name": "structured_query",
    "description": "Read-only query against the operational store (tickets, orders, employees). Use for counts, filters, and lookups by id/status/date. Do not use for prose documents or calendar. Never invent table names; only use tables listed in the enum.",
    "strict": true,
    "input_schema": {
      "type": "object",
      "properties": {
        "entity": { "type": "string", "enum": ["ticket", "order", "employee"] },
        "filters": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "status": { "type": "string" },
            "updated_after": { "type": "string", "description": "ISO-8601 date" }
          },
          "additionalProperties": false
        },
        "limit": { "type": "integer" }
      },
      "required": ["entity", "filters", "limit"],
      "additionalProperties": false
    }
  }
  ```

  **`calendar_create_event`:** required `idempotency_key`, `timezone`, ISO datetimes; reject if `end <= start` **in the executor** with an instructive error. Description must say: *only after the user confirmed time and attendees; do not use to search docs or tickets*.

  **Failure to show in a trace:** Responses request with `strict: true` and a schema that allows free additional properties → **HTTP error with constraint details**. Fix the schema; don’t disable strict “to unblock demo.” Mahesh Murag (AI Engineer Summit): tools as a **product surface** (names, descriptions, schemas) even when transport becomes MCP next week.

* **Apply It:**  
  1. Define the triad next to executors: `docs_search`, `structured_query`, `calendar_list_events` / `calendar_create_event`.  
  2. Enable `strict: true` (OpenAI `parameters` / Anthropic `input_schema`); require `additionalProperties: false` and closed enums.  
  3. Put **when to use / when not to use** in every `description`; split read vs write calendar tools.  
  4. Require `idempotency_key` on `calendar_create_event`; validate `end > start` in the executor.  
  5. Pydantic-validate args after provider parse; on OpenAI, `json.loads` in try/except → error observation.  
  6. Keep tool results in `tool_result` / `function_call_output` — never merge snippets into `system`.

---

### Tool selection and disambiguation

* **Fundamentals:**  
  **Tool selection** is the model’s choice of **which named capability** to invoke given the user goal and the tool list in context. This is **attention over a menu**. Every extra tool is a competing description.

  Failure shapes:

  - **Wrong twin** — `docs_search` vs `structured_query` vs `calendar_list_events` when names/descriptions overlap (“search”, “get”, “lookup”).  
  - **None when one is needed** — model answers from parametric memory about a policy that lives in the corpus.  
  - **Shotgun parallel** — calls search *and* SQL *and* calendar for “what’s the PTO rule?”  
  - **Write instead of read** — `calendar_create_event` when the user asked “am I free?”  
  - **Deferred-search miss** — tool search loads the wrong subset; the right tool was never in context.

  **Vendor techniques:**

  1. **Better descriptions (first lever)** — Anthropic: when Claude picks wrong tools, improve **`description` specificity**; encode **when not to use**.  
  2. **Fewer tools in context** — large catalogs dilute attention and burn tokens; merge duplicates; split agents (Week 13) so each sees a **small palette**. Chase: reliability via **narrower, more workflow-like** autonomy — not 80 peer tools on one brain.  
  3. **`tool_choice` constraints** — OpenAI / Agents SDK: `auto` | `required` | `none` | named tool. Named force is for forms / known workflows. Agents SDK: **reset `tool_choice` to `auto` after a call** or you loop forever. Anthropic: `tool_choice` type auto/any/tool; `disable_parallel_tool_use: true` reduces shotgun calling.  
  4. **Disable parallel when order matters** — docs → SQL → calendar is **sequential**; parallel is for independent reads only.  
  5. **Tool search / deferred loading (“RAG for tools”)** — OpenAI `tool_search` (gpt-5.4+): mark functions/MCP `defer_loading: true`; model searches and loads only needed tools. Agents SDK: exactly one `ToolSearchTool()`; namespaces via `tool_namespace(...)`. Anthropic exposes server-side `tool_search` analogously. Wrong search query still loads an irrelevant subset.  
  6. **Namespaces / grouping** — load a **group** instead of 15 near-duplicates; prefer namespaces or MCP servers over dozens of individually deferred functions.  
  7. **Router / multi-agent** — boundary of this week (Week 13). Week 11 should **feel** the pain of a 3-tool palette done well first.  
  8. **Embeddings over tool docs (custom)** — enterprise catalogs sometimes retrieve tool definitions with the same hybrid stack as docs; you own eval of retrieval@k for **tools**. [NEEDS MORE RESEARCH]: first-party vendor recipes for embedding-based tool routers beyond custom infra are not specified in this corpus.

  **Disambiguation recipe for the syllabus triad:**

  | User language | Tool | Why the others lose |
  |---------------|------|---------------------|
  | “What does the handbook say about X?” | `docs_search` | Not a row in a DB; not a meeting |
  | “How many open tickets does Alice have?” | `structured_query` | Not in PDFs; not calendar |
  | “Am I free Thursday 3pm?” | `calendar_list_events` | Don’t SQL the calendar replica; don’t search Confluence |
  | “Book 30 minutes with Alice” | `calendar_create_event` | Only after list/confirm; not search |

  Put those **negative** sentences in the `description` fields. Names should be **verb_noun** and non-overlapping (`search` appearing in two names is a smell — `docs_search` vs `structured_query` is intentional).

* **The Alternatives:**  

  | Strategy | When it helps | Cost |
  |----------|---------------|------|
  | Rewrite descriptions + when-not-to | Near-duplicate names; Week 11 triad | Human curation; eval set |
  | Fewer tools / merge | Any catalog | Product negotiation |
  | `disable_parallel` / `parallel_tool_calls: false` | Sequential tasks; shotgun | Extra latency on independent reads |
  | `tool_choice: required` / named | Forms, “always look it up” | Breaks refusal, small talk, already-in-context answers |
  | Deferred tool search | **~20–100+** tools | Extra latency; model/version (gpt-5.4+); search quality |
  | Namespaces | Related families (crm, billing) | Named `tool_choice` limitations |
  | Multi-agent split | Distinct domains | Orchestration (Week 13) |
  | Embedding router over tool docs | Dynamic enterprise catalogs | Custom infra; another RAG problem |

  Tradeoff: one mega-agent is simpler to ship; **selection quality collapses as tools grow**. Industry response is **retrieval over tools**, not infinite prompt stuffing — but retrieval can load the **wrong** 10 tools.

  Do **not** start Week 11 with `defer_loading` on three tools. You cannot tell description bugs from search bugs.

* **Failure Modes:**  
  - Wrong side effects — refund vs cancel; create vs list.  
  - Wasted API calls and user-visible thrashing.  
  - Authz holes — model picks a high-privilege twin because the description was shorter.  
  - Eval noise — Week 15 “trajectory fail” that is really a menu design fail.  
  - With deferred loading: **silent unavailability** of the correct tool.  
  - “Fix it in the system prompt” (`always use docs_search for policies`) **rots** the moment a fourth tool is added.

* **Average vs. Strong Engineer:**  
  **Average:** dump all CRM/Jira/Slack/MCP tools into one agent; debug with “please use X”; enable parallel because it looks faster.  
  **Strong:** inventory tools; merge duplicates; **mutual exclusion in descriptions**; golden prompts for **tool-choice accuracy** (Phase 3 Week 15): N user utterances → expected tool (or none); adopt tool_search past **~20–30** tools; route by intent to specialized agents when domains diverge; log `chosen_tool` vs `expected_tool`; keep a **hot set** (always loaded: search + query + list) and defer rare writes/admin tools.  
  **FDE bar:** explain why `docs_search` vs `structured_query` is the **same** problem as `search_tickets` vs `search_kb` at 10× catalog size; cite tool_search docs and namespace rules; mention Murag’s MCP talk as **distribution**, not selection magic.

* **Worked Example:**  
  Week 11 lab on Deployment Copilot (small palette, **no** tool search yet) — 20 paraphrases:

  - 5 should call **only** `docs_search`  
  - 5 **only** `structured_query`  
  - 5 **only** `calendar_list_events`  
  - 3 chitchat → **no tool**  
  - 2 sequential (docs then SQL) → **not** parallel both on turn 1  

  Score **tool-choice accuracy**. Then **deliberately** rename `structured_query` to `search_records` and watch accuracy drop — that is the disambiguation lesson.

  OpenAI Tool search / Agents SDK `tool_namespace` + `ToolSearchTool()` are the scale-up path after ~20–30 tools — not this week’s starting move.

* **Apply It:**  
  1. Write mutual-exclusion `description` text for the triad using the when/when-not table above.  
  2. Build a 20-utterance golden set for tool-choice accuracy (docs / SQL / list / none / sequential).  
  3. Disable parallel (`parallel_tool_calls: false` or `disable_parallel_tool_use: true`) for sequential PTO→ticket→calendar tasks.  
  4. Never pin `tool_choice` to a named tool across turns without resetting to `auto`.  
  5. Log `chosen_tool` vs `expected_tool` on the golden set.  
  6. Defer tool search / `defer_loading` until the catalog is ~20–30+ tools — not on three starter tools.

---

### Tool error handling and retry

* **Fundamentals:**  
  Tool failures are not one bucket. If you retry the wrong class, you either **amplify outages** or **duplicate side effects**. Three layers:

  1. **Executor / HTTP** — your code talking to calendar, search, warehouse.  
  2. **Observation to the model** — what the next prompt sees.  
  3. **Outer agent loop** — whether to continue, stop, or escalate.

  **Failure classes:**

  | Class | Example | Retry in executor? | Tell the model? |
  |-------|---------|--------------------|-----------------|
  | Transient infra | 429, 5xx, timeout, connection reset | **Yes**, capped exponential backoff + jitter | Only if retries exhausted |
  | Invalid model args | missing field, bad enum, `end < start` | **No** (strict should prevent; still happens) | **Yes**, instructive error |
  | Unknown tool name | hallucinated `search_all` | **No** | **Yes**, list allowed names |
  | Business-rule reject | calendar busy, ticket not found, ACL deny | **No** | **Yes**, what to try next |
  | Auth / 401 / 403 | expired app token | **No** (fix creds; don’t spin) | User-safe message; **do not** leak tokens |
  | Provider/server-tool | Anthropic web_search `max_uses_exceeded` | N/A (hosted) | Claude handles many server errors internally |
  | Truncated / parse | `max_tokens` mid-JSON args | Don’t execute | Error observation or abort turn |

  **Anthropic pattern (canonical):** Always return a `tool_result` for **every** `tool_use_id`. On failure: `"is_error": true` and an **instructive** `content` (what failed + what to try next). Do **not** crash the loop — convert exceptions to error results. Write instructive errors (`Rate limit exceeded. Retry after 60 seconds.`) not `"failed"`. Unknown tool / `TypeError`: map to `is_error` so the model recovers (zoom cookbook). Tool runner: `generate_tool_call_response()` to inspect errors **before** send. Security: strip secrets and stack traces; keep results in `tool_result`.

  **OpenAI pattern:** No first-class `is_error` on `function_call_output`. Put the error **text** (still correlated by `call_id`) in the output string. Prefer a **stable JSON** error shape so *your* logs parse:

  ```json
  {"ok": false, "error_class": "transient_exhausted", "retryable": false, "user_message": "Calendar API unavailable. Try again later."}
  ```

  Do not return HTML dumps or Python tracebacks. You **must** still answer every `call_id`.

  **LangGraph pattern:** **LLM-recoverable** errors (tool failures, parsing) → store error in state, loop back to the LLM; **transient** → retries in the node; **user-fixable** → interrupt (Week 13 HITL); **unexpected** → bubble up. Copy the classification even if you are not on LangGraph yet.

  **Application-level retries (distinct from model self-repair):**

  - Transient HTTP: backoff + jitter **inside** the tool executor **before** returning to the model; **max attempt count** (e.g. 3).  
  - Non-transient / auth / validation: return error immediately.  
  - Dangerous side effects: **no automatic retry** without **idempotency keys** (`calendar_create_event.idempotency_key`). HTTP 500 after the provider *maybe* created the event is the classic double-book.  
  - Consecutive identical failures: circuit-break the **loop** even if `max_iterations` remains.  
  - Timeouts: per-tool deadline (research cites search 3s, SQL 10s, calendar 5s as an example profile).  
  - Parallel tools: one failure should still produce results for the others (partial success).

  **Multiplier effect:** unbounded executor retries × unbounded model retries × unbounded loop = cost and duplicate writes.

* **The Alternatives:**  

  | Layer | Retry here? | Notes |
  |-------|-------------|-------|
  | HTTP client in tool | Yes for 429/5xx | Cap; don’t leak credentials; honor `Retry-After` |
  | Model self-repair via error result | Yes for bad args / “try different filter” | Needs clear error text; counts against `max_iterations` |
  | Outer agent loop | Cap / circuit break only | Avoid infinite “try again” |
  | Human escalation | Irreversible actions, repeated ACL denials | HITL Week 13 |
  | Swallow error, return empty hits | Never for writes; dangerous for reads | Silent wrong answers |

  | Error visibility | Pros | Cons |
  |------------------|------|------|
  | Silent executor retries | Model doesn’t thrash on flaky 500s | Inflated latency; hides SLO burns |
  | Always-forward to model | Model can switch tools | Token cost; may retry the same write |
  | Structured `error_class` + short prose | Logs + model both work | Must keep enum small |

  Tradeoff: instructive errors improve self-repair; **too much** internal detail becomes a prompt-injection and data-leak channel. Chase: retries of an irreversible tool *are* the expensive failure (**cost if wrong**).

* **Failure Modes:**  
  - Crash-on-exception aborts mid-`tool_use` → **illegal conversation** (missing results) → 400s / stuck UIs.  
  - Generic `"failed"` → useless model retries.  
  - Retrying `calendar_create_event` on 500 without idempotency → **two meetings**.  
  - Returning stack traces → secret leakage + injection surface.  
  - Retrying 403 → audit noise and lockouts.  
  - Traces without `error_class` → cannot tell infra from selection failures in Week 15.

* **Average vs. Strong Engineer:**  
  **Average:** `try/except: raise` in tools; agent dies; user refreshes; retries the **whole** chat (duplicating writes).  
  **Strong:** map exceptions → structured error results; never leave a `tool_use` unanswered; classify retryable vs not **in one function** used by all tools; idempotency keys on writes; timeout per tool; log `tool_name`, latency, error class, attempt; circuit breaker: N identical failures → `AgentStopped(tool_circuit)`; SDK hooks to redact before send; LangGraph: errors as state, not as thrown node exceptions, for recoverable classes.  
  **FDE bar:** draw the three layers; say out loud “I retry 429 in the executor; I never retry creates without an idempotency key; I always pair `tool_result`.”

* **Worked Example:**  
  Week 11 lab (calendar write) on Deployment Copilot:

  1. User: book a slot. Model calls `calendar_create_event` with `idempotency_key=K`.  
  2. Executor POSTs; API returns **500**. Executor retries **once** with the **same** key (calendar API dedupes) **or** returns `is_error` / error output without retry if the API is not idempotent.  
  3. Model may try again — executor **must** reuse `K` (pass through args) or refuse.  
  4. Inject a **validation** error (`end` before `start`) — no HTTP retry; model-visible message: `Error: end must be after start (ISO-8601). Resend with a valid range.`  
  5. Inject unknown tool `create_meeting` — result: `Unknown tool. Allowed: docs_search, structured_query, calendar_list_events, calendar_create_event.`

  Anthropic: `is_error: true` + instructive content. OpenAI: same strings in `function_call_output`, still one output per `call_id`. LangGraph: `execute_tool` catch → `"Tool error: …"` → `goto="agent"`.

* **Apply It:**  
  1. Centralize `classify_tool_error(...)` → retryable vs model-visible vs stop.  
  2. Cap executor retries for 429/5xx (e.g. 3) with backoff + jitter; never retry 401/403/validation.  
  3. Always emit a paired result (`is_error` or structured error JSON) — never crash mid-tool-use.  
  4. Require idempotency on writes; refuse auto-retry of creates without a key.  
  5. Set per-tool timeouts; circuit-break on N identical tool+args+error.  
  6. Redact secrets/stack traces before the observation reaches the model; log `error_class` on the turn trace.

---

### Stopping conditions and loop-limit guardrails

* **Fundamentals:**  
  **Stopping conditions** are the rules that **end** the agent loop. The model’s “I’m done” is **one** of them, not the only one. Production systems use **defense in depth**: semantic stop **and** hard caps.

  **Taxonomy (use these names in logs):**

  | Kind | Signal | Who owns it |
  |------|--------|-------------|
  | **Model-natural stop** | OpenAI: assistant message with no further `function_call`. Anthropic: `stop_reason` **other than** `tool_use` (e.g. `end_turn`, `refusal`, `stop_sequence`). | Provider + your branch on the enum |
  | **Truncation** | `max_tokens` / `max_output_tokens` mid-text or **mid-tool-call JSON** | You must **not** treat as success |
  | **Iteration cap** | Anthropic tool runner `max_iterations`; cookbook defaults like **20**; Agents SDK run `max_turns` | Application |
  | **Graph recursion limit** | LangGraph `recursion_limit` → `GraphRecursionError`; counts **super-steps**, not “tool calls” | Runtime |
  | **Proactive step budget** | LangGraph `RemainingSteps`; `config["metadata"]["langgraph_step"]` | Graph logic routes to `END` **before** throw |
  | **Resource budgets** | Max tokens in, max $, wall-clock, max invocations **per tool** | Application + provider |
  | **Policy / product** | User cancel, safety classifier, approval rejected, authz deny | Product |
  | **Goal predicate** | Structured “done” schema; verifier says pass; `tool_use_behavior: stop_on_first_tool` / `StopAtTools` | Application |
  | **Circuit break** | Repeated identical tool+args+error | Application |
  | **Forced tool trap** | `tool_choice` stuck on required/named — stop is **never** natural until reset | Framework default vs your bug |

  **OpenAI:** continue the tool-calling flow **as long as the task requires** — implying **you** decide when to stop. Agents SDK: `tool_use_behavior` can **stop the run** on first tool or on named tools; `reset_tool_choice` exists so forced tool use does not diverge. There is no substitute for an application **turn counter** on a raw Responses loop.

  **Anthropic:** Tool runner loops until Claude returns **without** tool use, **or** `max_iterations`; you may `break` while iterating. All seven SDKs support `max_iterations`. Zoom cookbook uses `max_iterations=20` as a runaway guard. Handle `max_tokens` as a **first-class stop**, especially if a `tool_use` block is incomplete.

  **LangGraph:** `recursion_limit` = max **super-steps** per execution; exceeded → `GraphRecursionError`. **Starting 1.0.6, default is 1000.** Pass `recursion_limit` on `invoke`/`stream` as a **top-level config key**, **not** inside `configurable`. **`RemainingSteps`**: managed value for **proactive** routing to a wrap-up / `END` node before the throw. Do **not** copy “default 25” from old blog posts. **Do** set the limit **explicitly** per agent profile (research examples: support bot 15, research agent 80). Functional API `while True` **without** a cap is the naive loop wearing official clothes.

  **What to emit to the UI** — never silently 504:

  ```text
  AgentStopped
    reason: max_iterations | recursion_limit | max_tokens | budget_usd | deadline | policy_deny | user_cancel | end_turn | refusal | circuit_break
    turn: 12
    last_tools: [docs_search]
    user_message: "I hit my step limit while searching docs. Partial findings: …"
  ```

  Near-limit prompts (“wrap up in the next answer, no more tools”) are a **soft** guard; hard caps still fire. Read-only vs mutating: **separate** remaining quotas (research example: 100 searches vs 3 creates).

* **The Alternatives:**  

  | Guardrail | Strength | Weakness |
  |-----------|----------|----------|
  | `max_iterations` / `max_turns` only | Simple; matches tool runner | Stops mid-task; need a user-facing fallback |
  | Token / $ budget | Aligns with billing | Hard to estimate per task; streaming complicates |
  | Wall-clock deadline | UX-friendly | Flaky under load; doesn’t stop a stuck tool without timeouts |
  | Structured DONE / stop tool | Clear semantic end | Model claims done early (`StopAtTools` can be abused) |
  | Recursion limit (graphs) | Handles cycles | Super-step ≠ LLM call; parallel branches change the math |
  | `RemainingSteps` wrap-up node | Graceful degradation | You must implement the wrap-up prompt |
  | Catch `GraphRecursionError` only | Easy | **Reactive** — user sees a crash unless you translate it |
  | Tight caps | Protect spend | More “I ran out of steps” |
  | Loose caps | Completes long tasks | Runaway agents |

  Chase: a stop that dumps a stack trace is high **cost if wrong**. A stop that returns **partial artifacts + reason** is low cost.

* **Failure Modes:**  
  - Unlimited loops = **cost, rate limits, stuck workers**.  
  - Caps without **user-visible fallback** = silent failure / infinite spinner.  
  - Ignoring `max_tokens` truncated tool JSON = corrupted state / illegal next request.  
  - Raising LangGraph `recursion_limit` to “fix” a cycle = **paying for a bug**.  
  - `tool_choice=required` without reset = **infinite paid loop**.  
  - Week 13 HITL: interrupt is another stop; if Week 11 has no taxonomy, HITL looks like a hang.  
  - Interview answer “the model stops” with no taxonomy = reject.

* **Average vs. Strong Engineer:**  
  **Average:** infinite loop until client timeout (504); or LangGraph default whatever-the-version-is; no `AgentStopped`.  
  **Strong:** configurable caps **per agent profile**; typed stop reason to UI **and** traces; near-limit wrap-up turn; separate limits for read-only vs mutating tools; proactive `RemainingSteps` on graphs; don’t rely on except-only; combine with HITL for high-impact actions (Week 13); dashboards: `stop_reason` distribution (if 40% are `max_iterations`, the agent is under-tooled or under-capped).  
  **FDE bar:** quote tool runner `max_iterations`, OpenAI “as many as the task requires” as **your** responsibility, LangGraph 1.0.6 default **1000** + explicit config, `RemainingSteps` vs `GraphRecursionError`.

* **Worked Example:**  
  Week 11 lab on Deployment Copilot:

  1. Task that needs ~4 tool turns (docs → SQL → list calendar → final). Cap `max_iterations=3` → expect `AgentStopped(max_iterations)` **with** a partial summary, not an exception.  
  2. Same task, cap 12 → `end_turn`.  
  3. LangGraph: two-node cycle **without** `should_continue` to `END` → `GraphRecursionError`; then add `RemainingSteps < 3 → wrap_up`.  
  4. Truncation drill: set tiny `max_tokens` on a tool-call turn; assert you **do not** execute half-parsed args.

  Expected pass trajectory for the syllabus user story: `docs_search(query="PTO carryover", k=5)` → `structured_query(entity="ticket", …)` → `calendar_list_events(...)` → if user said “book it” **and** slot is free: `calendar_create_event(..., idempotency_key=…)` **once** → `stop_reason=end_turn`.

* **Apply It:**  
  1. Define a typed `AgentStopped.reason` enum matching the taxonomy above; emit it to UI and traces.  
  2. Set `max_iterations` (or Agents `max_turns`) explicitly — cookbook default **20** is a starting point, not magic.  
  3. On LangGraph, pass `recursion_limit` as a top-level config key; add `RemainingSteps` wrap-up before the throw.  
  4. Treat `max_tokens` truncation as a first-class stop; never execute half-parsed tool args.  
  5. Separate read vs write remaining quotas; near-limit soft “wrap up” prompt plus hard caps.  
  6. Dashboard `stop_reason` distribution; investigate if `max_iterations` dominates.

---

## Week 11 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Schemas:** three client tools with `strict` JSON Schema — `docs_search`, `structured_query`, `calendar_list_events` / `calendar_create_event` (create requires `idempotency_key`).  
2. **Loop:** primary provider bounded loop with pairing; mapping table for the other provider.  
3. **Selection:** mutual-exclusion descriptions; 20-utterance tool-choice golden set; parallel off for sequential tasks.  
4. **Errors:** classify retryable vs model-visible; never crash mid-`tool_use`; no write retry without idempotency.  
5. **Stops:** iteration cap + typed `AgentStopped`; handle `max_tokens`; LangGraph `recursion_limit` set explicitly if using graphs.  
6. **Trace:** log turn, stop reason, tool names, latency, error class, remaining budget.  
7. **Interview artifact:** multi-step PTO/docs → tickets → calendar proposal trajectory with a **named stop reason**.

When those steps are true, Week 11 is done in the syllabus sense: Deployment Copilot has a **loop contract**, not a framework logo — and Week 12 MCP is the same schema surface over a different transport, not magic tools.
