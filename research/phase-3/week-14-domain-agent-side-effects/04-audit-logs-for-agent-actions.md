# 04 — Audit logs for agent actions

> Week 14 — Append-only record of attempted side effects  
> Research notes (raw). Traces help debug; **audit** answers “what changed in the ledger?”

---

## Fundamentals

An **audit log** for side-effecting agents is an **append-only, correlatable** record of who/what attempted which mutation, with what arguments, under which policy/approval, and with what **outcome**. Chat transcripts and LangSmith/Langfuse traces are **necessary but not sufficient**: they optimize for LLM spans; compliance and payments ops ask *whether money moved* and *who approved it*.

Week 13 already notes: checkpoint blobs are **not** a signed approval log unless you add one ([Week 13 overview](../week-13-orchestration-multi-agent/00-week-overview.md) open questions). Build that log **this week**.

### Minimum fields (converge across payments + agent write-ups)

| Field group | Examples |
|-------------|----------|
| **Actor** | user id, agent id, model + version, harness version, tenant |
| **Causation** | conversation / session id, LangGraph `thread_id` + checkpoint id, A2A `taskId` + `contextId`, parent span / trace id |
| **Action** | tool name, **redacted** params, idempotency key, dry-run vs commit |
| **Decision** | policy result, approval id, approver subject (human or `policy:threshold`) |
| **Result** | success/failure, HTTP/status, **downstream ids** (`re_456`, ticket id), read-back snapshot hash or safe fields |
| **Time** | synced timestamps (`intent_at`, `commit_at`); monotonic attempt n |

Cover **attempts, retries, compensations, propose / approve / commit, A2A hop boundaries**. A retry that hit Stripe dedupe should log `dedupe_hit=true` with the **same** downstream id — that is how you prove control 03 worked.

### Intent-before-execute

Write the **intent** record **before** calling the mutating API (crash between intent and result is detectable). Write the **result** after (including failures). If the process dies after Stripe succeeded but before result log, **read-back + idempotent retry** heals; the next intent with the same key should reconcile.

