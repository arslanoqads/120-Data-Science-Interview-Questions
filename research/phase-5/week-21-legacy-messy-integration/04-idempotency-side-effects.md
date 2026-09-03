# 04 — Idempotency in agent actions with side effects

> Week 21 — Once-per-intent writes when agents retry.  
> Research notes (raw). Week 14 covered HITL/dry-run envelope; this file is **Stripe-accurate keys**, **unknown timeout**, and **pipeline vs agent** overlap. Partial-failure retries are file [03](03-partial-failure-design.md).

---

## Fundamentals

Agents retry. Networks duplicate. Users double-click. Queues redeliver. LangGraph replays nodes. Any tool that **sends email, charges cards, creates tickets, updates CRM, or triggers workflows** needs **idempotency**.

EIP already stated the distributed-systems reason: a timeout cannot distinguish **lost request** from **lost response**; retry requires an **Idempotent Receiver** that keys on a correlation id and returns the **cached** response ([Request-Response with Retry](https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html)). Stripe is the industry-standard **HTTP** encoding of that pattern.

### Stripe idempotent requests (canonical API)

From [Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests):

1. Client sends `Idempotency-Key` (header / `IdempotencyKey` option) on **creating or updating** an object.  
2. Stripe saves **status code + body** of the **first request that began executing**, **success or failure**, **including 500**. Later same key → **same result**.  
3. Client generates the key (V4 UUID or high-entropy string; **≤255 chars**; **no PII** — no emails or personal ids).  
4. Keys prune after they are **at least 24 hours** old; reuse after prune is a **new** request.  
5. Incoming params compared to original; **mismatch → error** (misuse).  
6. Results saved **only after endpoint execution begins**. Validation failure **before** execution, or **concurrent conflict**, is **not** saved — **safe to retry**.  
7. All **POST**s accept keys. **GET/DELETE**: sending a key has **no effect** (already idempotent by HTTP definition).

FDE implication: if **your** store caches only successes, you do **not** match Stripe; a cached 500 can **poison** a key (Stripe’s choice) or you may allow retry on 5xx — **document which**. Concurrent in-flight: Stripe does not save; you need a **lease** / `in_progress` so two workers don’t both execute.

### Deterministic keys for agents (AWS)

[AGENTREL06-BP04](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentrel06-bp04.html):

- **Anti-pattern:** UUID or timestamp **minted at retry time** → different key → duplicate side effects.  
- **Do:** hash `(workflow_id, task_type, request_body)` or equivalent so retries collide.  
- Pre-check store; return cached success; DynamoDB **conditional writes** so two parallel retries cannot both commit; **TTL** ≥ retry window.  
- **Propagate** parent key or deterministic derivative to subtasks and to external APIs that accept keys.  
- Monitor **cache hit rate** on the idempotency store — hits mean retries are working.

[AWS Durable Execution — idempotency](https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/):

- Replay/retry run the step again. **At-least-once** (default): safe only if the step is idempotent. **At-most-once per retry**: wait for START checkpoint before side effect; interruption → `StepInterrupted`, not silent re-run. **Neither is exactly-once across the workflow** if the retry policy still retries — combine at-most-once with **no-retry** for “charge card once.”  
- If the API supports keys: **generate the key inside a checkpointed step**; a key generated **outside** the step **changes on replay**.  
- Duplicate-request error from the API often means **first attempt succeeded** — treat as success.  
- If you own the DB: `ON CONFLICT DO NOTHING`, conditional `PutItem`, transactional check-then-write, append-only events with deterministic ids. Avoid bare `INSERT` and unchecked counter increments.

### Agent-specific rules

- Mint keys at **plan time** (or in a durable step) **before** the first tool call — not in the HTTP retry adapter.  
- Derive from `(tenant, agent_run_id, step_id, action_type, business_object_id)` when possible. **Never** from free-form LLM text (paraphrase → new key). Model may pass `payment_id`; wrapper computes the key (Week 14).  
- Propagate through orchestrations and into Stripe/Zendesk/etc.  
- **Timeout with unknown outcome:** do **not** free the key and blindly retry with a new UUID. **Reconcile** (GET by id / “status of this key”) or surface `STATE_UNKNOWN` to the agent/human. Retry **same** key only after the protocol allows (Stripe: same params).  
- **Leases** for `in_progress` so dead workers don’t block forever; expired lease + reconcile, not double execute.  
- Separate read tools (naturally idempotent) from write tools (`no_auto_retry` unless keyed).  
- Mark tool schemas so models **reuse** keys rather than inventing new ones each thought step — better: **hide the key** from the model.

### Cron / pipelines (don’t double-launch)

