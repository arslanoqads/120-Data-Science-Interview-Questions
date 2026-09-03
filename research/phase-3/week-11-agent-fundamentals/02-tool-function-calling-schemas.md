# 02 — Tool / function calling schemas (OpenAI + Anthropic)

> Week 11 — Agent fundamentals  
> Research notes (raw).

---

## Fundamentals

A **tool schema** is a machine-readable contract: (1) **what** tools exist (`name`), (2) **when** to use them (natural-language `description`), (3) **what JSON is allowed** (`parameters` / `input_schema`, JSON Schema). The model does not “call a function” in-process. It emits a structured object your executor must validate, authorize, and run.

### OpenAI (Responses API + Chat Completions)

**Function tools** ([Function calling](https://developers.openai.com/api/docs/guides/function-calling), [Migrate to Responses](https://developers.openai.com/api/docs/guides/migrate-to-responses)):

| Field | Role |
|-------|------|
| `type: "function"` | Distinguishes from hosted tools (`web_search`, MCP, etc.) |
| `name` | Dispatch key; stable, versioned (`docs_search` not `search2`) |
| `description` | Selection signal (file 03) |
| `parameters` | JSON Schema object |
| `strict` | Recommended `true`: arguments must match schema via Structured Outputs |

**Call / result pairing:** model emits `function_call` with `call_id`, `name`, `arguments` (**JSON string** — parse it). You return `function_call_output` with the **same** `call_id` and a **string** output (JSON, error text, whatever; the model interprets it). Chat Completions uses `role: "tool"` + `tool_call_id` instead of `function_call_output` items — same pairing idea, different envelope.

**Custom / free-form tools:** OpenAI also documents tools that take/return free text when JSON Schema is a poor fit (e.g. code-ish payloads). Less structure for deterministic executors; use sparingly in Week 11.

**Strict mode constraints** (docs): enabling `strict: true` uses Structured Outputs and **rejects** incompatible schemas (must satisfy their subset: typically `additionalProperties: false`, all properties in `required`, limited union/optional patterns). Responses may **normalize** toward strict if you omit `strict`; Chat Completions stays non-strict by default. Fine-tuned models + parallel calls can **disable** strict for that turn. OpenAI: *we recommend always enabling strict mode* despite limitations.

**Parallel:** multiple function calls per turn; `parallel_tool_calls: false` for zero-or-one. Built-ins cannot join a parallel function batch on some GPT-5+ paths.

### Anthropic (Messages API)

**Client tools** ([Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)):

| Field | Role |
|-------|------|
| `name` | Dispatch key |
| `description` | Selection signal |
| `input_schema` | JSON Schema (not named `parameters`) |
| `strict: true` | Inputs guaranteed to match schema ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)) |

**Call / result pairing:** `tool_use` block (`id` like `toolu_…`, `name`, `input` as **object**, not string). Reply `tool_result` with `tool_use_id`, `content` (string, list of text/image/document/search_result blocks), optional `is_error`. Computer-use / browser-use member tools also require echoing `toolset_name`.

**Server tools** (`web_search`, `code_execution`, `tool_search`, …): run on Anthropic infra. Mix of client `tool_use` and `server_tool_use` in one assistant turn: your user message must contain **only** client `tool_result`s until server tools resolve, or you get 400 naming the unresolved server tool.

**`tool_choice`:** default `{ "type": "auto" }` — Claude may answer without tools. Can force a tool, force any tool, or `{ "type": "auto", "disable_parallel_tool_use": true }` (overview samples use this). Parallel tool use is a separate doc path.

**Unlike OpenAI:** no `role: tool`. History is still `user`/`assistant` with mixed content blocks. Formatting bugs look like application bugs (400), not model quality.

### Schema design levers (both)

- **Required vs optional** — strict modes often force every property listed to be required; model “optional” via enums like `"unspecified"` or split tools.  
- **Enums** — `entity: ticket|order|employee` on `structured_query` beats free-string table names.  
- **`additionalProperties: false`** — required for many strict pipelines.  
- **Parameter descriptions** — formats (`ISO-8601`), examples, units.  
- **Read vs write split** — `calendar_list_events` vs `calendar_create_event` (overview).  
- **Version names** — `docs_search_v2` when chunking changes; do not silently change meaning.  
- **Token cost** — every schema is prompt tokens every turn (unless deferred — file 03).

Map Week 4 structured outputs onto tools: **tool args are structured outputs**. Pydantic on the executor is defense in depth even with `strict` (provider bugs, custom tools, non-strict fallback).

### Untrusted results

