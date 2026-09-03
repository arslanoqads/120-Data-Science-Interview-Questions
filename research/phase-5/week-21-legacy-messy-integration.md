# Week 21 — Legacy & Messy Integration (SQL, ETL, Partial Failure, Idempotency)

> Phase 5 · Production, Cost, and Systems  
> Raw source material for FDE gate. Legal/public sources only.

---

## Concept: Integrating LLM systems with non-trivial existing data (messy SQL schemas)

### Fundamentals
Enterprise data is rarely warehouse-clean. FDE work means connecting agents/RAG to **production schemas** with:

- Cryptic table/column names (`CUST_XREF_V3`, `stat_cd`)
- Overloaded columns (status `1/2/3` meaning different things per division)
- Soft deletes (`deleted_at`, `is_active=0`) inconsistently applied
- Multiple sources of truth (CRM vs billing vs spreadsheet exports)
- Sparse documentation; tribal knowledge in Slack
- PII mixed into free-text notes
- Timezone-naive timestamps; currency in cents vs dollars
- Polymorphic FKs / EAV tables

LLM integration patterns that work on messy SQL:

1. **Semantic layer first** — curated views / metrics definitions (dbt, LookML, Cube) so the LLM never sees raw 400-table ERDs.
2. **Text-to-SQL with allowlists** — constrain to approved views; row-level security; read-only roles; `LIMIT`; statement timeouts.
3. **RAG over data docs** — ingest data dictionaries, example queries, join paths; retrieve before generating SQL.
4. **Hybrid tools** — prefer vetted parameterized tools (`get_invoice(id)`) over open-ended SQL for high-risk domains.
5. **Schema grounding** — dump filtered `information_schema` + sample rows (redacted) into context; version the schema snapshot.

Do **not** paste entire schemas into prompts — token cost, confusion, and leakage.

### Alternatives & Tradeoffs
| Approach | Accuracy | Safety | Effort |
|----------|----------|--------|--------|
| Open text-to-SQL on raw OLTP | Fragile | Dangerous | Low upfront |
| Semantic views + text-to-SQL | Higher | Better | Medium |
| Hand-built tools only | Highest | Highest | High |
| Copy to warehouse then AI | Cleaner | Lag | ETL cost |
| Fine-tuned schema linker | Strong | Still needs RLS | ML cost |

### Necessity
Pointing an agent at raw prod DB without RLS → data breach or accidental `UPDATE`. Ignoring soft deletes → “customers that don’t exist” in answers. Ignoring dual currency/timezone → wrong financial summaries and lost trust.

### Industry Practice
**Common:** dump schema into system prompt; hope.  
**Strong:** curated semantic layer; approved join graph; eval set of natural-language→SQL with execution accuracy; shadow mode (generate SQL, don’t run); human approve for write paths; column-level masking for PII; tenant predicates injected by middleware not by the model.

### Concrete Scenario
Strange Loop / industry talks on “legacy data” and production systems (conference archive):  
https://www.youtube.com/@StrangeLoopConf  

Google SRE book — data processing pipelines (complexity of real pipelines, consistency challenges):  
https://sre.google/sre-book/data-processing-pipelines/

Example of enterprise AI needing isolation over tenant data stores (pool vs silo) — schema mess compounds multi-tenancy:  
https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/

### Open Questions
- When is it cheaper to fix the semantic layer than to push harder on agent reasoning?
- Can LLMs maintain a living data catalog from query logs safely?
- OLTP vs replica vs warehouse: which is the default tool target for agents?

### Sources
- https://sre.google/sre-book/data-processing-pipelines/
- https://sre.google/workbook/data-processing/
- https://www.youtube.com/@StrangeLoopConf
- https://docs.getdbt.com/docs/build/models (semantic modeling adjacent — public docs)

---

## Concept: ETL / ingestion that tolerates malformed and inconsistent input