SRE distributed cron: some jobs are idempotent (GC every 5 minutes — skip is OK); some are not (payroll, newsletter). Google **favors skipping a launch over double launch** because undo is harder; fail closed ([Distributed periodic scheduling](https://sre.google/sre-book/distributed-periodic-scheduling/)).

SRE workbook: **idempotent mutations** and **two-phase mutations** so reprocessing and canaries don’t corrupt stores ([workbook](https://sre.google/workbook/data-processing/)).

SRE automation chapter is additional context for “safe to re-run” culture ([Automation at Google](https://sre.google/sre-book/automation-at-google/)).

### Sagas / multi-step

CRM create + email send: **one user intent** is not one HTTP key. Options:

- **Saga log** with compensating actions (email can’t unsend — compensate with “ignore / apology”).  
- **One key per side-effecting step**, derived from parent intent + step name.  
- Outbox: commit “intent” locally, workers deliver with keys.

There is no cross-system exactly-once. There is **at-least-once + idempotent receivers** (EIP).

---

## Alternatives & Tradeoffs

| Approach | Protects against | Gaps |
|----------|------------------|------|
| Natural idempotency (`PUT` absolute state) | Many retries | Not all APIs support |
| Stripe-style keys | Duplicate submits | Requires server support; 24h window |
| Outbox + at-least-once with dedupe | Distributed commit | Complexity |
| Human approval for writes | Dup risk ↓ | Latency / ops (Week 14) |
| AWS at-most-once + no retry | Double charge | Need reconcile UX on interrupt |
| Exactly-once wishful thinking | — | Doesn’t exist across systems |
| UUID in retry loop | Looks like a key | **Defeats** idempotency |

Caching only “seen key” without **response body** → retries return inconsistent payloads. Caching 500s (Stripe) vs not: pick and test.

---

## Necessity

Without keys: duplicate refunds, double shipments, spammed customers — classic agent demos-gone-wrong.

With keys minted inside a retry loop (`uuid4()` each attempt): **false sense of safety** (AWS BP04).

Timeout then new key: **two tickets** if the first POST landed (EIP lost-response case).

Cron newsletter without skip-over-duplicate policy: customers get two emails; SRE says skip is the recoverable failure.

---

## Industry Practice

**Common:** hope tool APIs are safe; retry 3 times; generate UUID in the HTTP middleware per attempt.

**Strong:**

- Tool registry marks side-effecting tools; mandatory key arg **filled by harness**.  
- Broker wraps third parties that lack keys (dedupe table in front of SOAP).  
- Reconciliation tools (`find_ticket_by_external_id`).  
- DLQ for failed agent writes.  
- Audit log of key → side effect (Week 14).  
- Tests: kill worker mid-flight; assert single execution.  
- Stripe-compatible semantics for **your** API if you expose agent writes to others.  
- OBO / multi-tenant token exchange still sits on **idempotent backends** ([AgentCore gateway OBO](https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/)).

---

## Concrete Scenario

**Create Zendesk ticket** key:

```
sha256(tenant_id | agent_run_id | "zendesk.ticket.create" | account_id | intent_hash)
```

`intent_hash` = hash of stable fields (subject template id + object id), **not** the model’s prose. TTL 48h (> 2× client retry window; Stripe’s floor is 24h).

Path:

1. Claim row `key` status=`in_progress` (conditional insert).  
2. POST Zendesk with `Idempotency-Key` if supported, else store external id.  
3. On 201: save body, status=`done`.  
4. On timeout: leave `in_progress` + lease; **search** by key/external id; if found, complete; if not and lease expired, **one** retry **same** key.  
5. User double-click / graph replay: same key → stored 201.

Stripe reference: [idempotent requests](https://docs.stripe.com/api/idempotent_requests).  
AWS BP04: [AGENTREL06-BP04](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentrel06-bp04.html).  
Durable execution key-inside-step: [idempotency and retries](https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/).  
SRE cron: [distributed periodic scheduling](https://sre.google/sre-book/distributed-periodic-scheduling/).  
Talk: [Idempotent data pipelines (YouTube)](https://www.youtube.com/watch?v=GcU2vxYrA3g).

---

## Open Questions

- Who owns key **namespaces** — agent framework, API gateway, or each tool?  
- Cross-tool sagas: one key or saga log with compensations?  
- How to teach models via tool schemas to *reuse* keys — or should keys never enter the prompt?  
- Should 500s be sticky (Stripe) for agent tools whose 500s are often transient?

---

## Sources

- https://docs.stripe.com/api/idempotent_requests  
- https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentrel06-bp04.html  
- https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/  
- https://sre.google/sre-book/distributed-periodic-scheduling/  
- https://sre.google/workbook/data-processing/  
- https://sre.google/sre-book/automation-at-google/  
- https://www.enterpriseintegrationpatterns.com/patterns/conversation/RequestResponseRetry.html  
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html  
- https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/  
- https://www.youtube.com/watch?v=GcU2vxYrA3g  
