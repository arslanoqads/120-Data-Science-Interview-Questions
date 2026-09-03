# Week 21 Textbook Chapter — Legacy and messy integration

> **Status:** COMPLETE  
> **Source:** `research/phase-5/week-21-legacy-messy-integration/`  
> **Chapter:** [chapter.md](chapter.md)

## Concepts covered

- [x] Messy SQL integration (semantic layer, text-to-SQL, docs RAG)
- [x] Tolerant ETL ingestion (bronze, contracts, quarantine/DLQ)
- [x] Partial failure design (timeouts, bulkheads, circuit breakers)
- [x] Idempotency for agent side effects (Stripe keys, unknown outcome)

## Structure check

Each concept includes Fundamentals, The Alternatives, Failure Modes, Average vs. Strong Engineer, Worked Example, and Apply It.

## Syllabus build

You already have a **containerized, OIDC-gated, cost-attributed LLM service** (Weeks 18–20). This week you **point it at the customer’s actual data and APIs**. (1) **Do not let the model see the raw ERD.** Curate views / metrics (dbt, LookML, Cube) and a join graph. Ground SQL on filtered `information_schema` + redacted samples. RAG over data dictionaries *before* generating SQL. Prefer parameterized tools (`get_invoice(id)`) for money and PII. (2) **Land bytes before you parse.** Immutable bronze + checksum. Validate with a contract. Quarantine malformed rows; do not abort the batch on the first bad CSV cell. Upsert on business keys so retries do not duplicate. (3) **Assume every customer SaaS is down or 5s slow.** Timeouts on every tool; bulkhead pools; Fowler circuit breaker; degrade with a labeled caveat or queue for later. Never retry non-idempotent POSTs blindly. (4) **Mint idempotency keys at plan time** from `(tenant, run_id, step_id, action, object_id)`. Forward Stripe-style keys to write APIs. On timeout, **look up status**, do not free the key.

Interview artifact = **semantic-layer sketch + one vetted SQL tool** + **ETL contract (good row / quarantine / DLQ)** + **dependency timeout/breaker table** + **idempotency key for “create Zendesk ticket”** including the unknown-outcome path.
