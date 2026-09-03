# 04 — Tool error handling and retry logic

> Week 11 — Agent fundamentals  
> Research notes (raw).

---

## Fundamentals

Tool failures are not one bucket. If you retry the wrong class, you either **amplify outages** or **duplicate side effects**. Three layers:

1. **Executor / HTTP** — your code talking to calendar, search, warehouse.  
2. **Observation to the model** — what the next prompt sees.  
3. **Outer agent loop** — whether to continue, stop, or escalate.

### Failure classes

| Class | Example | Retry in executor? | Tell the model? |
|-------|---------|--------------------|-----------------|
| Transient infra | 429, 5xx, timeout, connection reset | **Yes**, capped exponential backoff + jitter | Only if retries exhausted |
| Invalid model args | missing field, bad enum, `end < start` | **No** (strict should prevent; still happens) | **Yes**, instructive error |
| Unknown tool name | hallucinated `search_all` | **No** | **Yes**, list allowed names |
| Business-rule reject | calendar busy, ticket not found, ACL deny | **No** (not a blip) | **Yes**, what to try next |
| Auth / 401 / 403 | expired app token | **No** (fix creds; don’t spin) | User-safe message; **do not** leak tokens |
| Provider/server-tool | Anthropic web_search `max_uses_exceeded` | N/A (hosted) | Claude handles many server errors internally |
| Truncated / parse | `max_tokens` mid-JSON args | Don’t execute | Error observation or abort turn (file 05) |

### Anthropic pattern (canonical)

Always return a `tool_result` for **every** `tool_use_id`. On failure: `"is_error": true` and an **instructive** `content` (what failed + what to try next). Do **not** crash the loop — convert exceptions to error results ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

Documented examples:

- Execution: `ConnectionError: the weather service API is not available (HTTP 500)` → Claude may apologize or adapt.  
- Args: `Error: Missing required 'location' parameter` → Claude typically **retries 2–3 times** with corrections, then apologizes.  
- Strict mode **eliminates** the invalid-args class when the schema is compatible.

Write instructive errors (`Rate limit exceeded. Retry after 60 seconds.`) not `"failed"`.

