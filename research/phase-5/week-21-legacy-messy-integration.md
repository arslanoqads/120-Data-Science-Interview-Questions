# Week 21 — Legacy and messy-data integration

> Phase 5 — Production, Cost, and Systems Engineering  
> Raw research notes (not textbook prose). Legal sources only.

---

## Concept: Integrating LLM systems with non-trivial existing data (messy SQL)

### Fundamentals
Enterprise data rarely looks like a clean tutorial schema. Expect denormalized tables, overloaded status codes, nulls with secret meanings, duplicated entities, and “columns that changed meaning in 2019.” An LLM integration must **discover**, **document**, and **constrain** that reality—via SQL tooling with guardrails, semantic views, or curated marts—rather than dumping raw `SELECT *` into prompts.

### Alternatives & Tradeoffs
| Approach | Pros | Cons |
|----------|------|------|
| Text-to-SQL over prod DB | Fast demos | Injection, wrong joins, perf bombs |
| Read replicas + semantic layer | Safer; governed metrics | Upfront modeling |
| RAG over exported docs/CSV | Avoids live SQL risk | Stale; loses relational queries |
| Hybrid: curated views + retrieval | Best of both | Dual pipelines to maintain |

Tradeoff: model creativity vs allowlisted tables/columns; latency of multi-step SQL agents vs one trusted stored procedure.

### Necessity
FDE interviews stress the “integration wall.” Skipping schema archaeology → agents invent joins, leak PII columns, or answer from stale replicas while ops trusts live DB. Syllabus: connect to genuinely messy SQL and survive imperfect schema.

### Industry Practice
- **Common:** LangChain SQL agent on wide-open credentials.
- **Senior:** least-privilege DB user; allowlisted views; row-level security; EXPLAIN budgets; golden query evals; human confirm for writes; data dictionary in repo.

### Concrete Scenario
Google SRE Book chapters on data integrity / dealing with complex systems (free): https://sre.google/sre-book/table-of-contents/  
Enterprise text-to-SQL failure modes discussed widely in vendor blogs; start from governed semantic layers (dbt docs as context): https://docs.getdbt.com/docs/build/documentation

### Open Questions
- Will structured semantic layers + MCP SQL servers displace free-form text-to-SQL agents?
- How to evaluate SQL agent safety beyond “query executed”?

### Sources
- https://sre.google/sre-book/table-of-contents/
- https://docs.getdbt.com/docs/build/documentation

---

## Concept: ETL/ingestion that tolerates malformed or inconsistent input

### Fundamentals
Ingestion for RAG/agents must assume broken encodings, truncated JSON, mixed date formats, HTML-in-CSV, and schema drift. **Tolerant ETL** validates, quarantines bad rows, continues with partial batches, and emits metrics on reject rates—rather than failing the whole job or silently dropping fields.

### Alternatives & Tradeoffs
| Strategy | Behavior | Risk |
|----------|----------|------|
| Fail-fast job | Stops on first bad record | Easy ops signal; blocks freshness |
| Dead-letter / quarantine | Keep good rows; isolate bad | Need replay tooling |
| Best-effort coerce | Infer types aggressively | Silent corruption |
| Schema registry + versions | Explicit evolution | Process overhead |

For LLM corpora: prefer quarantine + alert over “always embed something,” which poisons the index.

### Necessity
Customer file drops are messy. Without quarantine, one bad PDF parser version can wipe or pollute a vector index overnight (corpus drift compounded by garbage chunks).

### Industry Practice
- **Common:** notebook scrape → embed → hope.
- **Senior:** idempotent load keys; content hashes; parser version metadata on chunks; DLQ dashboards; canary ingest on sample before full reindex.

### Concrete Scenario
SRE-style monitoring of data pipelines and purposeful partial failure handling: https://sre.google/sre-book/embracing-risk/  
YouTube: Strange Loop / data pipeline talks on poison messages — https://www.youtube.com/results?search_query=strange+loop+poison+message+queue

### Open Questions
- Auto-repair with LLMs on quarantined rows: helpful or a new corruption source?
- When to rebuild indexes vs incremental patch after parser fixes?

### Sources
- https://sre.google/sre-book/embracing-risk/
- https://sre.google/sre-book/table-of-contents/

---

## Concept: Designing for partial failure (customer system down or slow)