Do **not** log secrets, raw confirmation tokens, full PANs, or unconstrained PII in args. Hash or tokenize. Stripe: don’t put PII in idempotency keys either ([Idempotent requests](https://docs.stripe.com/api/idempotent_requests)).

### Observability layers (do not confuse them)

| Layer | Job | Limit |
|-------|-----|--------|
| **App stdout** | Dev | Not immutable; weak queries |
| **OTel traces** | Latency, parent/child, `execute_tool` spans | Retention; content capture often off for privacy |
| **LLM platforms** (LangSmith, Langfuse) | Prompt/tool DX; datasets from traces | May not meet ledger retention; export for compliance |
| **Immutable audit / SIEM / ledger table** | “Did the refund happen?” | Heavier; this is the **source of truth** for writes |

OpenTelemetry **GenAI semantic conventions** (repo moved to the GenAI conventions project; still referenced from [opentelemetry.io GenAI spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/)):

- LLM client spans: `gen_ai.operation.name`, model, tokens.  
- **`execute_tool`** — span name `execute_tool {gen_ai.tool.name}`; `gen_ai.tool.call.id`, `gen_ai.tool.name`; arguments/results **only if privacy policy allows**.  
- **`invoke_agent`** — `invoke_agent {gen_ai.agent.name}`; `CLIENT` when the agent is **remote** (A2A / Bedrock Agents), `INTERNAL` when in-process.

Propagate W3C `traceparent` across A2A HTTP so the remote `execute_tool` is a child of the client’s `invoke_agent`. Conventions do **not** replace a ledger: they do not define “refund succeeded in Stripe.” Put `payment.refund.id` on **your** audit row; optionally duplicate a **safe** subset as OTel attributes.

Langfuse documents a loop from **production traces → eval datasets** ([Langfuse agent evaluation](https://langfuse.com/resources/engineering/ai-agent-evaluation)). Use failing **audit** events as the sampling frame for Week 15 (writes that claimed success, outcome false).

Anthropic: a **transcript** is the messages array; the **outcome** is environment state ([Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)). Audit is how production stores that pair: transcript pointer + outcome snapshot.

### A2A and authority

When a Task crosses vendors, **both** sides should log. The **system of record** (payments API owner) is authoritative for “did money move.” The **client** is authoritative for “did our user approve.” Join on `taskId` + idempotency key. Neither log alone answers both questions.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| Chat / transcript only | Already have it | No ledger; PII-heavy; model lies |
| Trace platform only | Great DX | Retention/compliance; not signed |
| SQL append-only `agent_audit` table | Queryable; cheap start | Need tamper story later (WORM, hash chain) |
| SIEM / immutable object store | Compliance-grade | Ops cost |
| Checkpoint-as-audit | Free with LangGraph | Not signed; contains extra state; replay confusion |
| Log **after** success only | Less noise | Lost intents on crash; cannot reconcile |

Tradeoff: full tool-arg payloads explode cost and leak PII. Store **hashes + allowlisted fields** (amount, currency, object ids) and keep raw args in a **short-TTL** debug sink.

---

## Necessity

Without action audit:

- Cannot answer “did the payment go through?” when the model said yes.  
- Cannot debug duplicate writes vs successful dedupe.  
- Cannot satisfy SOC2 / payments / healthcare reviewers who ask for **approver + object id**.  
- Cannot build Week 15 datasets from **real** write failures.  
- A2A blame games: each vendor’s chat log disagrees.

---

## Industry Practice

**Common:** `print(tool_args)`; LangSmith for demos; no intent line; tokens in plaintext.

**Senior**

- Intent before side effect; result after; **reconcile job** for orphan intents.  
- Separate events: `preview`, `propose`, `approve`, `commit`, `dedupe_hit`, `compensate`.  
- Redact tokens, secrets, PII; never log Stripe secret keys.  
- Correlation: `thread_id` + `taskId` + `idempotency_key` on every write event.  
- OTel `execute_tool` **plus** ledger row; don’t pick one.  
- Feed failing production traces **and** audit mismatches into eval datasets (Langfuse loop).  
- Retention: ledger long (legal); prompts short.  
- Tests: assert an audit row exists in the refund pytest; assert retry produces `dedupe_hit` not a second downstream id.

---

## Concrete Scenario

**Refund with timeout (same as files 00 and 03), audit sequence:**

1. `preview` — `payment_id=pay_123`, `amount_cents=5000`  
2. `approve` — `approver=user:ops_18`, `interrupt_id=…`  
3. `intent` — `idempotency_key=abc…`, `trace_id=…`, `task_id=…`  
4. Stripe `POST /v1/refunds` (or local table) — timeout  
5. Retry — Stripe/store returns same `re_456`  
6. `result` — `downstream_id=re_456`, `dedupe_hit=true`, read-back `status=refunded`  

If step 6 were missing after a crash, a reconciler uses the key + Stripe retrieve.

Langfuse production traces → datasets: https://langfuse.com/resources/engineering/ai-agent-evaluation  

LangSmith trajectory evals (Week 15 adjacent): https://docs.langchain.com/langsmith/trajectory-evals  

OTel tool span shape (examples in semantic-conventions-genai): `execute_tool get_weather` + `gen_ai.tool.call.id` — extend with **your** business ids rather than stuffing PANs into `gen_ai.tool.call.arguments`.

A2A Task id as the cross-service join: [Key concepts](https://a2a-protocol.org/latest/topics/key-concepts/).

---

## Open Questions

- Retention vs cost for full tool-arg payloads; legal hold vs debug TTL.  
- Cross-vendor A2A: whose audit log is **authoritative**, and is there a shared export schema?  
- Hash chains / WORM vs “Postgres append-only + IAM” for first production.  
- Should confirmation tokens be **blinded** in traces even at debug level?  
- Standard OTel attributes for A2A `taskId` (today: custom `app.a2a.task_id` until a spec exists)?  
- Can checkpoint history (`get_state_history`) be a **derived** view of audit, or must they stay separate?

---

## Sources

- https://docs.stripe.com/api/idempotent_requests  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://a2a-protocol.org/latest/topics/key-concepts/  
- https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/  
- https://github.com/open-telemetry/semantic-conventions-genai  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://docs.langchain.com/langsmith/trajectory-evals  
- https://docs.langchain.com/oss/python/langgraph/interrupts  
- https://docs.langchain.com/oss/python/langgraph/checkpointers  
