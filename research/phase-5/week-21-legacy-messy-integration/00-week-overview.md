# 00 — Week overview: connect messy SQL/docs; handle timeout, malformed record, partial data

> Week 21 — Legacy & messy integration  
> Research notes (raw). Phase 5 week after cost/latency (Week 20). Next: capstone (Week 22). Do not start interview STAR write-ups from this corpus.

This file is the **design document** for the FDE interview artifact: an agent that **reads a messy warehouse + tribal docs**, survives a **malformed ingest row**, a **timed-out CRM call**, and **partial tool results**, and **never double-fires a ticket**. Concept files 01–04 are the depth; this file is the stitched path.

---

## Fundamentals

Weeks 18–20 shipped **where it runs**, **who may call it**, and **what it costs**. The remaining failure is the customer’s estate: 400-table OLTP with `stat_cd`, a SharePoint dump named `final_FINAL_v7.csv`, Salesforce that 503s on Friday deploys, and an agent that retries `create_ticket` three times.

Week 21 answers four coupled questions:

1. **How does the model get trustworthy facts from messy SQL and messy docs?** File [01](01-messy-sql-integration.md).  
2. **How do we ingest files/webhooks that violate the contract?** File [02](02-tolerant-etl-ingestion.md).  
3. **What happens when *their* system is slow or down?** File [03](03-partial-failure-design.md).  
4. **How do writes stay once-per-intent when the network lies?** File [04](04-idempotency-side-effects.md).

### Design: one request path through messy enterprise

```
user question
    │
    ├─► retrieve data docs (dictionary, example joins, “stat_cd meanings by division”)
    │         miss / stale docs → labeled gap, do not invent columns
    │
    ├─► choose tool
    │         vetted get_invoice(id)  vs  text-to-SQL on approved views only
    │
    ├─► execute with deadline budget
    │         CRM timeout ──► circuit open? → degrade (RAG/cache + caveat) or queue
    │         SQL timeout ──► cancel statement; return SQL_TIMEOUT, do not retry writes
    │         partial rows ──► answer with completeness flag + missing sources
    │
    └─► if write: same idempotency key minted at plan time
              timeout with unknown outcome → reconcile, not new key
```