### Fundamentals
Distributed integrations fail partially: auth OK, CRM timeout; vector DB up, LLM 429; half of fan-out tools succeed. Design for **timeouts, bulkheads, retries with jitter, circuit breakers, graceful degradation** (answer from cache/RAG without live SQL), and clear user-visible degraded modes—not a single global exception.

### Alternatives & Tradeoffs
| Tactic | Helps | Cost |
|--------|-------|------|
| Short timeouts + retry | Transient blips | Duplicate side effects if not idempotent |
| Circuit breaker | Protects your service | Needs fallback UX |
| Queue + async completion | Survives partner slowness | Harder interactive UX |
| Cached / last-known answers | Availability | Staleness / compliance issues |

CAP/PACELC literacy (Week 3) applies: during partner partition, do you refuse or serve stale?

### Necessity
FDE reality: customer APIs flake. Without partial-failure design, your agent becomes their outage amplifier (retry storms) or hard-downs your entire Copilot when one tool is slow.

### Industry Practice
- **Common:** default HTTP client timeouts; stack traces to users.
- **Senior:** per-dependency budgets; bulkheaded thread/async pools; explicit `degraded` responses; SLOs on dependency errors; chaos tests in staging.

### Concrete Scenario
Google SRE Book — handling overload / dependencies: https://sre.google/sre-book/table-of-contents/  
Classic circuit breaker narrative (Martin Fowler): https://martinfowler.com/bliki/CircuitBreaker.html

### Open Questions
- Should agent planners replan around unavailable tools automatically, or fail closed?
- How to expose degraded-mode truthfulness in regulated industries?

### Sources
- https://martinfowler.com/bliki/CircuitBreaker.html
- https://sre.google/sre-book/table-of-contents/

---

## Concept: Idempotency in agent actions with side effects

### Fundamentals
Agents retry. Networks retry. Humans double-click. **Idempotency** means repeating the same logical action with the same key does not duplicate side effects (double charge, double ticket). Patterns: client `Idempotency-Key`, server dedup table, forward provider keys (e.g. Stripe), checkpoints that skip completed steps, transactional outbox for event emission. LLMs may rethink tool args on retry—so keys must bind to the *business action*, and/or cache the decided action before execution.

### Alternatives & Tradeoffs
| Pattern | Strength | Weakness |
|---------|----------|----------|
| Natural idempotency (`PUT` absolute state) | Simple | Not all actions fit |
| Idempotency key + response cache | Standard for payments/APIs | Key design bugs cause either blocks or dupes |
| Dedup ledger + checkpoint resume | Fits multi-step agents | Requires durable store |
| Compensating transactions (sagas) | Undo path | Compensations also need idempotency |

Tradeoff: at-least-once delivery + exactly-once *effects* via dedup—not magical exactly-once networking.

### Necessity
Without idempotency, HITL approve + timeout + retry creates duplicate CRM updates—the exact outage that gets AI projects pulled. Week 14 side-effect agents inherit this requirement.

### Industry Practice
- **Common:** “just call the API”; rely on model not to retry.
- **Senior:** every mutating tool requires a key; tools are replay-safe; resume-from-checkpoint skips done steps; tests kill process mid-action and assert single effect; audit log shows key + outcome.

### Concrete Scenario
Idempotency key storage patterns: https://www.distributedrequest.com/backend-implementation-storage-patterns/  
Stripe-style layered idempotency discussion: https://backendbytes.com/articles/idempotency-patterns-distributed-systems/  
Agent-focused retry-safe patterns: https://www.buildmvpfast.com/blog/idempotent-ai-agent-retry-safe-patterns-production-workflow-2026  
YouTube: “Idempotency” talks (Stripe/API design) — https://www.youtube.com/results?search_query=stripe+idempotency+keys+api+design

### Open Questions
- How to key idempotency when the model changes arguments slightly but user intent is the same?
- Should MCP tool specs require idempotency metadata as a standard field?

### Sources
- https://www.distributedrequest.com/backend-implementation-storage-patterns/
- https://backendbytes.com/articles/idempotency-patterns-distributed-systems/
- https://www.buildmvpfast.com/blog/idempotent-ai-agent-retry-safe-patterns-production-workflow-2026
- https://docs.stripe.com/api/idempotent_requests
