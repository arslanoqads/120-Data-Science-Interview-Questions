# 02 — Tolerant ETL / ingestion (malformed and inconsistent input)

> Week 21 — Ingestion that assumes the contract is a rumor.  
> Research notes (raw). Semantic serving of the result is file [01](01-messy-sql-integration.md). Idempotent **agent writes** are file [04](04-idempotency-side-effects.md); this file is **pipeline** idempotency.

---

## Fundamentals

Customer file drops, webhook payloads, and “CSV from finance” violate contracts. Production ingestion must assume:

- Wrong encodings (Windows-1252 labeled as UTF-8)  
- Extra/missing columns; reordered headers  
- Duplicate primary keys; late-arriving updates  
- Null vs empty vs `"NULL"` string  
- Partially truncated JSON; trailing commas  
- Schema drift without notice  

**Tolerant ETL design (medallion-shaped):**

1. **Land raw first (bronze)** — immutable bytes + metadata (`source`, `received_at`, checksum, producer version if any). Replay is impossible without this.  
2. **Validate** with explicit contracts (JSON Schema, Great Expectations, pydantic) → **quarantine** bad records; do not fail the whole batch blindly.  
3. **Normalize** to a typed canonical model (silver) — this is EIP’s translator into the Canonical Data Model ([CDM](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html)).  
4. **Publish** to serving stores / vector indexes (gold) with versions.  
5. **Dead-letter + replay**; metrics on quarantine **rate** and **age**.  
6. **Idempotent upserts** on business keys so retries don’t duplicate.

For LLM corpora: PDF/HTML extraction fails often — keep parent document id, chunk checksums, and allow **partial** corpus updates (overview: partial data).

### What SRE actually says about pipelines