### Fundamentals
Customer file drops, webhook payloads, and “CSV from finance” violate contracts. Production ingestion must assume:

- Wrong encodings (Windows-1252 labeled as UTF-8)
- Extra/missing columns; reordered headers
- Duplicate primary keys; late-arriving updates
- Null vs empty vs `"NULL"` string
- Partially truncated JSON; trailing commas
- Schema drift without notice

**Tolerant ETL design:**

1. **Land raw first** (bronze/raw bucket) — immutable bytes + metadata (source, received_at, checksum).
2. **Validate** with explicit contracts (JSON Schema, Great Expectations, pydantic) → quarantine bad records, don’t fail the whole batch blindly.
3. **Normalize** to typed canonical model (silver).
4. **Publish** to serving stores / vector indexes (gold) with versions.
5. **Dead-letter** + replay; metrics on quarantine rate.
6. **Idempotent upserts** on business keys so retries don’t duplicate.

For LLM corpora: extraction (PDF/HTML) fails often — keep parent document ID, chunk checksums, and allow partial corpus updates.

Google SRE workbook emphasizes **idempotent mutations** and **two-phase mutations** for pipelines so reprocessing doesn’t corrupt stores, and canaries don’t write bad data unchecked:  
https://sre.google/workbook/data-processing/

### Alternatives & Tradeoffs
| Strategy | Pros | Cons |
|----------|------|------|
| Fail-fast entire job | Simple | One bad row blocks business |
| Per-row quarantine | Resilient | Operational load to fix DLQ |
| Schema-on-read | Flexible | Garbage reaches consumers |
| Contract tests with producers | Prevents issues | Needs org power |
| LLM to “fix” rows | Tempting | Quietly invents fields — dangerous |

Use LLMs for **suggestions** on messy mappings in staging; do not silently auto-write production mappings without tests.

### Necessity
Brittle ETL that aborts on first bad row creates perpetual firefighting and empty RAG indexes. Silent coercion (`parseInt` failures → 0) creates wrong AI answers that look authoritative. Without raw landing, you cannot replay after fixing parsers.

### Industry Practice
**Common:** cron script + `ON ERROR FAIL`.  
**Strong:** medallion architecture; contract monitoring; canary on pipeline code; idempotent upserts; data SLOs (freshness, completeness); quarantine dashboards; schema registry for events; PII detection on ingest before vectors.

### Concrete Scenario
SRE Workbook — Improve and Optimize Data Processing Pipelines (canarying pipelines, idempotent & two-phase mutations):  
https://sre.google/workbook/data-processing/

SRE Book — Managing Data Processing Pipelines:  
https://sre.google/sre-book/data-processing-pipelines/

### Open Questions
- How much “LLM data cleaning” is acceptable before audit/compliance says no?
- Vector index updates: rebuild vs incremental when 5% of source rows were quarantined?
- Who owns quarantine SLAs — data eng or the FDE embedding the corpus?

### Sources
- https://sre.google/workbook/data-processing/
- https://sre.google/sre-book/data-processing-pipelines/
- https://sre.google/sre-book/distributed-periodic-scheduling/

---

## Concept: Designing for partial failure (customer system down or slow)

### Fundamentals
Your AI feature depends on **their** CRM, ERP, ticketing, SharePoint, email, and IdP. Partial failure is the default:

- Timeouts and 503s
- Rate limits
- Stale read replicas
- Auth token expiry mid-job
- Region outage of one SaaS tool while others live

**Design principles:**

1. **Timeouts everywhere** — connect + read deadlines; no infinite waits on tool calls.
2. **Bulkheads** — isolate thread/connection pools per dependency so one stuck CRM doesn’t block the LLM provider client.
3. **Circuit breakers** — stop calling a sick dependency; fail fast; probe half-open.
4. **Graceful degradation** — answer from RAG cache with caveat; skip enrichment; queue for later; switch to human handoff.
5. **Retries with exponential backoff + jitter** — only on idempotent/safe calls (SRE best practice):  
   https://sre.google/sre-book/service-best-practices/
