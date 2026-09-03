# 99 — Week 21 master source map

> Consolidated index of Google SRE book/workbook, Enterprise Integration Patterns, Stripe idempotency, Martin Fowler Circuit Breaker, AWS Agentic AI / Durable Execution, GCP Dataflow / Apache Beam, dbt, YouTube. Legal sources only; no pirate book sites, no unauthorized course PDFs.

**Deep-pass date:** 2026-09-03. Re-fetch before shipping a lecture — Stripe key retention, Dataflow write APIs, AWS Lens BP ids, and dbt model docs move.

**Not used:** pirate “enterprise integration” PDFs, libgen, pdfcoffee, leaked Udemy/Maven decks, unauthorized copies of *Release It* or *EIP* book text. Official **sre.google** chapters, **enterpriseintegrationpatterns.com** pattern pages, **martinfowler.com** bliki, vendor **docs**, public **YouTube** only.

---

## Google SRE book

| Topic | URL |
|-------|-----|
| Data processing pipelines (Ch. 25) — hanging chunks, thundering herd, Workflow leases | https://sre.google/sre-book/data-processing-pipelines/ |
| Handling overload — degraded Search, adaptive throttling, per-customer limits | https://sre.google/sre-book/handling-overload/ |
| Addressing cascading failures — jitter, retry budgets, queues, deadline propagation | https://sre.google/sre-book/addressing-cascading-failures/ |
| Service best practices (App. B) — fail sanely, empty/truncated config, degrade, retries | https://sre.google/sre-book/service-best-practices/ |
| Distributed periodic scheduling (cron) — skip vs double-launch, idempotency | https://sre.google/sre-book/distributed-periodic-scheduling/ |
| Automation at Google | https://sre.google/sre-book/automation-at-google/ |

---

## Google SRE workbook

| Topic | URL |
|-------|-----|
| Data processing pipelines (Ch. 13) — SLOs, canaries, idempotent & two-phase mutations, quarantine | https://sre.google/workbook/data-processing/ |

---

## Enterprise Integration Patterns

| Topic | URL |
|-------|-----|
| Canonical Data Model | https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html |
| Message Translator | https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageTranslator.html |
| Dead Letter Channel | https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html |
| Idempotent Receiver | https://www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html |
| Request-Response with Retry (backoff, max retries, circuit breakers) | https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html |
| Loan broker / EventBridge circuit-breaker style (EIP ramblings) | https://www.enterpriseintegrationpatterns.com/ramblings/loanbroker_cdk.html |

---

## Circuit breaker (Fowler)

| Topic | URL |
|-------|-----|
| Circuit Breaker bliki (closed / open / half-open, timeouts, pools, stale fallback) | https://martinfowler.com/bliki/CircuitBreaker.html |

---

## Stripe

| Topic | URL |
|-------|-----|
| Idempotent requests (`Idempotency-Key`, 24h, 500 cached, POST vs GET/DELETE) | https://docs.stripe.com/api/idempotent_requests |

---

## AWS (agentic + durable execution)

| Topic | URL |
|-------|-----|
| AGENTREL06-BP04 idempotent task execution | https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentrel06-bp04.html |
| Durable Execution: idempotency and retries (at-least-once vs at-most-once, key inside step) | https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/ |
| Pool-model multi-tenancy (AgentCore) | https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/ |
| OBO token exchange for multi-tenant agents | https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/ |

---

## Ingest / warehouse / semantic layer

| Topic | URL |
|-------|-----|
| Dataflow write to BigQuery (failed inserts / DLQ) | https://docs.cloud.google.com/dataflow/docs/guides/write-to-bigquery |
| Beam BigQueryIO deadletter pattern | https://beam.apache.org/documentation/patterns/bigqueryio/ |
| Pub/Sub to BigQuery template (`outputDeadletterTable`) | https://docs.cloud.google.com/dataflow/docs/guides/templates/provided/pubsub-subscription-to-bigquery |
| Dataflow streaming pipeline upgrade / schema evolution | https://cloud.google.com/dataflow/docs/guides/upgrade-guide |
| dbt models | https://docs.getdbt.com/docs/build/models |

---

## YouTube (public talks / channels)

| Topic | URL |
|-------|-----|
| Idempotent data pipelines (educational talk) | https://www.youtube.com/watch?v=GcU2vxYrA3g |
| Strange Loop — legacy / production systems | https://www.youtube.com/@StrangeLoopConf |
| CNCF / KubeCon — resilience, chaos | https://www.youtube.com/@cncf |

---

## Citation snippet (curriculum later)

```
Beyer et al., Site Reliability Engineering (O'Reilly) — Ch. 22 cascading failures; Ch. 25 data processing pipelines; App. B service best practices; distributed cron. Public: sre.google.
Beyer et al., The Site Reliability Workbook — Ch. 13 data processing pipelines (canary, idempotent/two-phase mutations). Public: sre.google/workbook.
Hohpe & Woolf, Enterprise Integration Patterns — Canonical Data Model; Request-Response with Retry; Dead Letter Channel; Idempotent Receiver. Public pattern pages: enterpriseintegrationpatterns.com.
Fowler, M. (2014). Circuit Breaker. https://martinfowler.com/bliki/CircuitBreaker.html
Stripe Docs. Idempotent requests. https://docs.stripe.com/api/idempotent_requests
AWS Well-Architected Agentic AI Lens. AGENTREL06-BP04.
Apache Beam. BigQueryIO deadletter pattern.
```
