# Week 21 Research Corpus — Legacy & messy integration

> Phase 5 — Production, Cost, and Systems  
> **Status:** COMPLETE (deep pass)  
> Raw research corpus (not textbook). Legal/public sources only (Google SRE book + workbook, Enterprise Integration Patterns, Stripe idempotency docs, Martin Fowler Circuit Breaker, AWS Agentic AI Lens / Durable Execution, GCP Dataflow / Apache Beam, dbt, YouTube conference talks). **No pirate PDFs, no libgen/pdfcoffee, no unauthorized course decks.**

This directory is the Week 21 research repository. Read concept files in order, then the source map. **Do not start Week 22 (capstone) from this corpus** — this week ships **messy SQL / semantic layers**, **tolerant ETL**, **partial-failure design**, and **idempotent agent side effects**. Weeks 18–20 already isolated tenants, deployed the gateway, and attributed spend; this week is the customer’s **real systems of record**.

| # | File | Concept |
|---|------|---------|
| 00 | [00-week-overview.md](00-week-overview.md) | Connect messy SQL + docs; handle timeout, malformed record, partial data |
| 01 | [01-messy-sql-integration.md](01-messy-sql-integration.md) | Semantic layer, text-to-SQL allowlists, RAG over data dictionaries |
| 02 | [02-tolerant-etl-ingestion.md](02-tolerant-etl-ingestion.md) | Bronze/raw land, contracts, quarantine/DLQ, idempotent upserts |
| 03 | [03-partial-failure-design.md](03-partial-failure-design.md) | Timeouts, bulkheads, Fowler circuit breakers, SRE degradation |
| 04 | [04-idempotency-side-effects.md](04-idempotency-side-effects.md) | Stripe keys, deterministic agent keys, unknown-outcome reconcile |
| — | [99-source-map.md](99-source-map.md) | Master URL / SRE / EIP / Stripe / Fowler / YouTube index |

## Completeness checklist (Week 21)

- [x] All syllabus Week 21 concepts covered with **7 required fields**  
- [x] **Connect to messy SQL and messy docs** as a single FDE problem (overview + file 01)  
- [x] **Timeout**, **malformed record**, and **partial data** handled as first-class cases (overview)  
- [x] Semantic layer before open text-to-SQL; allowlists, RLS, statement timeouts, `LIMIT`  
- [x] EIP Canonical Data Model / Message Translator between producer schemas and agents  
- [x] Google SRE pipelines: hanging chunks, thundering herd, freshness/correctness SLOs  
- [x] SRE workbook: canary pipelines, **idempotent mutations**, **two-phase mutations**, quarantine of bad work units  
- [x] Medallion land-raw → validate → normalize → publish; DLQ + replay  
- [x] Dataflow / Beam `WriteResult` / `FailedRows` dead-letter pattern  
- [x] Fail-fast whole job vs per-row quarantine vs schema-on-read vs LLM “fix”  
- [x] Partial failure: connect + read timeouts, bulkheads, Fowler **closed / open / half-open**  
- [x] EIP Request-Response with Retry: max retries, exponential backoff, circuit breakers  
- [x] SRE: degraded Search, retry storms, jitter, retry budgets, deadline propagation  
- [x] Stripe `Idempotency-Key`: store status+body (incl. 500), 24h prune, param mismatch, POST only  
- [x] AWS AGENTREL06-BP04: deterministic keys (not UUID-at-retry), propagate, conditional writes  
- [x] Timeout with **unknown outcome** → reconcile / `STATE_UNKNOWN`, do not mint a new key  
- [x] YouTube: Strange Loop, CNCF/KubeCon, idempotent-pipeline talk  
- [x] Per-week research **directory** (not a single thin file)  
- [x] `_PRIOR_SINGLE_FILE.md` removed after expansion  

## Syllabus build task (Week 21)

You already have a **containerized, OIDC-gated, cost-attributed LLM service** (Weeks 18–20). This week you **point it at the customer’s actual data and APIs**.

1. **Do not let the model see the raw ERD.** Curate views / metrics (dbt, LookML, Cube) and a join graph. Ground SQL on filtered `information_schema` + redacted samples. RAG over data dictionaries *before* generating SQL. Prefer parameterized tools (`get_invoice(id)`) for money and PII.  
2. **Land bytes before you parse.** Immutable bronze + checksum. Validate with a contract. Quarantine malformed rows; do not abort the batch on the first bad CSV cell. Upsert on business keys so retries do not duplicate.  
3. **Assume every customer SaaS is down or 5s slow.** Timeouts on every tool; bulkhead pools; Fowler circuit breaker; degrade with a labeled caveat or queue for later. Never retry non-idempotent POSTs blindly.  
4. **Mint idempotency keys at plan time** from `(tenant, run_id, step_id, action, object_id)`. Forward Stripe-style keys to write APIs. On timeout, **look up status**, do not free the key.

Interview artifact = **semantic-layer sketch + one vetted SQL tool** + **ETL contract (good row / quarantine / DLQ)** + **dependency timeout/breaker table** + **idempotency key for “create Zendesk ticket”** including the unknown-outcome path.

## Default path (synthesis)

1. **Translate before reason.** Canonical model between messy producers and the agent ([EIP Canonical Data Model](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html)).  
2. **Pipelines accumulate operational complexity** far past `SELECT *` ([SRE data processing pipelines](https://sre.google/sre-book/data-processing-pipelines/)).  
3. **Idempotent + two-phase mutations** make reprocessing and canaries safe ([SRE workbook](https://sre.google/workbook/data-processing/)).  
4. **Open circuit is cheaper than waiting on a dead CRM** ([Fowler Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html); [SRE cascading failures](https://sre.google/sre-book/addressing-cascading-failures/)).  
5. **Same key + stored response**, including 500s; 24h retention as a lower bound ([Stripe](https://docs.stripe.com/api/idempotent_requests)).  
6. **Skip duplicate cron launches** when unsure; payroll is not GC ([SRE distributed cron](https://sre.google/sre-book/distributed-periodic-scheduling/)).  
