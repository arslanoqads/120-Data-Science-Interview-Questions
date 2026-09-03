# 03 — Partial failure design (customer system down or slow)

> Week 21 — Timeouts, bulkheads, circuit breakers, degradation.  
> Research notes (raw). Idempotent retries of **writes** are file [04](04-idempotency-side-effects.md). Do not retry POSTs from this file alone.

---

## Fundamentals

Your AI feature depends on **their** CRM, ERP, ticketing, SharePoint, email, and IdP. Partial failure is the default:

- Timeouts and 503s  
- Rate limits  
- Stale read replicas  
- Auth token expiry mid-job  
- Region outage of one SaaS while others live  

**Design principles:**

1. **Timeouts everywhere** — connect + read deadlines; no infinite waits on tool calls. Fowler: remote calls **fail or hang until a timeout**; many waiters exhaust pools and cascade ([Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)).  
2. **Bulkheads** — isolate thread/connection pools **per dependency** so one stuck CRM does not block the LLM provider client. Fowler: put calls on a pool; **break when the pool is exhausted**. SRE: thread starvation → health checks fail → more cascade ([Cascading failures](https://sre.google/sre-book/addressing-cascading-failures/)).  
3. **Circuit breakers** — stop calling a sick dependency; fail fast; probe half-open.  
4. **Graceful degradation** — answer from RAG cache with caveat; skip enrichment; queue for later; human handoff. Google Search serves **degraded** results under overload (smaller index, drop Instant) rather than dying ([Handling overload](https://sre.google/sre-book/handling-overload/); [Service best practices](https://sre.google/sre-book/service-best-practices/)).  
5. **Retries with exponential backoff + jitter** — only on idempotent/safe calls. Unbounded retries cause cascading failure. SRE epigraph: “If at first you don’t succeed, back off exponentially” / “add a little jitter” ([Cascading failures](https://sre.google/sre-book/addressing-cascading-failures/)).  
6. **Deadline propagation** — agent run has a total budget; tools inherit remaining time. Work after the client gave up is **wasted** and still loads the backend; cancel the tree ([same chapter](https://sre.google/sre-book/addressing-cascading-failures/)).  
7. **Status surfaces** — tell the user/agent **which** dependency failed (`CRM_TIMEOUT`), don’t swallow into generic “something went wrong.” Separate **retriable vs permanent** codes; don’t retry malformed requests.  
8. **Async for slow paths** — accept job, process when customer system recovers; webhook/resume (Week 13 checkpointers). Fowler: queue work when the supplier is down; circuit can mean **queue full**.

### Fowler circuit breaker (cite this, not folklore)

Martin Fowler (2014), popularizing Nygard *Release It*:

- Wrap the remote call; monitor failures.  
- After **failure_threshold** (example: 5 timeouts), trip **open**: further calls raise `CircuitBreaker::Open` **without** hitting the supplier.  
- Success in closed state **resets** the count.  
- **Half-open:** after `reset_timeout`, allow a trial call; success resets, failure restarts the open timer.  
- Not all errors should trip (business 404 vs timeout vs connection failure — different thresholds).  
- **Monitor:** log state changes; ops can trip/reset; breaker trips are early warning.  
- Clients must **react**: fail the operation, queue (e.g. credit-card auth later), or show **stale** data.

Example parameterization in the article: `invocation_timeout = 0.01` (illustrative), `failure_threshold = 5`, `reset_timeout = 0.1`. Production FDE: set timeouts from **SLO and remaining deadline**, not copy-paste 10ms.

### EIP: retries without breakers amplify load

[Request-Response with Retry](https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html):

- Consumer retries if no response in an interval; **both** sides must be idempotent (lost **response** looks like lost **request**).  
- Duplicate response: requestor must ignore the second.  
- **Idempotent Receiver** + same Correlation Identifier; cache the response (stateful provider).  
- Dynamic behavior: slow provider → timeouts → **more** requests → worse overload.  
- Mitigations: **max retry count**; **exponential backoff**; **circuit breakers** that return error immediately instead of waiting another timeout.  
- RosettaNet: receiver **must** accept duplicates and **resend** the same ack.

EIP AWS loan-broker series shows EventBridge-style breaker implementations ([loan broker CDK](https://www.enterpriseintegrationpatterns.com/ramblings/loanbroker_cdk.html)).

### SRE overload / cascade (numbers and tactics)

- Capacity is **not QPS** — model **CPU (and RAM)**; query cost varies ([Handling overload](https://sre.google/sre-book/handling-overload/)).  
- **Per-customer quotas** so one noisy tenant (or one agent loop) does not drown others.  
- **Adaptive client throttling:** if `requests` ≫ `accepts`, reject locally; typical **K=2** (`requests = 2 * accepts`) so ~half backend work can be rejects but state propagates fast; lower K if reject cost ≈ serve cost.  
- **Small queues** vs thread pool (e.g. ≤50%) so you **reject early** rather than queue 1.1s of latency; Gmail often **queueless** + failover.  
- Shed: HTTP **503** when in-flight > N; LIFO/CoDel drop requests the user already abandoned.  
- Retry rules: randomized exponential backoff; **limit retries per request**; **server-wide retry budget** (example: 60 retries/minute then stop); never retry permanent/malformed; distinct overloaded status so others **don’t** retry.  
- Missed RPC deadlines: server work wasted; clients retry → more overload.  
- **GC death spiral** (Java) as a cascade story — FDE: Python GIL + unbounded threadpool per tool is the analog.

Workbook: **plan for dependency failure** using advertised SLAs; replicate if a single-region store cannot meet your freshness SLO; practice failover so you don’t serve **stale processed as fresh** ([Plan for dependency failure](https://sre.google/workbook/data-processing/)).

AWS Agentic AI Lens: test **degraded** performance; **dynamic capability toggling** (related BPs AGENTREL06-BP03 / BP05) — turn off “live CRM” as a product flag when the breaker is open.

### Agent UX for partial failure

| Mode | UX | Correctness |
|------|----|-------------|
| Fail closed | Error message | Safe |
| Serve stale | Fast | May be wrong — **label** |
| Queue + notify | Delayed success | Good for tickets/emails |
| Proceed without tool | Partial answer | Must label missing context |
| Multi-provider failover | Resilient | Consistency differences |

Agents that **blindly retry** non-idempotent POSTs create duplicate tickets/orders (file 04).

Structured observation example: `{tool: "salesforce.get_account", error: "TIMEOUT", elapsed_ms: 2000, circuit: "closed", remaining_deadline_ms: 8000}`.

---

## Alternatives & Tradeoffs

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

**Shared vs local breakers:** per-replica open is simpler; shared (Redis) trips faster cluster-wide but synchronized open is a new failure mode (SRE: Chubby-watched config for degradation can **sync-fail**).

---

## Necessity

A single hung customer API without timeouts pins all workers → full platform outage (**your** fault in the customer’s eyes).

No degradation path → brittle demos and unpaid renewals.

No structured dependency errors → the LLM retries uselessly and burns tokens (Week 20 spend cube will show it; this week prevents it).

Retries without jitter/backoff/budget → you DDoS the recovering CRM (EIP + SRE). Circuit without **timeouts** still waits on the first N calls.

---

## Industry Practice

**Common:** default HTTP client timeout or none; `try/except` log; retry 3 times on every status code; one process-wide connection pool.

**Strong:**

- Per-dependency SLOs and timeouts derived from remaining deadline.  
- Chaos: latency injection, 503s (CNCF/KubeCon talks).  
- Explicit tool error types in the agent observation channel.  
- Runbooks; fallback model **provider** (Week 20) **and** fallback **data** (stale RAG).  
- “Degraded mode” product copy approved by legal for regulated advice.  
- Queue depth alerts when customer system is down.  
- Retry budgets; never retry 4xx validation.  
- Ops can trip a breaker (Fowler).  
- Tests: Salesforce +5s, Salesforce down, billing OK — assert partial labeled answer.

---

## Concrete Scenario

SRE — Handling Overload; Addressing Cascading Failures; Service Best Practices (retries, Search degradation, jitter):  
https://sre.google/sre-book/handling-overload/  
https://sre.google/sre-book/addressing-cascading-failures/  
https://sre.google/sre-book/service-best-practices/

Fowler Circuit Breaker (closed / open / half-open, pool exhaustion, stale workaround):  
https://martinfowler.com/bliki/CircuitBreaker.html

EIP Request-Response with Retry (max retries, exponential backoff, circuit breakers, idempotent receiver):  
https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html

KubeCon / CNCF resilience and chaos:  
https://www.youtube.com/@cncf

Workbook dependency failure / DiRT:  
https://sre.google/workbook/data-processing/

**Sketch:** CRM p99 is 400ms, timeout 2s, threshold 5, reset 30s. Agent deadline 15s. After 5 CRM timeouts, open; answer from warehouse + “CRM unavailable”; Zendesk write goes to outbox (keyed). Half-open probe on next request after 30s.

---

## Open Questions

- How should multi-agent systems **share** circuit-breaker state?  
- When is “answer without live CRM” legally acceptable in regulated advice?  
- Product UX for multi-hour customer outages on async agent jobs?  
- Should LLM-provider breakers and SaaS breakers share one dashboard or stay isolated (bulkhead for **ops** too)?

---

## Sources

- https://martinfowler.com/bliki/CircuitBreaker.html  
- https://sre.google/sre-book/handling-overload/  
- https://sre.google/sre-book/addressing-cascading-failures/  
- https://sre.google/sre-book/service-best-practices/  
- https://sre.google/sre-book/distributed-periodic-scheduling/  
- https://sre.google/workbook/data-processing/  
- https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html  
- https://www.enterpriseintegrationpatterns.com/ramblings/loanbroker_cdk.html  
- https://www.youtube.com/@cncf  