**Unknown tool / TypeError:** zoom cookbook manual loop maps these to `is_error` so the model recovers ([Zoom cookbook](https://platform.claude.com/cookbook/multimodal-crop-tool)).

**Tool runner:** `generate_tool_call_response()` to inspect errors **before** send ([Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)).

**Server tools:** you do not send `is_error` for hosted web search; Claude documents codes like `too_many_requests`, `invalid_input`, `max_uses_exceeded`, `query_too_long`, `unavailable`.

**Security:** strip secrets and stack traces from model-visible messages. Tool results are untrusted (injection) — keep them in `tool_result` ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

### OpenAI pattern

No first-class `is_error` on `function_call_output`. Put the error **text** (still correlated by `call_id`) in the output string; the model treats it as observation and may retry ([Function calling](https://developers.openai.com/api/docs/guides/function-calling): output format is up to you). You **must** still answer every `call_id`. Prefer a **stable JSON** error shape in that string so *your* logs parse even if the model only reads prose:

```json
{"ok": false, "error_class": "transient_exhausted", "retryable": false, "user_message": "Calendar API unavailable. Try again later."}
```

Do not return HTML dumps or Python tracebacks.

### LangGraph pattern

Thinking-in-langgraph: **LLM-recoverable** errors (tool failures, parsing) → store error in state, loop back to the LLM; **transient** → retries in the node; **user-fixable** → interrupt (Week 13 HITL); **unexpected** → bubble up ([Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)). `ToolNode` advertises error handling for graph workflows ([Workflows and agents](https://docs.langchain.com/oss/javascript/langgraph/workflows-agents)). Copy the classification even if you are not on LangGraph yet.

### Application-level retries (distinct from model self-repair)

- **Transient HTTP:** backoff + jitter **inside** the tool executor **before** returning to the model; **max attempt count** (e.g. 3).  
- **Non-transient / auth / validation:** return error immediately; don’t burn retries.  
- **Dangerous side effects:** **no automatic retry** without **idempotency keys** (`calendar_create_event.idempotency_key`). HTTP 500 after the provider *maybe* created the event is the classic double-book.  
- **Consecutive identical failures:** circuit-break the **loop** even if `max_iterations` remains (same tool, same args, same error class ≥ N).  
- **Timeouts:** per-tool deadline (search 3s, SQL 10s, calendar 5s). A hung tool is a stuck worker.  
- **Parallel tools:** one failure should still produce results for the others (partial success) with `is_error` only on the failed `id`.

**Multiplier effect:** unbounded executor retries × unbounded model retries × unbounded loop = cost and duplicate writes.

---

## Alternatives & Tradeoffs

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

Tradeoff: instructive errors improve self-repair; **too much** internal detail becomes a prompt-injection and data-leak channel.

---

## Necessity

- Crash-on-exception aborts mid-`tool_use` → **illegal conversation** (missing results) → 400s / stuck UIs.  
- Generic `"failed"` → useless model retries.  
- Retrying `calendar_create_event` on 500 without idempotency → **two meetings**.  
- Returning stack traces → secret leakage + injection surface.  
- Retrying 403 → audit noise and lockouts.  
- Week 15: if traces don’t record `error_class`, you cannot tell infra from selection failures.

---

## Industry Practice

- **Common:** `try/except: raise` in tools; agent dies; user refreshes; retries the **whole** chat (duplicating writes).  
- **Senior:**  
  - Map exceptions → structured error results; never leave a `tool_use` unanswered.  
  - Classify retryable vs not **in one function** used by all tools.  
  - Idempotency keys on writes; **PUT/upsert** semantics where the API allows.  
  - Timeout per tool; log `tool_name`, latency, error class, attempt.  
  - Circuit breaker: N identical failures → `AgentStopped(tool_circuit)`.  
  - SDK hooks (Anthropic `generate_tool_call_response`) to redact before send.  
  - LangGraph: errors as state, not as thrown node exceptions, for recoverable classes.  
- **FDE bar:** draw the three layers; say out loud “I retry 429 in the executor; I never retry creates without an idempotency key; I always pair `tool_result`.”

Chase (AI Engineer): **reduce cost if wrong** — reversible actions, human correction. Retries are part of that cost: a retry of an irreversible tool *is* the expensive failure.

---

## Concrete Scenario

**Anthropic docs:** `is_error: true` + `ConnectionError: … (HTTP 500)` and missing-parameter correction retries: https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  

**Cookbook:** unknown tool names and `TypeError` on args become `is_error` in the manual loop: https://platform.claude.com/cookbook/multimodal-crop-tool  

**LangGraph:** `execute_tool` catch → `{"tool_result": f"Tool error: {str(e)}"}` → `goto="agent"`: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph  

**Week 11 lab (calendar write):**

1. User: book a slot. Model calls `calendar_create_event` with `idempotency_key=K`.  
2. Executor POSTs; API returns **500**. Executor retries **once** with the **same** key (calendar API dedupes) or returns `is_error` without retry if the API is not idempotent.  
3. Model may try again — executor **must** reuse `K` (pass through args) or refuse.  
4. Inject a **validation** error (`end` before `start`) — no HTTP retry; model-visible message: `Error: end must be after start (ISO-8601). Resend with a valid range.`  
5. Inject unknown tool `create_meeting` — result: `Unknown tool. Allowed: docs_search, structured_query, calendar_list_events, calendar_create_event.`

OpenAI equivalent: same strings in `function_call_output`, still one output per `call_id`: https://developers.openai.com/api/docs/guides/function-calling  

---

## Open Questions

- Should frameworks standardize a cross-provider `ToolError` shape (`code`, `retry_after`, `user_safe_message`, `retryable`)?  
- How many **model-visible** retries are optimal before a human (2–3 is Anthropic’s invalid-args anecdote — is that universal)?  
- Circuit breakers: per-tool vs per-vendor vs per-tenant?  
- Should `retryable: true` in the observation be allowed, or does that invite the model to hammer production?

---

## Sources

- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls  
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner  
- https://platform.claude.com/cookbook/multimodal-crop-tool  
- https://developers.openai.com/api/docs/guides/function-calling  
- https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph  
- https://docs.langchain.com/oss/javascript/langgraph/workflows-agents  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://youtu.be/kQmXtrmQ5Zg  