6. **Deadline propagation** — agent run has a total budget; tool calls inherit remaining time.
7. **Status surfaces** — tell the user/agent *which* dependency failed (`CRM_TIMEOUT`), don’t swallow into generic “something went wrong.”
8. **Async for slow paths** — accept job, process when customer system recovers; webhook/resume.

Google SRE overload chapter: shed load, degrade answers, avoid retry storms:  
https://sre.google/sre-book/handling-overload/

### Alternatives & Tradeoffs
| Mode | UX | Correctness |
|------|----|-------------|
| Fail closed | Error message | Safe |
| Serve stale | Fast | May be wrong |
| Queue + notify | Delayed success | Good for tickets/emails |
| Proceed without tool | Partial answer | Must label missing context |
| Multi-provider failover | Resilient | Consistency differences |

Agents that **blindly retry** non-idempotent POSTs create duplicate tickets/orders (next concept).

### Necessity
A single hung customer API without timeouts pins all workers → full platform outage (your fault in the customer’s eyes). No degradation path → brittle demos and unpaid renewals. No structured dependency errors → the LLM retries uselessly and burns tokens.

### Industry Practice
**Common:** default HTTP client timeout or none; try/except log.  
**Strong:** per-dependency SLOs; chaos tests (latency injection); explicit tool error types in the agent observation channel; runbooks; fallback model provider; “degraded mode” product copy; queue depth alerts when customer system is down.

### Concrete Scenario
SRE Book — Handling Overload; Service Best Practices (retries, degradation):  
https://sre.google/sre-book/handling-overload/  
https://sre.google/sre-book/service-best-practices/

KubeCon talks on resilience / chaos (CNCF):  
https://www.youtube.com/@cncf

### Open Questions
- How should multi-agent systems share circuit-breaker state?
- When is “answer without live CRM” legally acceptable in regulated advice?
- Product UX for multi-hour customer outages on async agent jobs?

### Sources
- https://sre.google/sre-book/handling-overload/
- https://sre.google/sre-book/service-best-practices/
- https://sre.google/sre-book/distributed-periodic-scheduling/
- https://www.youtube.com/@cncf

---

## Concept: Idempotency in agent actions with side effects

### Fundamentals
Agents retry. Networks duplicate. Users double-click. Queues redeliver. Any tool that **sends email, charges cards, creates tickets, updates CRM, or triggers workflows** needs **idempotency**.

Core pattern (industry-standard, e.g. Stripe-style):

1. Client/agent generates an **idempotency key** once per **business intent** (not once per HTTP attempt).
2. Send key with the write (`Idempotency-Key` header or equivalent).
3. Server **atomically claims** the key (DB unique constraint / `SET NX`).
4. Execute side effect once; **store the response** with the key.
5. Retries return the **same stored outcome**.
6. TTL the key ≥ 2× max client retry window (Stripe documents 24h retention for keys):  
   https://docs.stripe.com/api/idempotent_requests

Agent-specific rules:

- Mint keys at **plan time** before the first tool call.
- Derive deterministic keys from `(tenant, agent_run_id, step_id, action_type, business_object_id)` when possible.
- On **timeout with unknown outcome**: do **not** free the key and blindly retry — **reconcile** (status lookup) or surface `STATE_UNKNOWN` to the agent/human.
- Use leases for `in_progress` claims so dead workers don’t block forever.
- Separate read tools (naturally idempotent) from write tools (`no_auto_retry` unless keyed).

SRE book on cron: non-idempotent jobs (payroll, newsletter) must avoid double launch; prefer skip over duplicate when unsure:  
https://sre.google/sre-book/distributed-periodic-scheduling/

SRE workbook: idempotent pipeline mutations for safe reprocessing:  
https://sre.google/workbook/data-processing/