Anthropic: tool results often come from the web, email, uploads, third-party APIs. Treat as **untrusted** (indirect prompt injection). Keep them in `tool_result` blocks, **not** concatenated into `system` or naked user text ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). Same rule for OpenAI `function_call_output` strings: delimit, don’t merge into developer instructions.

---

## Alternatives & Tradeoffs

| Choice | Pros | Cons |
|--------|------|------|
| Loose schema + post-validation | Flexible; easy to start | Model invents args; repair loops (Anthropic: 2–3 retries then apology) |
| `strict: true` | Fewer invalid calls | Schema subset; optional fields awkward; request rejected if schema illegal |
| Custom/free-form OpenAI tools | Good for messy text I/O | Weak executor contracts |
| Hosted / built-in tools | Less code | Data residency, less control, mixed-loop complexity |
| MCP-wrapped tools (Week 12) | Discovery/transport standard | Same JSON-Schema-ish surface; **not** a substitute for schema hygiene |
| One fat tool with a `action` enum | Fewer names | Giant schema; worse selection; harder authz |

Tradeoff: richer schemas improve disambiguation **and** burn tokens; near-duplicate parameter names across tools confuse selection (file 03).

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

---

## Necessity

Without a precise schema + description:

- Hallucinated parameters, omitted required fields, never-called tools.  
- Anthropic: invalid/missing params → retries 2–3 times then apology; **strict** eliminates that class ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).  
- Unpaired/misordered results are **hard API errors**.  
- `structured_query` without enums → model-authored SQL → data incident (Week 21 problem, Week 11 prevention).  
- Calendar create without `idempotency_key` in schema → you cannot safely retry (file 04).  
- Injection: stuffing search snippets into the system prompt lets a malicious doc jailbreak the agent.

---

## Industry Practice

- **Common:** copy `get_weather`; description “gets data”; no `strict`; args printed as Python dicts into the next user message (breaks Anthropic pairing).  
- **Senior:**  
  - Description encodes **when to use / when not to use** (see overview table).  
  - Parameter docs include formats; enums for closed sets.  
  - `strict` / Structured Outputs where supported; **Pydantic validate** anyway.  
  - Schemas live **next to executors** (one module per tool); generated OpenAPI is reviewed, not dumped.  
  - Version tool names; treat results as untrusted.  
  - OpenAI: parse `arguments` with `json.loads` in try/except → error output, don’t crash.  
- **FDE bar:** whiteboard both envelopes; explain why Anthropic `tool_result` must be first and immediately after `tool_use`; mention `strict` schema subset failures as a **release blocker**, not an LLM mystery.

OpenAI playground-generated schemas enable strict by default — copy the **constraints**, not only the happy JSON.

---

## Concrete Scenario

**OpenAI canonical:** `get_horoscope` with JSON Schema + `strict: true`, local execute, `function_call_output` + `call_id`, final NL: https://developers.openai.com/api/docs/guides/function-calling  

**Anthropic canonical:** `get_weather` `input_schema` + `tool_result`: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  

**Week 11 triad (implement these, not weather):**

1. `docs_search` — `query` + `k`; result JSON `{hits: [{doc_id, score, snippet, url}]}` — snippets stay inside the tool payload.  
2. `structured_query` — `entity` enum + `filters` + `limit`; executor compiles parameterized SQL/API; model never sees a connection string.  
3. `calendar_create_event` — required `idempotency_key`, `timezone`, ISO datetimes; reject if `end <= start` **in the executor** with an instructive error (file 04).

**Failure to show in a trace:** Responses request with `strict: true` and a schema that allows free additional properties → **HTTP error with constraint details**, not a clever model. Fix the schema; don’t disable strict “to unblock demo.”

Mahesh Murag (AI Engineer Summit, MCP workshop) — tools as a **product surface** (names, descriptions, schemas) even when transport becomes MCP next week: https://youtu.be/kQmXtrmQ5Zg

---

## Open Questions

- Will **programmatic tool calling** (model writes a script that calls tools in a sandbox) displace per-turn JSON for high-churn workflows?  
- How much schema complexity can models follow before **tool search / deferred loading** is mandatory (file 03)?  
- Should FDE wrappers expose a **single** internal schema AST compiled to OpenAI `parameters` and Anthropic `input_schema` (Week 4 client) — and who owns drift when one provider’s strict subset is stricter?  
- JSON Schema `format: date-time` — do providers actually enforce it under strict, or only `type`?

---

## Sources

- https://developers.openai.com/api/docs/guides/function-calling  
- https://developers.openai.com/api/docs/guides/migrate-to-responses  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
- https://openai.github.io/openai-agents-python/tools/  
- https://youtu.be/kQmXtrmQ5Zg  
- https://www.youtube.com/@aidotengineer  
