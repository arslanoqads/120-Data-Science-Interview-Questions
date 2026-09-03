# 05 — Provider-agnostic client (wrapper interface)

> Week 4 concept research (deep) — syllabus build augment. Legal sources only.

---

## Fundamentals

### Why a wrapper exists
Product code should not import `openai` and `anthropic` at every call site. Roles, tool result shapes, stream events, structured-output knobs, token counting, and cache fields all diverge (concepts 01–04). A **provider-agnostic client** is the port that:

1. Accepts a stable internal request (messages, tools, response schema, stream flag, cache hints).  
2. Adapts to OpenAI (Chat Completions and/or Responses) or Anthropic Messages.  
3. Emits a stable internal response (text, tool calls, usage including cache, finish reason).  
4. Is mockable in Week 2-style pytest without live keys.

This is the Week 4 **syllabus build**: implement the port even if the syllabus bullet list only names mechanics/structured outs/tokens/caching—the build is how those concepts become shippable code.

### Hand-rolled ports (recommended core)
Define a small Protocol / ABC, e.g.:

```python
class LLMClient(Protocol):
    async def complete(self, req: LLMRequest) -> LLMResponse: ...
    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMEvent]: ...
    async def count_tokens(self, req: LLMRequest) -> int: ...
```

Implement `OpenAIAdapter` and `AnthropicAdapter` that:

- Map `developer`/`system` ↔ Anthropic top-level `system`  
- Map tool results (`role: tool` ↔ `tool_result` in user content)  
- Aggregate streaming tool-arg deltas  
- Attach structured-output / strict-tool flags  
- Normalize usage (`cached_tokens` vs `cache_read_input_tokens`)

Keep the internal type **minimal**—enough for your product—not a clone of either provider’s entire surface.

### LiteLLM (library + gateway)
[LiteLLM](https://docs.litellm.ai/docs/) unifies 100+ providers behind the **OpenAI Chat Completions shape**:

- SDK: `litellm.completion(model="anthropic/...", messages=..., tools=..., stream=True)`  
- Responses always look like OpenAI `chat.completion` / chunks  
- Maps provider exceptions to OpenAI exception types  
- **Router**: retries, fallbacks, load balancing across deployments  
- **Proxy / AI Gateway**: virtual keys, budgets, spend tracking, admin UI, OpenAI-compatible `base_url`

LiteLLM also documents function calling translation, streaming, and cross-provider prompt caching helpers—useful, but still an OpenAI-shaped façade over Anthropic semantics.

### What “agnostic” does **not** mean
You cannot pretend OpenAI built-in tools ≡ Anthropic server tools, or that Responses item state ≡ Messages content blocks, without a capability matrix. Agnostic means: **one call site**, explicit feature flags, honest degradation—not infinite compatibility.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons | When |
|----------|------|------|------|
| **Hand-rolled Protocol + 2 adapters** | Full control; clear semantics; easy to mock | You maintain stream/role edge cases | Syllabus default; product core |
| **LiteLLM SDK in-process** | Fast multi-provider; fallbacks; cost callbacks | Dependency; LCD quirks; upgrade coupling | Prototypes; many providers |
| **LiteLLM Proxy gateway** | Central keys/budgets/UI; any OpenAI client works | Ops surface; another hop; debugging transforms | Platform / multi-team |
| **OpenAI SDK only + Anthropic later** | Speed | Lock-in; rewrite | Throwaway demos |
| **Heavy framework (LangChain, etc.)** | Batteries | Opaque adapters; hard eval/debug | Only if team already standardized |

Hybrid common in industry: **hand-rolled port for app semantics** + optional LiteLLM/proxy for failover and spend controls.

---

## Necessity

Without a port:

1. Feature flags for model choice touch every service file.  
2. Unit tests need live keys or duplicated mocks per SDK.  
3. Streaming/tool bugs get fixed in one provider path only.  
4. Prompt-cache and token helpers diverge → cost regressions.  
5. Take-homes fail the “swap Anthropic under the hood” interview ask.

---

## Industry Practice

### Common (weak)
- `if provider == "openai": ... else: ...` sprinkled in route handlers.  
- LiteLLM as a black box with no tests of role remapping.  
- No `count_tokens` on the interface; no normalized usage logging.

### Strong / senior
- Protocol in `src/<pkg>/llm/port.py`; adapters in `.../adapters/`.  
- Dependency-injected into FastAPI (Week 2 `dependency_overrides`).  
- Golden tests: same internal request → assert mapped Anthropic/OpenAI payloads (snapshot or contract).  
- Capability flags: `supports_structured_outputs`, `supports_prompt_cache_explicit`, `supports_server_tools`.  
- Usage normalized to `{input, output, cache_read, cache_write, model, provider}`.  
- Dougherty / ACI lesson: when adding a third model family, fix the **tool response format** in the adapter, not only the system prompt.  
- LiteLLM YouTube guidance: treat gateway for org enablement; keep agent loop ownership in your code (`https://www.youtube.com/watch?v=_BuWC220CzA`).

### Syllabus build checklist
1. `LLMRequest` / `LLMResponse` / `ToolCall` dataclasses or Pydantic models.  
2. OpenAI + Anthropic adapters with streaming aggregation.  
3. Structured-output path wired to concept 02 schemas.  
4. `count_tokens` pre-flight (concept 03).  
5. Cache-control / breakpoint fields pass-through (concept 04).  
6. Pytest mocks the Protocol—never live keys in unit CI.

---

## Concrete Scenario

Build `WeatherAgent` behind `LLMClient`. With `OPENAI_ADAPTER`, the weather tool uses Chat Completions/Responses function calling and `role: tool` results. Flip config to `ANTHROPIC_ADAPTER`: same agent code, but adapter places policy in top-level `system` and wraps tool results as `tool_result` user blocks; stream aggregator concatenates `partial_json`. Optionally put LiteLLM proxy in front for spend limits without changing the Protocol—only the adapter’s HTTP target.

LiteLLM getting started: https://docs.litellm.ai/docs/  
Function calling guide: https://docs.litellm.ai/docs/completion/function_call  
OpenAI tools: https://developers.openai.com/api/docs/guides/function-calling  
Anthropic tools: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use  
Talk (ACI / multi-model): https://www.youtube.com/watch?v=7MiFIhlkBoE  
Talk (LiteLLM agents): https://www.youtube.com/watch?v=_BuWC220CzA

---

## Open Questions

1. Should the internal event model follow Responses items for future-proofing, or stay smaller?  
2. When does LiteLLM proxy replace in-process adapters entirely for FDEs embedding at a customer?  
3. How to version adapter behavior when providers rename `system`↔`developer` again?  
4. Is a shared community “LLM port” (OpenAI-compat only) enough, or do serious apps always need Anthropic-native escape hatches?  
5. Where should prompt templates live relative to the client—same package or Week 5 prompt service?

---

## Sources

- https://docs.litellm.ai/docs/  
- https://docs.litellm.ai/docs/completion/function_call  
- https://docs.litellm.ai/docs/routing  
- https://docs.litellm.ai/docs/proxy/reliability  
- https://github.com/BerriAI/litellm  
- https://developers.openai.com/api/docs/guides/function-calling  
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use  
- https://www.youtube.com/watch?v=_BuWC220CzA  
- https://www.youtube.com/watch?v=7MiFIhlkBoE  
- https://ai.engineer/talks/how-to-build-ai-agents-that-actually-work  
