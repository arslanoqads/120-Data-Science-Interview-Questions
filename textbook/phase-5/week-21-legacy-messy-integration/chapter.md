# Chapter 21 — Legacy and messy integration

> **Phase 5 — Production, Cost, and Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-5/week-21-legacy-messy-integration/`  
> **Syllabus Build:** You already have a **containerized, OIDC-gated, cost-attributed LLM service** (Weeks 18–20). This week you **point it at the customer’s actual data and APIs**. (1) **Do not let the model see the raw ERD.** Curate views / metrics (dbt, LookML, Cube) and a join graph. Ground SQL on filtered `information_schema` + redacted samples. RAG over data dictionaries *before* generating SQL. Prefer parameterized tools (`get_invoice(id)`) for money and PII. (2) **Land bytes before you parse.** Immutable bronze + checksum. Validate with a contract. Quarantine malformed rows; do not abort the batch on the first bad CSV cell. Upsert on business keys so retries do not duplicate. (3) **Assume every customer SaaS is down or 5s slow.** Timeouts on every tool; bulkhead pools; Fowler circuit breaker; degrade with a labeled caveat or queue for later. Never retry non-idempotent POSTs blindly. (4) **Mint idempotency keys at plan time** from `(tenant, run_id, step_id, action, object_id)`. Forward Stripe-style keys to write APIs. On timeout, **look up status**, do not free the key.

---

## Chapter framing

Week 21 is the **customer systems of record** week of Phase 5. Weeks 18–20 shipped **where it runs**, **who may call it**, and **what it costs**. The remaining failure is the customer’s estate: a 400-table OLTP with `stat_cd`, a SharePoint dump named `final_FINAL_v7.csv`, Salesforce that 503s on Friday deploys, and an agent that retries `create_ticket` three times.

This week answers four coupled questions that FDE embeds, security reviews, and interview whiteboards treat as the minimum bar for an agent that touches real enterprise data:

1. **How does the model get trustworthy facts from messy SQL and messy docs?** (semantic layer, text-to-SQL allowlists, dictionary RAG)  
2. **How do we ingest files/webhooks that violate the contract?** (bronze land, quarantine/DLQ, idempotent upserts)  
3. **What happens when *their* system is slow or down?** (timeouts, bulkheads, Fowler breakers, labeled degradation)  
4. **How do writes stay once-per-intent when the network lies?** (Stripe-style keys, deterministic agent keys, unknown-outcome reconcile)

**Do not start Week 22 (capstone) from this chapter** — this week ships **messy SQL / semantic layers**, **tolerant ETL**, **partial-failure design**, and **idempotent agent side effects**. Weeks 18–20 already isolated tenants, deployed the gateway, and attributed spend; honor tenant/RLS inside SQL tools and do not cache mutating tool results (Week 20). Chunking/rerank theory (Weeks 6–8) is still *used* for dictionary indexes. HITL/dry-run envelopes (Week 14) are *reused* for write approval—do not rewrite them.

**Design: one request path through messy enterprise**

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

Messy SQL and messy docs are the **same surface**. Without docs the model guesses `cust_id` vs `customer_uuid`; without SQL the wiki’s “status 3 means cancelled” for Division A collides with Division B’s “collections.” Joint design: curated views/metrics, versioned schema snapshot in the *tool*, dictionary + example queries in RAG before SQL, approved join graph, tenant + RLS injected by middleware—never “add `WHERE tenant_id = …` in the prompt and hope.”

Three failure classes are the **default production path**, not afterthoughts: **timeout** (customer system slow/hung), **malformed record** (ingest), **partial data** (incomplete batch, missing tool, degraded corpus). Partial is **success with holes**, not a 500.

**Default path (synthesis)**

1. **Translate before reason.** Canonical model between messy producers and the agent (EIP Canonical Data Model).  
2. **Pipelines accumulate operational complexity** far past `SELECT *` (Google SRE data-processing pipelines).  
3. **Idempotent + two-phase mutations** make reprocessing and canaries safe (SRE workbook).  
4. **Open circuit is cheaper than waiting on a dead CRM** (Fowler Circuit Breaker; SRE cascading failures).  
5. **Same key + stored response**, including 500s; 24h retention as a lower bound (Stripe).  
6. **Skip duplicate cron launches** when unsure; payroll is not GC (SRE distributed cron).

Interview artifact = **semantic-layer sketch + one vetted SQL tool** + **ETL contract (good row / quarantine / DLQ)** + **dependency timeout/breaker table** + **idempotency key for “create Zendesk ticket”** including the unknown-outcome path.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) after Weeks 18–20 — now pointed at the customer’s warehouse, file drops, and SaaS APIs.

---

### Messy SQL integration (semantic layer, text-to-SQL, docs RAG)

* **Fundamentals:**  
  Enterprise data is rarely warehouse-clean. FDE work means connecting agents/RAG to **production schemas** with cryptic names (`CUST_XREF_V3`, `stat_cd`), overloaded columns (status `1/2/3` meaning different things **per division**), soft deletes applied inconsistently, multiple sources of truth (CRM vs billing vs spreadsheet exports), sparse documentation and tribal Slack knowledge, PII in free-text notes, timezone-naive timestamps, currency in cents vs dollars, and polymorphic FKs / EAV tables.

  **Messy docs are part of the same surface.** A data dictionary that is three years stale is more dangerous than no dictionary: the model will cite it. Treat docs as **versioned artifacts** ingested with the same bronze/silver discipline as CSV: source, `as_of`, owner, checksum.

  Five integration patterns that work:

  1. **Semantic layer first** — curated views / metrics (dbt models, LookML, Cube) so the LLM never sees a raw 400-table ERD. dbt models are SELECT statements materialized as tables/views and composed via `ref()`; that composition **is** the join graph you allowlist.  
  2. **Text-to-SQL with allowlists** — approved views only; row-level security; read-only roles; `LIMIT`; **statement timeouts**; no multiple statements; no `INTO OUTFILE`. Middleware injects `tenant_id` / RLS; the model does not.  
  3. **RAG over data docs** — ingest dictionaries, example queries, join paths, “do not join X to Y” notes; retrieve **before** generating SQL; require a citation or refuse the table.  
  4. **Hybrid tools** — vetted parameterized tools (`get_invoice(id)`, `list_open_ar(account_id)`) for high-risk domains; open SQL only for analyst-grade questions on views.  
  5. **Schema grounding** — filtered `information_schema` + redacted sample rows in the **tool result**, versioned with the schema snapshot id. Do **not** paste entire schemas into the system prompt (tokens, confusion, leakage).

  EIP **Canonical Data Model**: each application has its own format; minimize N×N translators by agreeing on a common model. At 2 apps, CDM can cost *more* translators; at 6 apps it wins (30 pairwise vs 12). Agents are another consumer: they should speak **Customer / Invoice / Ticket**, not `CUST_XREF_V3`. Companion pattern: **Message Translator** between the producer’s format and the canonical one—dbt models and tool adapters *are* translators.

  Google SRE on pipelines: real processing accumulates **operational** complexity—worker sizing, hanging chunks, preemptions, monitoring that only reports on job completion (so a hung periodic job is silent). Pointing an agent at OLTP without a replica/warehouse strategy inherits lock contention, statement timeouts, and “thundering herd” if every user session issues a full scan.

  | Target | Use | Risk |
  |--------|-----|------|
  | Prod OLTP | Never for open SQL | Locks, PII, writes |
  | Read replica | Narrow parameterized lookups | Replica lag; still RLS |
  | Warehouse / semantic views | Analytics, text-to-SQL | Freshness SLO; still tenant filters |

  Measure **end-to-end** freshness/correctness, not per-stage “job succeeded” (SRE workbook). The user cares that AR in the answer matches billing within Y minutes, not that dbt ran. Multi-tenancy compounds schema mess: pool vs silo isolation still needs predicates the model cannot strip (Week 19 RBAC applies **inside** SQL tools).

  **Eval:** gold set of (question, allowed views, expected rows or equivalent SQL). Score **execution accuracy**, not string-match SQL. Shadow: generate, do not run, until the allowlist compiler is trusted.

* **The Alternatives:**  

  | Approach | Accuracy | Safety | Effort |
  |----------|----------|--------|--------|
  | Open text-to-SQL on raw OLTP | Fragile | Dangerous | Low upfront |
  | Semantic views + text-to-SQL | Higher | Better | Medium |
  | Hand-built tools only | Highest | Highest | High — does not scale to 200 questions |
  | Copy to warehouse then AI | Cleaner | Lag | ETL cost |
  | Fine-tuned schema linker | Strong | Still needs RLS | ML cost |
  | Dump full schema in prompt | Looks grounded | Leakage + confusion | Cheap until context fills |
  | Docs RAG only, no SQL | Safe | Cannot compute | Low |
  | Schema-on-read into vectors | Fast to demo | Garbage in answers | Hidden |

  The syllabus selects **semantic views + docs RAG + vetted write tools** because a SQL allowlist/parser that rejects unknown tables is cheaper than hoping the model “knows” the policy. Put the join graph in code. Prefer: high-risk domains → parameterized tools; exploratory analytics → text-to-SQL on **views** only.

* **Failure Modes:**  
  - Raw prod DB without RLS → data breach or accidental `UPDATE`; FDE pilots die when the first SQL hallucination touches a write-capable role.  
  - Ignoring soft deletes → answers about “customers that don’t exist.”  
  - Dual currency/timezone → wrong financial summaries and lost trust.  
  - Ignoring docs → the model invents column semantics; trusting stale docs without `as_of` → systematic bias by division.  
  - Unbounded `SELECT` without timeout → warehouse slot exhaustion (your agent as denial-of-service).  
  - Kill-and-restart the whole conversation because one GROUP BY is slow—instead cancel **that** statement, return `SQL_TIMEOUT`, continue with other tools.  
  - Pasting the full ERD → token cost, confusion, leakage.

* **Average vs. Strong Engineer:**  
  **Average:** `information_schema` dump in the system prompt; shared DBA login; `SELECT *` examples in few-shots; wiki page last edited in 2019.  
  **Strong:** semantic layer owned by analytics eng—agent consumes **only** that; approved join graph and SQL compiler; read-only role per tenant; NL→SQL eval with execution accuracy and regression on every schema snapshot bump; shadow mode then human approve for any write path; column-level masking / tokenization for PII **before** rows enter model context; tenant predicates injected by middleware; schema snapshot **version** in traces; statement timeout + max rows + max bytes returned to the model; catalog freshness SLO (dictionary PRs when dbt models change, gated in CI).

* **Worked Example:**  
  User asks Deployment Copilot: “Explain last month’s churn for Division B.”

  1. Retrieve dictionary chunks: `stat_cd` for Division B; `churn` metric defined in dbt as `fct_subscription_churn`.  
  2. Compiler allows `fct_subscription_churn` + `dim_account`; rejects `stg_salesforce_raw`.  
  3. Generated SQL runs on the warehouse with 8s statement timeout and `LIMIT 5000`.  
  4. Result carries a truncated flag if the limit was hit.  
  5. Answer cites the metric definition URL/path.

  For money and PII, the same agent prefers `get_invoice(id)` over open SQL. Middleware injects tenant filters; the model never sees a shared DBA role.

* **Apply It:**  
  1. Sketch the semantic layer: curated views/metrics + approved join graph; ban raw OLTP for open SQL.  
  2. Ingest versioned data dictionaries into RAG; retrieve **before** SQL generation; refuse tables without a citation.  
  3. Implement a SQL allowlist/compiler (views only, `LIMIT`, statement timeout, no multi-statement).  
  4. Inject tenant/RLS in middleware; use read-only roles; mask PII before model context.  
  5. Build a hybrid tool surface: parameterized tools for invoices/AR; text-to-SQL only on views.  
  6. Add NL→SQL eval with **execution** accuracy; shadow-mode generate-don’t-run until the compiler is trusted.

---

### Tolerant ETL ingestion (bronze, contracts, quarantine/DLQ)

* **Fundamentals:**  
  Customer file drops, webhook payloads, and “CSV from finance” violate contracts. Production ingestion must assume wrong encodings (Windows-1252 labeled UTF-8), extra/missing/reordered columns, duplicate primary keys, late-arriving updates, null vs empty vs `"NULL"` string, partially truncated JSON, trailing commas, and schema drift without notice.

  **Tolerant ETL design (medallion-shaped):**

  1. **Land raw first (bronze)** — immutable bytes + metadata (`source`, `received_at`, checksum, producer version if any). Replay is impossible without this.  
  2. **Validate** with explicit contracts (JSON Schema, Great Expectations, pydantic) → **quarantine** bad records; do not fail the whole batch blindly.  
  3. **Normalize** to a typed canonical model (silver) — EIP’s translator into the Canonical Data Model.  
  4. **Publish** to serving stores / vector indexes (gold) with versions.  
  5. **Dead-letter + replay**; metrics on quarantine **rate** and **age**.  
  6. **Idempotent upserts** on business keys so retries don’t duplicate.

  For LLM corpora: PDF/HTML extraction fails often—keep parent document id, chunk checksums, and allow **partial** corpus updates.

  **What SRE says about pipelines (Book Ch. 25):** periodic pipelines are fragile under organic growth—jobs exceed deadlines, hanging chunks, kill-and-restart **without checkpoints** discards all chunk work; monitoring that only emits on completion hides in-flight failure; **thundering herd** when thousands of workers start together; naive retries compound load; **Moiré** overlap of two pipelines on a shared store. Google Workflow’s answer: leases, unique output names, task versioning, server tokens—**exactly-once-shaped** commits, not “hope the CSV load is unique.”

  **Workbook (Ch. 13) best practices:** SLOs for freshness (`X% in Y minutes` / oldest data / job completed within Y) and **correctness** (golden accounts, invoice error rate)—**end-to-end**, not per-stage; plan for dependency failure; **canary pipelines** (process real data but skip production writes, or **two-phase mutation**: buffer, verify, apply); rolling 1% of *data* when you cannot canary a region; **idempotent mutations** (same input → same stored result under reprocessing); automatic quarantine of bad work units and replay as the mature bar.

  **Fail sanely:** empty/truncated config should not replace last-known-good (SRE: 2005 DNS empty file → six minutes of `NXDOMAIN`; 2009 malware list `/` matching the entire web). An empty dictionary or 0-byte CSV must **alert** and keep the previous gold index, not wipe embeddings.

  **Cloud-native DLQ (legal vendor docs):** Dataflow → BigQuery failed Storage Write API / streaming inserts via `WriteResult` (`getFailedStorageApiInserts` / failed rows) routed to a dead-letter table; Beam `BigQueryIO` deadletter pattern (`WriteResult` + `withExtendedErrorInfo` + `getFailedInsertsWithErr` / `FailedRows`; `InsertRetryPolicy.retryTransientErrors()` — **invalid** rows go to DLQ, transients retry); Pub/Sub → BigQuery template `outputDeadletterTable`; incompatible schema evolution via façade views / staging tables. EIP **Dead Letter Channel**: messages that cannot be processed go to a dedicated channel rather than blocking the pipe.

  **LLM-specific:** do not use a model to silently “fix” types into production. Use it for **suggested mappings** in a staging UI with tests. When 5% of source rows are quarantined: incremental upsert of successful keys; do not full-rebuild unless the parser change is global; surface completeness (`indexed_frac = 0.95`); rebuild when quarantine is drained or embedding schema changed.

* **The Alternatives:**  

  | Strategy | Pros | Cons |
  |----------|------|------|
  | Fail-fast entire job | Simple | One bad row blocks business → empty RAG |
  | Per-row quarantine + DLQ | Resilient | Operational load to fix DLQ |
  | Schema-on-read | Flexible | Garbage reaches consumers / RAG |
  | Contract tests with producers | Prevents issues | Needs org power |
  | LLM to “fix” rows | Tempting | Quietly invents fields — dangerous |
  | Two-phase mutation canary | Safe deploys | Latency; extra storage |
  | Exactly-once engine (Workflow-like) | Strong correctness | Heavy; still need business keys at the edges |
  | Append-only + deterministic event id | Log-shaped dedupe | Different ops model than natural-key upsert |

  Prefer: land raw → contract validate → quarantine bad rows → idempotent upsert on business keys → incremental gold. Use LLMs for **suggestions** on messy mappings in staging; do not silently auto-write production mappings without tests.

* **Failure Modes:**  
  - Brittle ETL that aborts on the first bad row → perpetual firefighting and empty RAG indexes.  
  - Silent coercion (`parseInt` → 0) → wrong AI answers that look authoritative.  
  - No raw landing → cannot replay after fixing parsers.  
  - No DLQ → poison pills halt streaming forever.  
  - No idempotent mutations → every retry/reprocess duplicates customers in the index.  
  - No two-phase / dry-run canaries → a bad dbt model or chunker ships to 100% of tenants.  
  - No freshness/correctness SLOs → “the agent is wrong” tickets that are actually a stuck pipeline.  
  - Empty dictionary file teaches the agent there are zero tables—wipes gold instead of keeping last-known-good.

* **Average vs. Strong Engineer:**  
  **Average:** cron script + `ON ERROR FAIL`; load to prod table in one shot; no checksum; DLQ is a folder named `bad/` that nobody reads.  
  **Strong:** medallion architecture; contract monitoring; schema registry for events; canary on pipeline **code** (dry-run writes) and on **data %**; idempotent upserts; data SLOs on dashboards next to LLM evals; quarantine dashboards with owner and age SLO; PII detection on ingest **before** vectors; replay runbooks; unique output names / partition dates so orphans cannot clobber; high-priority tenants processed first under crunch (workbook data isolation); encoding detection as a first-class step—never trust the filename `.utf8.csv`.

* **Worked Example:**  
  Finance drops `invoices_2026_09.csv` (Windows-1252, extra column `amt2`, one truncated row). Deployment Copilot’s ingest lands the bytes in bronze with checksum and `received_at`. Validator quarantines 12 rows to DLQ; 10,000 load to silver with idempotent upsert on `invoice_natural_key`. Gold vector index updates incrementally; UI shows “12 invoices in quarantine” / `indexed_frac` completeness. Parser fix later: replay only quarantined work units from immutable bronze—no full wipe of embeddings. Beam/Dataflow-style path: null in a REQUIRED field → `FailedRows` / dead-letter table; transient insert errors retry.

* **Apply It:**  
  1. Land immutable bronze (bytes + checksum + `received_at` + source) before any parse.  
  2. Define an explicit contract; quarantine bad rows to DLQ with rate and age metrics—do not fail the whole job on one cell.  
  3. Normalize to a canonical silver model; publish versioned gold (warehouse + vector index).  
  4. Upsert on business keys; make mutations idempotent under reprocessing.  
  5. Add pipeline canaries and/or two-phase mutations before 100% production writes.  
  6. Alert on empty/truncated inputs; keep last-known-good gold. Surface completeness when quarantine is non-zero.

---

### Partial failure design (timeouts, bulkheads, circuit breakers)

* **Fundamentals:**  
  Your AI feature depends on **their** CRM, ERP, ticketing, SharePoint, email, and IdP. Partial failure is the default: timeouts and 503s, rate limits, stale read replicas, auth token expiry mid-job, region outage of one SaaS while others live.

  **Design principles:**

  1. **Timeouts everywhere** — connect + read deadlines; no infinite waits on tool calls. Fowler: remote calls **fail or hang until a timeout**; many waiters exhaust pools and cascade.  
  2. **Bulkheads** — isolate thread/connection pools **per dependency** so one stuck CRM does not block the LLM provider client. Fowler: put calls on a pool; **break when the pool is exhausted**. SRE: thread starvation → health checks fail → more cascade.  
  3. **Circuit breakers** — stop calling a sick dependency; fail fast; probe half-open.  
  4. **Graceful degradation** — answer from RAG cache with caveat; skip enrichment; queue for later; human handoff. Google Search serves **degraded** results under overload (smaller index, drop Instant) rather than dying.  
  5. **Retries with exponential backoff + jitter** — only on idempotent/safe calls. Unbounded retries cause cascading failure. SRE: “If at first you don’t succeed, back off exponentially” / “add a little jitter.”  
  6. **Deadline propagation** — agent run has a total budget; tools inherit remaining time. Work after the client gave up is **wasted** and still loads the backend; cancel the tree.  
  7. **Status surfaces** — tell the user/agent **which** dependency failed (`CRM_TIMEOUT`); separate **retriable vs permanent** codes; don’t retry malformed requests.  
  8. **Async for slow paths** — accept job, process when customer system recovers; webhook/resume (Week 13 checkpointers). Fowler: queue work when the supplier is down; circuit can mean **queue full**.

  **Fowler circuit breaker (cite this, not folklore):** wrap the remote call; monitor failures. After **failure_threshold** (example: 5 timeouts), trip **open**: further calls raise without hitting the supplier. Success in closed state **resets** the count. **Half-open:** after `reset_timeout`, allow a trial call; success resets, failure restarts the open timer. Not all errors should trip (business 404 vs timeout vs connection failure—different thresholds). Monitor state changes; ops can trip/reset. Clients must **react**: fail the operation, queue, or show **stale** data. Fowler’s illustrative params (`invocation_timeout = 0.01`, `failure_threshold = 5`, `reset_timeout = 0.1`) are not production defaults—set timeouts from **SLO and remaining deadline**.

  **EIP Request-Response with Retry:** consumer retries if no response in an interval; **both** sides must be idempotent (lost **response** looks like lost **request**). Duplicate response: requestor must ignore the second. Dynamic behavior: slow provider → timeouts → **more** requests → worse overload. Mitigations: **max retry count**; **exponential backoff**; **circuit breakers** that return error immediately instead of waiting another timeout.

  **SRE overload / cascade tactics:** capacity is **not QPS**—model CPU (and RAM); query cost varies. **Per-customer quotas** so one noisy tenant (or one agent loop) does not drown others. **Adaptive client throttling:** if `requests` ≫ `accepts`, reject locally; typical **K=2** (`requests = 2 * accepts`). **Small queues** vs thread pool (e.g. ≤50%) so you **reject early**; shed HTTP **503** when in-flight > N. Retry rules: randomized exponential backoff; **limit retries per request**; **server-wide retry budget** (example: 60 retries/minute then stop); never retry permanent/malformed; distinct overloaded status so others **don’t** retry. Missed RPC deadlines: server work wasted; clients retry → more overload. Workbook: plan for dependency failure using advertised SLAs; practice failover so you don’t serve **stale processed as fresh**.

  AWS Agentic AI Lens: test **degraded** performance; **dynamic capability toggling**—turn off “live CRM” as a product flag when the breaker is open. `[NEEDS MORE RESEARCH]` for exact BP numbers beyond AGENTREL06-BP03 / BP05 naming cited in research.

  Agent UX modes:

  | Mode | UX | Correctness |
  |------|----|-------------|
  | Fail closed | Error message | Safe |
  | Serve stale | Fast | May be wrong — **label** |
  | Queue + notify | Delayed success | Good for tickets/emails |
  | Proceed without tool | Partial answer | Must label missing context |
  | Multi-provider failover | Resilient | Consistency differences |

  Structured observation example: `{tool: "salesforce.get_account", error: "TIMEOUT", elapsed_ms: 2000, circuit: "closed", remaining_deadline_ms: 8000}`.

* **The Alternatives:**  

  | Approach | Protects | Cost |
  |----------|----------|------|
  | Timeouts only | Hung sockets | Still retry storms |
  | Timeouts + jittered retries | Transients | Amplifies if not idempotent / no budget |
  | Fowler breaker | Sick dependency + your pools | Need half-open + metrics; can hide recovery if timeout too long |
  | Bulkhead pools | Blast radius | Under-utilization; must size per SaaS |
  | Adaptive throttling | Global overload | Sporadic clients have poor local view (SRE caveat) |
  | Always fail closed | Safety | Demo dies when Salesforce blinks |
  | Always stale | Availability | Compliance / wrong advice |
  | Queue all writes | Customer outages | Need idempotency + drain SLOs |

  **Shared vs local breakers:** per-replica open is simpler; shared (Redis) trips faster cluster-wide but synchronized open is a new failure mode. The syllabus selects **timeouts + bulkheads + Fowler breaker + labeled degradation** because open circuit is cheaper than waiting on a dead CRM, and generic “something went wrong” causes the model to retry the same POST.

* **Failure Modes:**  
  - A single hung customer API without timeouts pins all workers → full platform outage (**your** fault in the customer’s eyes).  
  - No degradation path → brittle demos and unpaid renewals.  
  - No structured dependency errors → the LLM retries uselessly and burns tokens.  
  - Retries without jitter/backoff/budget → you DDoS the recovering CRM.  
  - Circuit without **timeouts** still waits on the first N calls.  
  - Blind retries of non-idempotent POSTs → duplicate tickets/orders (next concept).  
  - Treating partial data as a 500 instead of success-with-holes (warehouse OK, CRM skipped, completeness flag missing).

* **Average vs. Strong Engineer:**  
  **Average:** default HTTP client timeout or none; `try/except` log; retry 3 times on every status code; one process-wide connection pool.  
  **Strong:** per-dependency SLOs and timeouts derived from remaining deadline; chaos latency injection and 503s; explicit tool error types in the agent observation channel; runbooks; fallback model **provider** (Week 20) **and** fallback **data** (stale RAG); “degraded mode” product copy; queue depth alerts when customer system is down; retry budgets; never retry 4xx validation; ops can trip a breaker; tests: Salesforce +5s, Salesforce down, billing OK — assert partial labeled answer.

* **Worked Example:**  
  Deployment Copilot: CRM p99 is 400ms, tool timeout 2s, failure threshold 5, reset 30s. Agent deadline 15s. User asks open AR for Acme. Text-to-SQL on `vw_ar_open` succeeds. Salesforce `get_account` times out at 2s; breaker still closed (1/5). Answer uses warehouse AR, labels “CRM account owner not refreshed,” remaining deadline propagated to other tools. After five CRM timeouts, circuit **open**; next calls fail fast with `CRM_CIRCUIT_OPEN`—answer from last good RAG/warehouse with caveat; Zendesk write goes to outbox (keyed). Half-open probe after 30s. Structured observation carries `TIMEOUT` / `circuit` / `remaining_deadline_ms` so the model does not invent a blind POST retry.

* **Apply It:**  
  1. Put connect + read timeouts on every tool; derive from remaining agent deadline.  
  2. Bulkhead connection/thread pools **per** customer dependency.  
  3. Implement Fowler closed / open / half-open with failure threshold, reset timeout, and ops trip/reset.  
  4. Emit structured tool errors (`CRM_TIMEOUT`, `SQL_TIMEOUT`, `CRM_CIRCUIT_OPEN`); separate retriable vs permanent.  
  5. Define degradation copy: stale RAG + caveat, skip enrichment, or queue writes.  
  6. Cap retries with backoff + jitter + retry budget; never retry non-idempotent POSTs from this layer alone. Test Salesforce-down / billing-OK partial answers.

---

### Idempotency for agent side effects (Stripe keys, unknown outcome)

* **Fundamentals:**  
  Agents retry. Networks duplicate. Users double-click. Queues redeliver. LangGraph replays nodes. Any tool that **sends email, charges cards, creates tickets, updates CRM, or triggers workflows** needs **idempotency**.

  EIP already stated the distributed-systems reason: a timeout cannot distinguish **lost request** from **lost response**; retry requires an **Idempotent Receiver** that keys on a correlation id and returns the **cached** response. Stripe is the industry-standard **HTTP** encoding of that pattern.

  **Stripe idempotent requests (canonical API):**

  1. Client sends `Idempotency-Key` on **creating or updating** an object.  
  2. Stripe saves **status code + body** of the **first request that began executing**, **success or failure**, **including 500**. Later same key → **same result**.  
  3. Client generates the key (V4 UUID or high-entropy string; **≤255 chars**; **no PII**).  
  4. Keys prune after they are **at least 24 hours** old; reuse after prune is a **new** request.  
  5. Incoming params compared to original; **mismatch → error**.  
  6. Results saved **only after endpoint execution begins**. Validation failure **before** execution, or **concurrent conflict**, is **not** saved — **safe to retry**.  
  7. All **POST**s accept keys. **GET/DELETE**: sending a key has **no effect** (already idempotent by HTTP definition).

  FDE implication: if **your** store caches only successes, you do **not** match Stripe; a cached 500 can **poison** a key (Stripe’s choice) or you may allow retry on 5xx—**document which**. Concurrent in-flight: Stripe does not save; you need a **lease** / `in_progress` so two workers don’t both execute.

  **Deterministic keys for agents (AWS AGENTREL06-BP04):** anti-pattern is UUID or timestamp **minted at retry time** → different key → duplicate side effects. **Do:** hash `(workflow_id, task_type, request_body)` or equivalent so retries collide. Pre-check store; return cached success; conditional writes so two parallel retries cannot both commit; **TTL** ≥ retry window. **Propagate** parent key or deterministic derivative to subtasks and to external APIs that accept keys. Monitor **cache hit rate** on the idempotency store.

  AWS Durable Execution: replay/retry runs the step again. **At-least-once** (default) is safe only if the step is idempotent. **At-most-once per retry**: wait for START checkpoint before side effect; interruption → `StepInterrupted`, not silent re-run. Neither is exactly-once across the workflow if the retry policy still retries—combine at-most-once with **no-retry** for “charge card once.” If the API supports keys: **generate the key inside a checkpointed step**; a key generated **outside** the step **changes on replay**. Duplicate-request error from the API often means **first attempt succeeded**—treat as success. If you own the DB: `ON CONFLICT DO NOTHING`, conditional `PutItem`, transactional check-then-write, append-only events with deterministic ids.

  **Agent-specific rules:**

  - Mint keys at **plan time** (or in a durable step) **before** the first tool call—not in the HTTP retry adapter.  
  - Derive from `(tenant, agent_run_id, step_id, action_type, business_object_id)` when possible. **Never** from free-form LLM text (paraphrase → new key). Model may pass `payment_id`; wrapper computes the key (Week 14).  
  - Propagate through orchestrations and into Stripe/Zendesk/etc.  
  - **Timeout with unknown outcome:** do **not** free the key and blindly retry with a new UUID. **Reconcile** (GET by id / “status of this key”) or surface `STATE_UNKNOWN`. Retry **same** key only after the protocol allows (Stripe: same params).  
  - **Leases** for `in_progress` so dead workers don’t block forever; expired lease + reconcile, not double execute.  
  - Separate read tools (naturally idempotent) from write tools (`no_auto_retry` unless keyed).  
  - Prefer **hiding the key** from the model rather than hoping schemas teach reuse.

  **Cron / pipelines:** SRE distributed cron favors **skipping a launch over double launch** because undo is harder (payroll/newsletter vs GC). Workbook: **idempotent mutations** and **two-phase mutations** so reprocessing and canaries don’t corrupt stores.

  **Sagas / multi-step:** CRM create + email send is not one HTTP key. Options: saga log with compensating actions (email can’t unsend—compensate with “ignore / apology”); **one key per side-effecting step**, derived from parent intent + step name; outbox (commit intent locally, workers deliver with keys). There is no cross-system exactly-once—only **at-least-once + idempotent receivers** (EIP).

* **The Alternatives:**  

  | Approach | Protects against | Gaps |
  |----------|------------------|------|
  | Natural idempotency (`PUT` absolute state) | Many retries | Not all APIs support |
  | Stripe-style keys | Duplicate submits | Requires server support; 24h window |
  | Outbox + at-least-once with dedupe | Distributed commit | Complexity |
  | Human approval for writes | Dup risk ↓ | Latency / ops (Week 14) |
  | AWS at-most-once + no retry | Double charge | Need reconcile UX on interrupt |
  | Exactly-once wishful thinking | — | Doesn’t exist across systems |
  | UUID in retry loop | Looks like a key | **Defeats** idempotency |

  Caching only “seen key” without **response body** → retries return inconsistent payloads. Caching 500s (Stripe) vs not: pick and test. The syllabus selects **deterministic keys minted at plan time + Stripe-compatible storage + unknown-outcome reconcile**.

* **Failure Modes:**  
  - Without keys: duplicate refunds, double shipments, spammed customers.  
  - Keys minted inside a retry loop (`uuid4()` each attempt): **false sense of safety**.  
  - Timeout then new key: **two tickets** if the first POST landed (EIP lost-response case).  
  - Cron newsletter without skip-over-duplicate policy: customers get two emails.  
  - Cache only successes → concurrent workers both execute; or undocumented sticky 500 poisons a key forever.  
  - Key derived from LLM prose → paraphrase creates a new side effect.

* **Average vs. Strong Engineer:**  
  **Average:** hope tool APIs are safe; retry 3 times; generate UUID in the HTTP middleware per attempt.  
  **Strong:** tool registry marks side-effecting tools; mandatory key arg **filled by harness**; broker wraps third parties that lack keys (dedupe table in front of SOAP); reconciliation tools (`find_ticket_by_external_id`); DLQ for failed agent writes; audit log of key → side effect; tests that kill workers mid-flight and assert single execution; Stripe-compatible semantics for **your** API if you expose agent writes; OBO / multi-tenant token exchange still sits on **idempotent backends**.

* **Worked Example:**  
  User says “file a ticket” for Acme. Deployment Copilot mints:

  ```
  sha256(tenant_id | agent_run_id | "zendesk.ticket.create" | account_id | intent_hash)
  ```

  `intent_hash` = hash of stable fields (subject template id + object id), **not** the model’s prose. TTL 48h (> 2× client retry window; Stripe’s floor is 24h).

  Path: (1) Claim row `key` status=`in_progress` (conditional insert). (2) POST Zendesk with `Idempotency-Key` if supported, else store external id. (3) On 201: save body, status=`done`. (4) On timeout: leave `in_progress` + lease; **search** by key/external id; if found, complete; if not and lease expired, **one** retry **same** key. (5) User double-click / graph replay: same key → stored 201. No second ticket.

* **Apply It:**  
  1. Mark side-effecting tools in the registry; harness mints keys at plan time from `(tenant, run_id, step_id, action, object_id)`.  
  2. Store status + body (document 5xx policy); TTL ≥ retry window (≥24h if Stripe-compatible).  
  3. Use leases / conditional writes for `in_progress`; never mint a new key on timeout.  
  4. On unknown outcome: reconcile via GET / key lookup or surface `STATE_UNKNOWN`; retry **same** key only.  
  5. Propagate keys to external APIs; broker APIs that lack keys.  
  6. Add kill-worker-mid-flight tests; skip-over-duplicate for non-idempotent cron; one key per saga step or compensating actions.

---