**Book (Ch. 25):** periodic pipelines are **fragile** under organic growth: jobs exceed deadlines, hanging chunks, kill-and-restart **without checkpoints** discards all chunk work; monitoring that only emits on completion hides in-flight failure; **thundering herd** when thousands of workers start together; naive retries compound load; **Moiré** overlap of two pipelines on a shared store ([pipelines](https://sre.google/sre-book/data-processing-pipelines/)). Google Workflow’s answer: leases, unique output names, task versioning, server tokens — **exactly-once-shaped** commits, not “hope the CSV load is unique.”

**Workbook (Ch. 13):** pipelines are business-critical; delayed or incorrect data is expensive. Best practices:

- **SLOs:** freshness (`X% in Y minutes` / oldest data / job completed within Y); **correctness** (golden accounts, invoice error rate); **end-to-end** not per-stage (a stage can “succeed” while dropping a field the next stage ignores).  
- **Plan for dependency failure**; DiRT-style regional outages; don’t overwrite good data with stale during failover.  
- **Canary pipelines:** process real data but **skip production writes**, or use **two-phase mutation** (buffer mutations, verify, then apply). Rolling 1% of *data* when you cannot canary a region (Dataflow/Dataproc).  
- **Idempotent mutations:** same input → same stored result under reprocessing.  
- **Two-phase mutations:** store proposed mutations, validate, apply — so a canary cannot corrupt the store.  
- Feature table: **automatic quarantine of bad work units** and **replay** as the mature bar vs “no support for failed work units” ([workbook](https://sre.google/workbook/data-processing/)).

**Fail sanely (SRE appendix):** empty/truncated config should not replace last-known-good (2005 DNS empty file → six minutes of `NXDOMAIN`; 2009 malware list `/` matching the entire web) ([service best practices](https://sre.google/sre-book/service-best-practices/)). FDE: an empty dictionary or 0-byte CSV must **alert** and keep the previous gold index, not wipe embeddings.

### Cloud-native DLQ (legal vendor docs)

- Dataflow → BigQuery: failed Storage Write API / streaming inserts via `WriteResult` (`getFailedStorageApiInserts` / failed rows) routed to a dead-letter table ([Write to BigQuery](https://docs.cloud.google.com/dataflow/docs/guides/write-to-bigquery)).  
- Beam `BigQueryIO` **deadletter pattern**: `WriteResult` + `withExtendedErrorInfo` + `getFailedInsertsWithErr` / `FailedRows`; `InsertRetryPolicy.retryTransientErrors()` — **invalid** rows (null in REQUIRED) go to DLQ, transients retry ([pattern](https://beam.apache.org/documentation/patterns/bigqueryio/)).  
- Pub/Sub → BigQuery template: `outputDeadletterTable` for transform/UDF failures ([template](https://docs.cloud.google.com/dataflow/docs/guides/templates/provided/pubsub-subscription-to-bigquery)).  
- Incompatible schema evolution: façade views / staging tables ([upgrade streaming pipeline](https://cloud.google.com/dataflow/docs/guides/upgrade-guide)).

EIP **Dead Letter Channel**: messages that cannot be processed go to a dedicated channel rather than blocking the pipe ([Dead Letter Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html)).

**LLM-specific:** do not use a model to silently “fix” types into production. Use it for **suggested mappings** in a staging UI with tests. Extraction failures keep parent id so gold can update 95% of chunks.

**Vector index when 5% quarantined:** incremental upsert of successful keys; do not full-rebuild unless the parser change is global. Surface completeness: `indexed_frac = 0.95`. Rebuild when quarantine is drained or schema of embeddings changed.

---

## Alternatives & Tradeoffs

| Strategy | Pros | Cons |
|----------|------|------|
| Fail-fast entire job | Simple | One bad row blocks business |
| Per-row quarantine + DLQ | Resilient | Operational load to fix DLQ |
| Schema-on-read | Flexible | Garbage reaches consumers / RAG |
| Contract tests with producers | Prevents issues | Needs org power |
| LLM to “fix” rows | Tempting | Quietly invents fields — dangerous |
| Two-phase mutation canary | Safe deploys | Latency; extra storage |
| Exactly-once engine (Workflow-like) | Strong correctness | Heavy; still need business keys at the edges |

Use LLMs for **suggestions** on messy mappings in staging; do not silently auto-write production mappings without tests.

**Idempotent upsert vs append-only:** upsert on natural key handles late-arriving corrections; append-only + deterministic event id is the log-shaped alternative (AWS durable execution: append events, readers dedupe — [idempotency](https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/)).

---

## Necessity

Brittle ETL that aborts on first bad row → perpetual firefighting and **empty RAG indexes**. Silent coercion (`parseInt` → 0) → wrong AI answers that look authoritative. Without raw landing → cannot replay after fixing parsers. Without DLQ → poison pills halt streaming forever.

Without idempotent mutations → every retry/reprocess duplicates customers in the index. Without two-phase / dry-run canaries → a bad dbt model or chunker ships to 100% of tenants (Week 18 digest promotion applied to **data**).

Without freshness/correctness SLOs → “the agent is wrong” tickets that are actually a stuck pipeline (workbook: Dressy recommendations stale 24h — stuck preprocess vs bad model vs stale binary).

---

## Industry Practice

**Common:** cron script + `ON ERROR FAIL`; load to prod table in one shot; no checksum; DLQ is a folder named `bad/` that nobody reads.

**Strong:**

- Medallion; contract monitoring; schema registry for events.  
- Canary on pipeline **code** (dry-run writes) and on **data %**.  
- Idempotent upserts; data SLOs on dashboards next to LLM evals.  
- Quarantine dashboards with owner and age SLO.  
- PII detection on ingest **before** vectors (Week 19 residency).  
- Replay runbooks; unique output names / partition dates so orphans cannot clobber (SRE Workflow lesson).  
- Isolation: high-priority tenants processed first under crunch (workbook).  
- Encoding detection as a first-class step; never trust the filename `.utf8.csv`.

---

## Concrete Scenario

**GCP Dataflow:** capture Storage Write API / streaming insert failures into a dead-letter path instead of failing the job — [write to BigQuery](https://docs.cloud.google.com/dataflow/docs/guides/write-to-bigquery).

**Apache Beam** dead-letter sample (REQUIRED field null → `FailedRows` / `getFailedInsertsWithErr`) — [BigQueryIO patterns](https://beam.apache.org/documentation/patterns/bigqueryio/).

**SRE workbook:** canarying pipelines, idempotent and two-phase mutations, quarantine of bad work units — [Improve and optimize data processing pipelines](https://sre.google/workbook/data-processing/).

**SRE book:** hanging chunks, thundering herd, Workflow leases — [Managing data processing pipelines](https://sre.google/sre-book/data-processing-pipelines/).

**Periodic jobs:** don’t stack overlapping runs; don’t kill nearly-finished work because the next cron fired — [Distributed periodic scheduling](https://sre.google/sre-book/distributed-periodic-scheduling/).

**Talk:** educational walkthrough of idempotent data pipelines — [YouTube `GcU2vxYrA3g`](https://www.youtube.com/watch?v=GcU2vxYrA3g). Strange Loop for legacy/pipeline reliability — [channel](https://www.youtube.com/@StrangeLoopConf).

---

## Open Questions

- How much “LLM data cleaning” is acceptable before audit/compliance says no?  
- Vector index: rebuild vs incremental when 5% of source rows were quarantined?  
- Who owns quarantine SLAs — data eng or the FDE embedding the corpus?  
- When does schema-on-read for RAG become an SLO violation vs a feature?

---

## Sources

- https://docs.cloud.google.com/dataflow/docs/guides/write-to-bigquery  
- https://beam.apache.org/documentation/patterns/bigqueryio/  
- https://docs.cloud.google.com/dataflow/docs/guides/templates/provided/pubsub-subscription-to-bigquery  
- https://cloud.google.com/dataflow/docs/guides/upgrade-guide  
- https://sre.google/workbook/data-processing/  
- https://sre.google/sre-book/data-processing-pipelines/  
- https://sre.google/sre-book/distributed-periodic-scheduling/  
- https://sre.google/sre-book/service-best-practices/  
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html  
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html  
- https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/  
- https://www.youtube.com/watch?v=GcU2vxYrA3g  
- https://www.youtube.com/@StrangeLoopConf  