Google’s SRE book treats real pipelines as **operational systems**: schema evolution, hanging chunks, thundering herds, consistency — not a one-off `cron` script ([Data processing pipelines](https://sre.google/sre-book/data-processing-pipelines/)). Agents inherit that complexity the moment they join OLTP to RAG.

Enterprise Integration Patterns: producers do not share a schema. A **Canonical Data Model** plus translators sit in the middle so each new app pays one mapping, not N×N ([Canonical Data Model](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html)). The FDE semantic layer *is* that model for the LLM.

### Connecting messy SQL and messy docs (same problem)

Messy SQL without docs: the model guesses `cust_id` vs `customer_uuid`.  
Messy docs without SQL: the wiki says “status 3 means cancelled” for Division A; Division B uses 3 for “collections.”

**Joint design:**

| Artifact | Role |
|---------|------|
| Curated views / metrics (dbt, LookML, Cube) | Hide EAV, soft-delete filters, currency units |
| Versioned schema snapshot | `information_schema` + redacted samples in the *tool*, not a 200k-token prompt |
| Data dictionary + example queries in RAG | Retrieved *before* SQL generation; cite the doc chunk |
| Approved join graph | Edges the model may use; everything else is a compile error |
| Tenant + RLS injected by middleware | Never “add `WHERE tenant_id = …` in the prompt and hope” |

Do **not** paste the full ERD. Token cost, confusion, and leakage. Prefer **hybrid tools**: high-risk domains are parameterized functions; exploratory analytics is text-to-SQL on **views**.

### Three failure classes the overview must specify

These are not afterthoughts; they are the default production path.

#### 1. Timeout (customer system slow or hung)

- Every tool has **connect** and **read** deadlines. Infinite default HTTP clients pin workers and take down *your* product ([Fowler: remote calls hang until timeout](https://martinfowler.com/bliki/CircuitBreaker.html)).  
- Agent run has a **total deadline**; remaining time is propagated to nested RPCs (SRE: missed deadlines waste work; clients retry and amplify load — [Addressing cascading failures](https://sre.google/sre-book/addressing-cascading-failures/)).  
- After N failures, Fowler **open** circuit: fail fast with `CRM_CIRCUIT_OPEN`, do not wait 30s × retries. Half-open probe after `reset_timeout`.  
- UX: structured error in the observation channel (`CRM_TIMEOUT`, remaining budget). Generic “something went wrong” causes the model to retry the same POST.  
- If the timed-out call was a **write**, treat outcome as **unknown** (file 04), not as “safe to retry with a new key.”

#### 2. Malformed record (ingest)

- File drop / webhook / “CSV from finance” will have Windows-1252 labeled UTF-8, extra columns, `"NULL"` strings, truncated JSON.  
- **Land raw first** (immutable bytes + checksum + `received_at`). Parser bugs are then replayable ([SRE workbook: reprocessing](https://sre.google/workbook/data-processing/)).  
- Validate against an explicit contract (JSON Schema, Great Expectations, pydantic). **Quarantine the row**, do not fail the whole job because one line is missing `invoice_id`.  
- Beam/Dataflow: `WriteResult` / `FailedRows` / `getFailedInsertsWithErr` → dead-letter table ([Beam BigQueryIO deadletter](https://beam.apache.org/documentation/patterns/bigqueryio/)).  
- Never silently `parseInt` → `0`. Wrong numbers in RAG look authoritative.  
- LLM “cleaning” belongs in **staging suggestions**, not silent writes to gold.

SRE service best practices: validate syntax *and* semantics; watch for **empty and truncated** configs; continue on last-known-good rather than serving `NXDOMAIN` for the whole web ([Fail sanely](https://sre.google/sre-book/service-best-practices/)). Same instinct for pipeline config and for “empty dictionary file” that would teach the agent there are zero tables.

#### 3. Partial data (incomplete batch, missing tool, degraded corpus)

Partial is **success with holes**, not a 500.

| Source of partial | Product behavior |
|------------------|------------------|
| 5% of bronze rows in DLQ | Gold index updates incrementally; UI/agent says “N invoices not yet searchable”; quarantine SLO owned |
| Salesforce 503; billing API OK | Answer billing facts; label CRM enrichment skipped; optional async resume (Week 13 checkpointers) |
| Text-to-SQL `LIMIT` / timeout mid-scan | Return rows gathered + `truncated=true`; do not invent the rest |
| Soft-delete / replica lag | Document freshness SLO; do not treat replica as SoR for writes |
| Docs RAG miss | “No dictionary hit for `CUST_XREF_V3`” — refuse to join that table |

SRE: Search **degrades** (smaller index, drop Instant) rather than dying ([Handling overload](https://sre.google/sre-book/handling-overload/); [Service best practices](https://sre.google/sre-book/service-best-practices/)). Agent analog: answer from last good RAG snapshot with **caveat**, skip live enrichment, queue the write.

Workbook **data isolation**: under resource crunch, process high-priority tenants/rows first ([Data isolation/load balancing](https://sre.google/workbook/data-processing/)). FDE: P0 customer corpus before bulk historical PDF backfill.

### End-to-end FDE playbook (Weeks 18–21 stitch)

1. Tolerant ETL → curated warehouse/views (this week 02 + 01).  
2. Tenant + RBAC on every retrieval/tool (Week 19).  
3. Gateway routing/caching (Week 20) on K8s (Week 18).  
4. SSO OIDC/SAML; workload identity to cloud (Week 19).  
5. Agent tools: timeouts, breakers, idempotency keys, degradation copy (03 + 04).  
6. Eval + cost dashboards before claiming success (Weeks 16–17, 20).

Sequence risk as **data access correctness → reliability → cost**, not the reverse. Big-bang “autonomous agent on prod SQL” fails security review. Incremental: read-only RAG + vetted tools → writes behind approval → limited autonomy.

### Mapping to adjacent weeks

| This week | Not this week |
|-----------|----------------|
| Semantic layer, text-to-SQL safety, messy docs RAG | Chunking/rerank theory (Weeks 6–8) — still **use** those indexes |
| Bronze/silver/gold, DLQ, contracts | Prompt/cache economics (Week 20) except “don’t cache mutating tool results” |
| Customer CRM timeout / breaker | K8s HPA (Week 18) — still bulkhead *thread pools* per dependency |
| Stripe-style keys on agent writes | HITL/dry-run envelope depth (Week 14) — **reuse**, don’t rewrite |
| Partial answers labeled | Capstone narrative (Week 22) |

---

## Alternatives & Tradeoffs

| Approach | Accuracy | Safety | Ops load |
|----------|----------|--------|----------|
| **Semantic views + docs RAG + vetted write tools + per-row ETL + breakers + keyed writes** | High when catalog is current | High | Medium-high (catalog + DLQ + breaker dashboards) |
| Open text-to-SQL on OLTP, fail-fast ETL, no timeouts | Fragile | Dangerous | Low until the first incident |
| Warehouse copy then AI only | Cleaner SQL | Lag; ETL cost | Warehouse team |
| Hand-built tools only | Highest | Highest | Does not scale to 200 questions |
| Schema-on-read into vectors | Fast to demo | Garbage in answers | Hidden |
| Fail closed on any missing tool | Safe | Empty UX during SaaS blips | Support tickets |
| Serve stale always | Fast | May be wrong | Must label |

EIP note: Canonical Data Model costs **more translators at N=2** and **fewer at N=6** ([pattern page](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html)). FDE: one canonical “Customer / Invoice / Ticket” beats pairwise CRM↔ERP↔agent mappings.

---

## Necessity

Pointing an agent at raw prod without RLS → breach or accidental `UPDATE`. Ignoring soft deletes → “customers that don’t exist.” Dual currency/timezone → wrong money and lost trust.

Brittle ETL that aborts on the first bad row → empty RAG and perpetual firefighting. Silent coercion → authoritative wrong answers. No raw landing → cannot replay after a parser fix. No DLQ → poison pill stalls streaming.

A hung CRM without timeouts pins all workers → **your** outage in the customer’s eyes. Blind retries of POSTs → duplicate tickets (file 04). No structured errors → the LLM burns tokens retrying.

Skipping authz + idempotency + partial failure produces demos that cannot survive production or security review.

---

## Industry Practice

**Common:** dump schema into the system prompt; shared DBA login; cron `ON ERROR FAIL`; default HTTP client timeout (or none); `uuid4()` inside the retry loop.

**Strong:**

- Curated semantic layer; eval set NL→SQL with **execution** accuracy; shadow mode (generate SQL, don’t run); human approve for writes; column masking; tenant predicates in middleware; schema snapshot versioning.  
- Medallion architecture; contract monitoring; pipeline canaries + two-phase mutations; data SLOs (freshness, completeness); quarantine dashboards; schema registry; PII detection before vectors.  
- Per-dependency SLOs; chaos latency injection; tool error taxonomy; “degraded mode” product copy; queue depth alerts.  
- Tool registry marks side-effecting tools; mandatory idempotency key; broker in front of APIs that lack keys; reconciliation tools; tests that kill workers mid-flight.

---

## Concrete Scenario

**Whiteboard story (use in interview):**

Finance drops `invoices_2026_09.csv` (Windows-1252, extra column `amt2`, one truncated row). Bronze lands the bytes. Validator quarantines 12 rows to DLQ; 10,000 load to silver with idempotent upsert on `invoice_natural_key`. Gold vector index updates; UI shows “12 invoices in quarantine.”

User asks: “What’s open AR for Acme?” Agent retrieves the dictionary (`amt` is cents; `stat_cd=3` is open **in US**, paid **in EU**). Text-to-SQL hits `vw_ar_open` (already filtered `deleted_at IS NULL`) with `LIMIT` and 5s statement timeout. Salesforce `get_account` times out at 2s; breaker still closed (1/5). Answer uses warehouse AR, labels “CRM account owner not refreshed.” User says “file a ticket.” Tool uses key `tenant|run|step|zendesk.create|acme-id`. First HTTP times out after Zendesk accepted the POST. Reconcile by external id / key lookup; retry **same key** returns stored 201. No second ticket.

Cites for the story:

- Pipelines and reprocessing: [SRE Ch. 25](https://sre.google/sre-book/data-processing-pipelines/), [Workbook Ch. 13](https://sre.google/workbook/data-processing/)  
- Dead-letter inserts: [Beam BigQueryIO](https://beam.apache.org/documentation/patterns/bigqueryio/)  
- Timeouts / breakers: [Fowler](https://martinfowler.com/bliki/CircuitBreaker.html), [EIP retry](https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html)  
- Keys: [Stripe](https://docs.stripe.com/api/idempotent_requests)  
- Conference flavor: [Strange Loop](https://www.youtube.com/@StrangeLoopConf), [CNCF](https://www.youtube.com/@cncf)

---

## Open Questions

- When is it cheaper to **fix the semantic layer** than to push harder on agent reasoning?  
- Minimum viable “enterprise integration” for a 2–4 week FDE embed?  
- How to measure integration quality beyond model evals (freshness SLOs, tool error budgets, quarantine age)?  
- Multi-agent **shared** vs **per-replica** circuit-breaker state?  
- Vector index: rebuild vs incremental when 5% of source rows are quarantined?  
- Who owns quarantine SLAs — data eng or the FDE embedding the corpus?

---

## Sources

- https://sre.google/sre-book/data-processing-pipelines/  
- https://sre.google/workbook/data-processing/  
- https://sre.google/sre-book/handling-overload/  
- https://sre.google/sre-book/addressing-cascading-failures/  
- https://sre.google/sre-book/service-best-practices/  
- https://sre.google/sre-book/distributed-periodic-scheduling/  
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html  
- https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html  
- https://martinfowler.com/bliki/CircuitBreaker.html  
- https://docs.stripe.com/api/idempotent_requests  
- https://beam.apache.org/documentation/patterns/bigqueryio/  
- https://www.youtube.com/@StrangeLoopConf  
- https://www.youtube.com/@cncf  