### Alternatives & Tradeoffs
| Approach | Protects against | Gaps |
|----------|------------------|------|
| Natural idempotency (`PUT` absolute state) | Many retries | Not all APIs support |
| Idempotency keys | Duplicate submits | Requires server support |
| Outbox + at-least-once with dedupe | Distributed commits | Complexity |
| Human approval for writes | Dup risk ↓ | Latency / ops cost |
| Exactly-once wishful thinking | — | Doesn’t exist across systems |

### Necessity
Without keys: duplicate refunds, double shipments, spammed customers — classic agent demos-gone-wrong. With keys minted inside a retry loop (`uuid4()` each attempt): **false sense of safety**. Caching only “seen key” without response body → retries return inconsistent payloads.

### Industry Practice
**Common:** hope tool APIs are safe; retry 3 times.  
**Strong:** tool registry marks side-effecting tools; mandatory idempotency key arg; broker wraps third parties that lack keys; reconciliation tools; DLQ for failed agent writes; audit log of key → side effect; tests that kill workers mid-flight and assert single execution.

### Concrete Scenario
Stripe Idempotent Requests (canonical API design reference):  
https://docs.stripe.com/api/idempotent_requests  

SRE — cron / non-idempotent launches:  
https://sre.google/sre-book/distributed-periodic-scheduling/

SRE Workbook — idempotent and two-phase mutations:  
https://sre.google/workbook/data-processing/

AWS multi-tenant agent OBO patterns still need idempotent tool backends underneath identity:  
https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/

### Open Questions
- Who owns key namespaces — agent framework, API gateway, or each tool?
- Cross-tool sagas (CRM create + email send): one key or saga log with compensating actions?
- How to teach models via tool schemas to *reuse* keys instead of inventing new ones each thought step?

### Sources
- https://docs.stripe.com/api/idempotent_requests
- https://sre.google/sre-book/distributed-periodic-scheduling/
- https://sre.google/workbook/data-processing/
- https://sre.google/sre-book/automation-at-google/
- https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/

---

## Concept: End-to-end FDE integration playbook (messy enterprise)

### Fundamentals
A realistic Phase-5 engagement stitches Weeks 18–21:

1. Land customer data with tolerant ETL → curated warehouse/views.
2. Enforce tenant + RBAC on every retrieval/tool.
3. Deploy gateway with routing/caching (Week 20) on K8s (Week 18).
4. SSO via OIDC/SAML (Week 19); workload identity to cloud.
5. Agent tools: timeouts, breakers, idempotency keys, degradation copy.
6. Eval + cost dashboards before claiming success.

### Alternatives & Tradeoffs
Big-bang “autonomous agent on prod SQL” vs incremental: start with read-only RAG + vetted tools → add writes behind approval → then limited autonomy.

### Necessity
Skipping any layer (especially authz + idempotency + partial failure) produces demos that cannot survive production traffic or security review.

### Industry Practice
Strong FDEs sequence risk: **data access correctness → reliability → cost** , not the reverse.

### Concrete Scenario
SRE service best practices appendix as a checklist while integrating:  
https://sre.google/sre-book/service-best-practices/

### Open Questions
- What’s the minimum viable “enterprise integration” scope for a 2–4 week FDE embed?
- How to measure integration quality beyond model evals (data freshness SLOs, tool error budgets)?

### Sources
- https://sre.google/sre-book/service-best-practices/
- https://sre.google/workbook/data-processing/
- https://docs.stripe.com/api/idempotent_requests

---

## Week 21 synthesis notes (for later curriculum writing)

- FDE bar: explain bronze/silver/gold ingest; write a tool error taxonomy; design an idempotency key for “create Zendesk ticket”; argue why text-to-SQL needs a semantic layer; sketch behavior when Salesforce is 5s slow / down.
- Closes Phase 5: production deploy + identity + cost + messy reality of customer systems.
