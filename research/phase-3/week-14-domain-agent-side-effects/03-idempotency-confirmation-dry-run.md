# 03 — Idempotency, confirmation gates, and dry-run

> Week 14 — The three runtime controls that sit on every write  
> Research notes (raw). Teach as one envelope; implement as separate code paths.

---

## Fundamentals

Agents and harnesses provide **at-least-once** tool execution in practice: HTTP timeouts, LangGraph **node replay** after `interrupt`, checkpoint resume, user “try again,” A2A client retry after a dropped SSE stream. For non-idempotent writes, that means **duplicate side effects** unless a **server** (or a durable dedupe layer in front of a legacy API) coalesces retries.

Week 13 already requires: code **before** `interrupt()` is side-effect-free or idempotent; the write lives **after** resume ([LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)). This file is the rest of the envelope: **keys**, **gates**, **preview**.

### A. Idempotency (Stripe-style)

Stripe ([Idempotent requests](https://docs.stripe.com/api/idempotent_requests)):

1. Client sends `Idempotency-Key` on **POST** (header; up to 255 chars).  
2. Server stores **status code + body** of the first request that **began executing**, success **or** failure (including **500**).  
3. Retries with the **same key + same params** return the **same** result.  
4. Same key + **different params** → error (misuse).  
5. Keys prune after **≥ 24 hours**; reuse after prune is a **new** request.  
6. **GET/DELETE** ignore keys (already idempotent by HTTP definition).  
7. If validation fails **before** endpoint execution, Stripe **does not** save the result — you **may** retry. Concurrent conflict similarly unsaved.  
8. Generate keys as **V4 UUIDs** or high-entropy strings. **Do not** put PII (email, personal ids) in the key.  
9. Client owns key generation.

**Agent-specific rules** (apply Stripe’s model to tool wrappers):

- Derive the key from **stable structural context**: `tenant + intent + business object id + step id + A2A taskId / graph thread_id`. **Never** from free-form LLM text (the model will paraphrase and mint a new key).  
- Wrapper performs **claim → execute → record** atomically (or uses the downstream API’s native key).  
- Do **not** treat a cached **transient** failure as “never retry” if your store (unlike Stripe) only caches successes — know your semantics. Stripe caches 500s; a naive cache of “error” can poison a key. Document which you chose.  
- Pair with **read-back** when the downstream API has no native idempotency (legacy SOAP, “fire email”).  
- Bind the key to the **A2A Task** when the write is delegated: client and server must not each mint independent keys for the same user intent.

```python
# Wrapper, not the model
key = idempotency_key(
    tenant=auth.tenant_id,
    intent="refund.create",
    payment_id=payment_id,
    task_id=a2a_task_id or thread_id,
)
# Model may pass payment_id; it must not pass `key`
```

If two different intents must hit the same API (partial refund then second partial), they **must** use **different** keys (different `intent` or `attempt` / `refund_line_id`).

### B. Confirmation gates (HITL) — structural, not prompt-based

A **confirmation gate** forces a human (or a **policy engine** with a recorded decision id) to approve before a dangerous side effect **commits**.

**Weak form (insufficient):** system prompt “always ask the user”; model prints “Confirm?” and then calls `refund` anyway. Jailbreak / confused trajectory bypasses this. Anthropic: agents should **pause** at checkpoints or blockers — that pause must be in the **harness** ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

**Harness form (Week 13):** `interrupt(payload)` **before** the write; `Command(resume=…)` after a durable checkpoint. Official example: `"Transfer $500"` as `action_details` ([Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)). Node replay: anything **before** `interrupt` runs again → **no write there**.

**Tokenized propose/commit (tool-level, framework-agnostic):**

1. Agent calls `propose_refund` → human-readable summary + **single-use token** (TTL, bound to args hash).  
2. UI shows summary (ideally the **dry-run** payload). Human approves in *your* app, not in the model’s imagination.  
3. `commit_refund(token)` executes in the **same transaction as token consume**.  
4. Retry after success returns `already_consumed` / idempotent result — must not loop creating tokens.

Combine: graph `interrupt` displays the preview; on resume the node calls `commit` with a server-issued token. **Redact tokens in logs** (file 04).

Risk-tier tools so you do not interrupt on `lookup_customer`. Dual control (two humans) for break-glass. Policy engine auto-approve **under a threshold** (e.g. refund &lt; $25) still emits an **approval id** of type `policy:threshold`.

**A2A:** gate at the **client** (user-facing) **and/or** the **remote** (system of record). Remote should not trust “the other agent said the human approved” without a signed approval id or shared IdP. Spec is **async-first** and explicitly mentions HITL-long tasks — use Task state (`input_required` patterns in implementations) rather than blocking HTTP.

### C. Dry-run / preview

A **dry-run** tool returns **what would happen** (diffs, affected rows, cost, recipients) **without** mutating state. Agents chain dry-runs to validate a plan; HITL summaries should be **this payload**, not a model paraphrase.

Requirements:

- **Parity:** preview must match commit closely enough that operators can trust it. Document known drift (e.g. FX rate at commit time).  
- **Naming poka-yoke:** `refund_preview` vs `refund_commit`, or a mandatory `dry_run: true` **default** that the wrapper rejects flipping without a gate. Anthropic: change arguments so mistakes are harder.  
- Preview is **read-only** toward the system of record; it may still read clocks and balances (those can race — say so in the payload `as_of` timestamp).  
- Include preview artifacts in the **audit trail**.  
- Bulk / IAM / prod config: ship preview **first**; hide commit until preview exists.

Nondeterministic externals (seat maps, inventory): preview is a **reservation-shaped estimate**; commit may still fail — surface that as a first-class error, not a silent partial write.

---

## Alternatives & Tradeoffs

### Idempotency

| Technique | Pros | Cons |
|-----------|------|------|
| Native API keys (Stripe) | Correctness at source | Not all APIs support it |
| Caller-side dedupe store | Works in front of legacy | You operate TTL/clocks; must match Stripe-like semantics |
| Natural idempotency (PUT by id, upsert) | Simple | Not always available (`POST /charges`) |
| Read-before-write / read-back | Detects silent success/failure | Races under concurrency |
| Exactly-once queues | Strong for async | Heavy; **handler** still needs idempotency |

### Confirmation

| Gate style | Pros | Cons |
|------------|------|------|
| Structural propose/commit | Cannot bypass in-loop | More tools; token security |
| LangGraph `interrupt` | Durable; kill-safe | Framework-specific; node replay |
| Policy engine under thresholds | Scales | Threshold tuning; still audit |
| Dual control | High assurance | Slow |
| Prompt-only confirm | Cheap | Bypassable |
| Anomaly detection after the fact | Fast | Reactive; money already moved |

### Dry-run

| Approach | Pros | Cons |
|----------|------|------|
| Dedicated `*_preview` tools | Hard to mix up | Tool count doubles |
| `dry_run` boolean | Single tool | Model may set `false` too early unless wrapper forbids |
| Staging clone | Highest fidelity | Cost; drift |
| Deferred execution queue | Soft undo | Not a true preview |

---

## Necessity

**Without idempotency:** every timeout is a potential **duplicate booking, charge, ticket, or email**. Checkpointed long-running agents (Week 13) make this **near-certain** at scale. Stripe exists as an industry template because payments learned this the expensive way.

**Without gates:** runaway loops charge cards, grant admin, or mass-email. Post-incident “the model shouldn’t have…” is not a control. LangGraph `interrupt_after` a send is theater — the mail is gone.

**Without preview:** HITL rubber-stamps vague natural language (“refund the user”); bulk updates surprise operators; multi-step agents discover blockers only after **partial** mutation.

The three controls **compose**: preview fills the interrupt payload; interrupt (or token) authorizes commit; commit uses the **same** idempotency key on retry; audit records all three stages.

---

## Industry Practice

**Common:** UUID from the LLM; chat “YES”; one `refund` tool; no replay tests.

**Senior**

- Wrapper-owned keys; tests: timeout, replay, param mismatch, key TTL.  
- Monitor **dedupe hit rate** (retries working) vs **collision / mismatch errors** (bugs).  
- Risk-tier: only irreversible / high-value require human gates; small refunds policy-auto with an id.  
- Tokens not in LLM context if possible (orchestrator holds them); never log raw tokens.  
- Dry-run results shown **verbatim** in the approval UI.  
- Combine commit with idempotency so double-approve is safe.  
- A2A: document whether the **remote** requires its own HITL (`input_required`) in addition to the client’s.  
- Stripe: don’t put PII in keys; don’t send keys on GET.

---

## Concrete Scenario

**Stripe — retry customer create:**

```http
POST /v1/customers
Idempotency-Key: KG5LxwFBepaKHyUD
```

First request creates `cus_…`. Connection error. Retry **same key** → same customer, not two. Docs: https://docs.stripe.com/api/idempotent_requests  

**LangGraph — $500 transfer gate:** `interrupt` with action details; `Command(resume=True|False)` → `proceed` / `cancel` nodes; write only on proceed. https://docs.langchain.com/oss/python/langgraph/interrupts  

**Syllabus refund:** `preview_refund(pay_123)` → `{amount_cents: 5000, already_refunded: false}` → interrupt → `commit_refund` with wrapper key `sha256(acme|refund.create|pay_123|task_abc)` → kill after HTTP send → retry → one `re_456`. Second commit with **different amount** and **same key** must **error** (Stripe mismatch rule) — forces a new intent id for partials.

**A2A healthcare trailer** (delegation, then apply this envelope on the specialist that actually writes): https://www.youtube.com/watch?v=4gYm0Rp7VHc  

**Chase** (reversible actions + inbox of approvals): https://www.youtube.com/watch?v=kTnfJszFxCg  

---

## Open Questions

- Standard header / metadata field in A2A `Send Message` for idempotency keys?  
- Cross-agent dedupe: should the remote **trust** client-supplied keys or namespace them (`clientId + key`)?  
- Can another **agent** be a confirmer, or must the confirmer be human for regulated domains?  
- Gate A2A-delegated side effects at client, remote, or both?  
- Should Agent Cards advertise `preview` as a capability/skill modality?  
- How to dry-run actions that depend on nondeterministic external systems (inventory, fraud scores)?  
- Stripe caches 500s on a key — should agent wrappers copy that, or allow retry on 5xx with the same key only when the server is known not to have executed?

---

## Sources

- https://docs.stripe.com/api/idempotent_requests  
- https://docs.langchain.com/oss/python/langgraph/interrupts  
- https://docs.langchain.com/oss/python/langgraph/persistence  
- https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://a2a-protocol.org/latest/specification/  
- https://a2a-protocol.org/latest/topics/key-concepts/  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://www.youtube.com/watch?v=4gYm0Rp7VHc  
