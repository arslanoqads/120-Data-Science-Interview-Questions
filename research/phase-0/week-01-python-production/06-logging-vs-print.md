# 06 — Logging vs print debugging

> Week 1 concept research (deep). Legal sources only.

---

## Fundamentals

### print vs logging (stdlib doctrine)
Python Logging HOWTO task table:

| Task | Tool |
|------|------|
| Ordinary CLI user output | `print()` |
| Normal operational events | logger `info` / `debug` |
| Warnings | `warnings.warn` or logger `warning` |
| Errors | raise, or logger `error`/`exception`/`critical` |

`print` → stdout for interactive humans. **Logging** → leveled events via loggers, handlers, formatters; filterable; multiple destinations; library-safe.

### Logger hierarchy
`logging.getLogger(__name__)` creates hierarchical loggers. Libraries should **log but not configure**. Applications configure once (`dictConfig` / `fileConfig`).

### Levels
DEBUG &lt; INFO &lt; WARNING &lt; ERROR &lt; CRITICAL. Production default often INFO; DEBUG sampled or on demand.

### Structured logging
For Cloud Logging/Datadog/Loki, emit **JSON** with stable fields: `event`, `request_id`, `trace_id`, `model`, `token_usage`, `latency_ms`, `error_type`. **structlog** builds event dicts through a processor pipeline; often bridges to stdlib via `LoggerFactory`.

### Non-blocking I/O
Handlers that write to network/disk can block request workers. Pattern: **QueueHandler + QueueListener** (stdlib) so formatting/I/O runs on a background thread. MCoding “Modern Python logging” talk emphasizes `dictConfig`, QueueHandler, and library-vs-app configuration: https://www.youtube.com/watch?v=9L77QExPmI0

### Correlation with traces
OpenTelemetry: attach `trace_id` / `span_id` to log records (LoggingHandler or structlog processor reading current span). GenAI semantic conventions evolving for model/provider attributes—pair with Phase 4 observability.

### PII / prompt safety
Logs that dump full prompts/retrieved docs can leak secrets and user data. Redact or hash; log metadata (token counts, chunk ids) instead of raw content in prod.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| print | Zero setup | No levels; pollutes APIs; hard to silence in tests |
| basicConfig | Quick | Global; fights libraries; weak structure |
| dictConfig + stdlib | Standard; powerful | Verbose; easy to misconfigure |
| structlog | Ergonomic bound context; processors | Another dependency; must integrate with stdlib for libs |
| loguru | Nice DX | Nonstandard; some teams reject |
| OTel logs/traces only | Unified telemetry | Overkill for Week 1; still need local console |

**Tradeoff:** Over-logging costs $ and leaks PII; under-logging makes agent tool failures invisible.

---

## Necessity

Cloud Run / K8s with prints:
- Cannot filter severity in log sinks.  
- No `request_id` correlation across RAG retrieve → generate.  
- Secrets in stdout scraped by aggregators.  
- Libraries interleaved with app prints.  
- Load: sync logging blocks event loop / workers under traffic.

---

## Industry Practice

### Common
Leftover prints; `basicConfig(level=DEBUG)`; logs without correlation IDs; prompt text in INFO.

### Senior
- `getLogger(__name__)` everywhere in library/app code.  
- App-only `dictConfig` / structlog configure at startup.  
- JSON in prod; human-readable console in dev.  
- Bind `request_id` in middleware (contextvars).  
- QueueHandler for non-blocking.  
- Redaction filters for Authorization headers and prompt bodies.  
- Metrics/traces alongside logs (don’t overload logs as the only analytics).  
- Uvicorn access logs coordinated (often custom middleware instead of double access logging).

### LLM-specific fields (research checklist)
```
event=llm_call model=... provider=... input_tokens=... output_tokens=...
latency_ms=... cache_hit=... tool_name=... error_class=...
trace_id=... span_id=... request_id=...
```

---

## Concrete Scenario

- Logging HOWTO: https://docs.python.org/3/howto/logging.html  
- logging.config: https://docs.python.org/3/library/logging.config.html  
- QueueHandler: https://docs.python.org/3/library/logging.handlers.html#queuehandler  
- structlog: https://www.structlog.org/  
- MCoding YouTube: https://www.youtube.com/watch?v=9L77QExPmI0  
- OTel + Python logging bridge guides: https://www.dash0.com/guides/opentelemetry-logging-python  
- Structured logging + OTel patterns: https://oneuptime.com/blog/post/2025-01-06-python-structured-logging-opentelemetry/view  

**Scenario:** Intermittent 5xx on chatbot. Without structured logs, engineer SSHes and adds prints. With JSON logs + request_id, filter shows all failures share `provider=anthropic` + `error_class=TimeoutError` after a deploys—points to missing timeout budget, not “RAG is broken.”

---

## Open Questions

1. Maturity of OpenTelemetry GenAI semantic conventions for standardizing LLM log fields?  
2. Do agent traces (Langfuse/Phoenix) replace many INFO logs, or dual-write?  
3. Default log level for tool args in staging vs prod?  
4. Should Week 1 mandate structlog or is stdlib JSON formatter enough?

---

## Sources

- https://docs.python.org/3/howto/logging.html  
- https://docs.python.org/3/library/logging.html  
- https://docs.python.org/3/library/logging.config.html  
- https://docs.python.org/3/library/logging.handlers.html  
- https://www.structlog.org/  
- https://www.youtube.com/watch?v=9L77QExPmI0  
- https://www.dash0.com/guides/opentelemetry-logging-python  
- https://oneuptime.com/blog/post/2025-01-06-python-structured-logging-opentelemetry/view  
- https://python-observability.com/modern-python-logging-libraries-deep-dive/structlog-architecture-and-setup/  
- https://opentelemetry.io/docs/specs/semconv/  
