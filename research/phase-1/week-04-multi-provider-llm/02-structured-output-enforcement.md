# 02 — Structured output enforcement

> Week 4 concept research (deep). Legal sources only.

---

## Fundamentals

### Problem
Downstream code needs typed objects (invoices, classifications, tool args, eval labels). Free-form generation routinely omits keys, invents enums, wraps JSON in markdown fences, or emits invalid JSON. Prompt-only “return JSON” is not an SLA.

### OpenAI Structured Outputs
With constrained decoding via JSON Schema, the API generates responses that **adhere to the schema**—not merely valid JSON syntax.

Chat Completions shape (classic):

```json
"response_format": {
  "type": "json_schema",
  "json_schema": { "name": "...", "strict": true, "schema": { ... } }
}
```

Responses API uses `text.format` with `type: "json_schema"` and `strict: true`. Distinct from older **JSON mode** (`type: "json_object"`), which guarantees JSON syntax but **not** schema adherence. OpenAI recommends Structured Outputs over JSON mode whenever available (gpt-4o snapshots and later; prefer current flagship for new work).

Python/JS SDKs accept **Pydantic / Zod** via `.parse()` helpers that: (1) convert the model to a strict JSON Schema, (2) call the API, (3) deserialize into a typed object (`message.parsed` / `output_parsed`). Benefits called out in docs: reliable type-safety, fewer retries, **explicit refusals** detectable separately from parse failures. Length / content_filter finish reasons should be treated as first-class failures, not silent empty parses.

Two OpenAI surfaces for structure:

| Surface | When |
|---------|------|
| Structured Outputs via **function/tool calling** (`strict` tools) | Model must call a tool / perform a side effect with typed args |
| Structured Outputs via **`json_schema` response format** | Model answers the user with a typed object (extraction, UI schema, CoT scaffolding) |

### Anthropic Structured Outputs
Two complementary features:

1. **JSON outputs** via `output_config.format` with `type: "json_schema"` (legacy/beta: `output_format`; SDKs may still accept the old name on `messages.parse()` and translate).  
2. **Strict tool use** (`strict: true` on tool definitions) guaranteeing tool names/inputs match schemas.

Constrained decoding guarantees schema-compliant text/tool inputs. SDKs may transform unsupported schema constraints into description text and validate against the original schema. Older pattern: force a single extraction tool with `tool_choice` when native structured outputs were unavailable.

### Pydantic / Zod as the contract
Schema-as-code keeps API schema and application types synchronized. Field descriptions become soft guidance to the model; validators (`Field`, custom validators) enforce **business rules** after (or instead of) model-side constraints. One model per task; generate provider schemas from it—never hand-maintain divergent JSON Schema copies.

### Retry-on-malformed (fallback path)
Classic pattern: prompt for JSON → `json.loads` → Pydantic validate → on failure, re-prompt with the error (“fix these fields…”) up to N times.

Still needed when:

- Model/provider lacks strict structured outputs  
- Using JSON mode only  
- **Semantic** validators fail even when syntax/schema pass (`end_date >= start_date`)  
- Output truncated (`finish_reason: length` / `max_tokens`)

With true structured outputs, syntax/schema retries largely disappear; semantic retries and refusal handling remain.

---

## Alternatives & Tradeoffs

| Technique | Guarantee | Cost / latency | Notes |
| --- | --- | --- | --- |
| Prompt-only “return JSON” | None | Cheap | Production-fragile |
| JSON mode | Valid JSON | Low | No schema adherence |
| Structured Outputs / constrained decoding | Schema adherence | Slight overhead; schema compile/cache | Preferred when available |
| Forced tool for extraction | Tool-arg shape | Extra tool machinery | Good fallback; mixes with agent tools carefully |
| Client retry + repair prompt | Best-effort | Multiplies cost | Keep for semantic validation failures |
| Grammar / outlines (local models) | Strong local control | Infra complexity | Self-hosted path |

Unsupported schema features vary by provider (numeric ranges, complex `oneOf`, deep recursion)—check each docs’ limitations list before designing contracts.

---

## Necessity

Any pipeline that writes to a database, triggers workflows, or feeds another agent step needs machine-checkable outputs. Prompt-only formatting is insufficient for SLAs.

Failure modes if skipped:

1. Markdown-fenced JSON breaks `json.loads` in CI only sometimes.  
2. Missing required keys → null pointer / silent default in business logic.  
3. Invented enum values → invalid state machine transitions.  
4. Agent tool args that “look right” but fail server validation → infinite retry loops.  
5. Eval labels / golden-set extractors that drift week to week → false eval progress.

---

## Industry Practice

### Common (weak)
- “Respond with JSON only” in the system prompt; strip fences with regex.  
- Duplicate hand-written JSON Schema in OpenAI and Anthropic configs.  
- No distinction between refusal, truncation, and parse error.

### Strong / senior
- Define **one Pydantic/Zod model per task**; generate OpenAI/Anthropic schemas from it.  
- Prefer **strict structured outputs** when the model supports them; keep **retry+repair** for unsupported providers/models and for semantic checks.  
- Treat refusals and length truncation as first-class outcomes (OpenAI `.parse()` raises on length/content_filter).  
- For agents: structured outputs for final answers; **strict tools** for side effects; avoid free-form JSON in the same turn as unconstrained prose.  
- Log raw text + validation errors for offline prompt/schema improvement.  
- Version schemas (`schema_version` field or package version) so cached prompts and clients stay compatible.

### RAG chatbot application
Use structured outputs for: citation objects, confidence+answer envelopes, routing classifications. Use strict tools for: `retrieve`, `create_ticket`, `deploy_action`. Never trust free-form tool JSON for side effects.

---

## Concrete Scenario

OpenAI’s Structured Outputs guide shows extracting a calendar event (`name`, `date`, `participants`) via `responses.parse` / `chat.completions.parse` with a Zod/Pydantic schema—no manual `json.loads`. Anthropic’s structured outputs docs show the parallel `output_config.format` / `messages.parse()` path for schema-guaranteed JSON text. A production extraction service would: call parse → on schema success run domain validators → on semantic failure retry once with the validation error → else dead-letter.

URL: https://developers.openai.com/api/docs/guides/structured-outputs  
Companion: https://platform.claude.com/docs/en/build-with-claude/structured-outputs  
SDK helpers: https://github.com/openai/openai-python/blob/main/helpers.md

---

## Open Questions

1. Which schema features remain unsupported across providers (numeric ranges, complex `oneOf`, recursive types)?  
2. When do constrained decoding and extended thinking / high reasoning effort conflict?  
3. Is repair-prompting still worth it once strict mode is on, or only for semantic validators?  
4. How to version schemas so cached prompts and client types stay compatible?  
5. Should multi-provider gateways reject non-strict schemas at the edge?

---

## Sources

- https://developers.openai.com/api/docs/guides/structured-outputs  
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs  
- https://github.com/openai/openai-python/blob/main/helpers.md  
- https://docs.pydantic.dev/latest/  
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use (strict tool use)  
