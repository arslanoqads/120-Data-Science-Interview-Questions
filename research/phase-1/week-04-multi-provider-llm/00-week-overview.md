# 00 — Week overview & syllabus mapping

> Week 4 — Multi-Provider LLM APIs  
> Research notes (raw).

---

## Fundamentals

Week 4 opens **Phase 1** by making the Week 1–3 service talk to real model providers correctly. Phase 0 proved packaging, HTTP, tests, and shippability; Week 4 proves you can orchestrate **messages, tools, streams, schemas, tokens, and caches** across OpenAI and Anthropic without treating either SDK as the product core.

The syllabus spine is:

1. **API mechanics** — roles, tool loops, streaming aggregation.  
2. **Structured outputs** — schema-guaranteed JSON / tool args, not prompt hope.  
3. **Token accounting** — pre-flight counts, window budgets, truncation/compaction.  
4. **Prompt caching** — prefix-stable prompts as a first-class cost/latency control.  
5. **Provider-agnostic client** — a port/adapter (hand-rolled or LiteLLM) so product code stays provider-neutral.

These five form one pipeline: assemble a cache-stable prompt → count → call with tools/structured format → stream/aggregate → validate → append tool results → repeat. Skipping any step shows up as wrong roles, truncated tool JSON, 400s on context overflow, or a sudden bill spike after a one-character system-prompt edit.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| Single-provider SDK everywhere | Speed; full feature surface | Lock-in; painful failover; role/tool remap later |
| Thin Protocol + two adapters (syllabus default) | Controllable semantics; testable ports | You own stream aggregation + cache fields |
| LiteLLM SDK / proxy as the only client | Breadth, fallbacks, spend UI | Lowest-common-denominator quirks; upgrade coupling |
| Framework-only (LangChain / Agents SDK) | Fast demos | Opaque role/tool/cache behavior when debugging |

For the flagship Deployment Copilot / RAG chatbot, Week 4 should prefer a **thin internal port** with optional LiteLLM for gateway/failover—not framework-as-core. Week 5 (prompts) and Week 11+ (agents) assume you already understand the wire protocol.

---

## Necessity

Concrete failure modes if Week 4 is skipped:

- Anthropic `system` stuffed into OpenAI-style roles (or vice versa) → instruction hierarchy bugs and cache misses.  
- Streaming tool args concatenated wrong → failed tool executions and hallucinated retries.  
- Prompt-only “return JSON” → silent schema drift into DBs/workflows.  
- Unbounded chat/tool transcripts → context 400s mid-agent loop.  
- Unstable prefixes → paying full input on every turn despite “caching enabled.”  
- Product code calling `openai.*` / `anthropic.*` directly → take-homes cannot swap models under a feature flag.

---

## Industry Practice

- **Common (demo AI):** one SDK, `print` the stream, `json.loads` the answer, no token budget, hope caching helps.  
- **Strong:** Protocol `LLMClient` with `complete` / `stream` / `count_tokens`; Pydantic schemas for structured outs and tool args; usage logging including cache read/write; prompt layout `stable → semi-stable → dynamic`.  
- **FDE bar:** can explain OpenAI Responses vs Chat Completions, Anthropic tool_result-in-user-message, cache breakpoint placement, and when LiteLLM’s OpenAI-shaped façade is a lie for a provider-specific feature.

---

## Concrete Scenario

Syllabus build intent: wrap OpenAI + Anthropic behind one client used by the FastAPI RAG chatbot. A support-style turn (“weather in SF”) exercises the full loop on both providers; a second path extracts a calendar event via structured outputs; a third path loads a long system+tools prefix and proves cache hits on follow-ups. Interviewers probe why the adapter exists and what breaks if you only use LiteLLM.

Related public bar: Patrick Dougherty (AI Engineer Summit) on agent-computer interface — tool payload shape (JSON vs XML by model) matters as much as the prompt:  
https://ai.engineer/talks/how-to-build-ai-agents-that-actually-work · https://www.youtube.com/watch?v=7MiFIhlkBoE

---

## Open Questions

- Standardize internal messages on OpenAI Responses items vs keep a minimal custom type?  
- How early should the gateway (LiteLLM proxy) appear vs in-process adapters?  
- Who owns prompt-cache key design in multi-tenant SaaS—platform team or product?  
- Does Week 5’s few-shot selection policy live in the prompt layer or the cache-layout layer?

---

## Sources

- Syllabus PDF (uploaded): AQ AI Engineer FDE Syllabus  
- https://developers.openai.com/api/docs/guides/function-calling  
- https://docs.anthropic.com/en/api/messages-streaming  
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching  
- https://docs.litellm.ai/docs/  
- https://ai.engineer/talks/how-to-build-ai-agents-that-actually-work  
