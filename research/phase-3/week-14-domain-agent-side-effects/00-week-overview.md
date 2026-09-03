# 00 — Week overview & syllabus mapping

> Week 14 — Small second agentic system with genuine side effects  
> Research notes (raw). Phase 3 week after graph orchestration / HITL (Week 13).

---

## Fundamentals

Week 14 is the **action** week of Phase 3. Week 11 taught the **loop**. Week 12 taught how tools **show up at a host**. Week 13 taught how work **pauses and resumes** on a durable `thread_id`. This week does **not** replace those. It is the first time the syllabus *requires* the environment to **change**: a refund row, a ticket, a calendar event, a CRM update.

Anthropic’s production pattern for agents: the model directs tool use while gaining **ground truth from the environment** each step; customer support is the canonical domain because **issuing refunds and updating tickets** are programmatic and success is measurable ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), Appendix 1). The same post warns: autonomy means **compounding errors**; sandbox + guardrails when agents write.

**Transcript ≠ outcome.** Anthropic’s eval vocabulary (use it as a *design* vocabulary this week, even though scoring is Week 15):

| Term | Meaning |
|------|---------|
| **Transcript / trajectory** | What the agent said and which tools it called |
| **Outcome** | Final **environment** state (reservation row in SQL, refund object in Stripe) |

An agent that says “Your refund is processed” while the payments table is unchanged **failed**, regardless of fluent text ([Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

### Four controls (teach as a set)

| Control | Job | This week’s file |
|---------|-----|------------------|
| **Idempotency** | Timeouts, checkpoint replay, user retries do not double-write | [03](03-idempotency-confirmation-dry-run.md) |
| **Confirmation gate** | Irreversible / high-value work cannot execute without a structural approve | [03](03-idempotency-confirmation-dry-run.md) + Week 13 `interrupt` |
| **Dry-run / preview** | HITL and the model see *what would happen* before mutate | [03](03-idempotency-confirmation-dry-run.md) |
| **Audit log** | Who/what attempted which write, with which key, with what result | [04](04-audit-logs-for-agent-actions.md) |

A2A is **orthogonal**: it is how a **peer agent** (different framework/vendor/process) receives the work. A2A does **not** make writes safe. Pair them: propagate `taskId` / `contextId` into idempotency keys and audit records ([A2A key concepts](https://a2a-protocol.org/latest/topics/key-concepts/)).

### MCP vs A2A (do not conflate)

Official A2A site ([What is A2A](https://a2a-protocol.org/latest/)):

- **MCP** = agent-to-**tool** (equip one agent with APIs/resources).  
- **A2A** = agent-to-**agent** (opaque peers: discover, delegate tasks, share artifacts) **without** sharing memory, tools, or proprietary logic.

A2A is **not** an SDK, **not** a sub-agent protocol, **not** Slack. LangGraph / CrewAI / ADK remain the *build* layer; A2A is the *interop* layer at agent boundaries.

### Syllabus artifact: a small second system that writes

**What you ship:** one bounded agent (or graph) whose **success criterion is a mutated store**, plus the four controls. It can be a sibling of the Week 11–13 app (recommended) rather than a rewrite.

**Recommended write:** `issue_refund` against a local SQLite/Postgres **payments** table **or** Stripe test-mode `Refunds` API **or** `calendar_create_event` (Week 11 write tool, now fully wrapped).

Sketch of the **write SOP** (workflow in code; agent only in lookup/conversation):

```
START → identify customer / object (read tools)
           ↓
        preview_refund  (no mutation; returns affected row + amount)
           ↓
        interrupt / propose token   ← Week 13 harness OR tokenized gate
           ↓ Command(resume=approve) / commit(token)
        commit_refund(idempotency_key=…)
           ↓
        read_back_refund
           ↓
        audit intent+result already written
          END
```

Illustrative wrapper (keys **not** from the model):

```python
import hashlib
import uuid
from typing import TypedDict

class RefundPreview(TypedDict):
    payment_id: str
    amount_cents: int
    currency: str
    customer_id: str
    already_refunded: bool

def idempotency_key(*, tenant: str, payment_id: str, intent: str, task_id: str) -> str:
    # Wrapper-owned. Stable across retries. Not LLM text.
    raw = f"{tenant}:{intent}:{payment_id}:{task_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]

def preview_refund(payment_id: str) -> RefundPreview:
    row = db.get_payment(payment_id)  # read-only
    return {
        "payment_id": payment_id,
        "amount_cents": row.amount_cents,
        "currency": row.currency,
        "customer_id": row.customer_id,
        "already_refunded": row.refund_id is not None,
    }

def commit_refund(*, payment_id: str, amount_cents: int, key: str, approval_id: str) -> dict:
    audit.emit_intent(
        action="refund.commit",
        payment_id=payment_id,
        amount_cents=amount_cents,
        idempotency_key=key,
        approval_id=approval_id,
    )
    result = payments.refund(  # Stripe-like: same key → same result
        payment_id=payment_id,
        amount=amount_cents,
        idempotency_key=key,
    )
    snapshot = db.get_payment(payment_id)  # read-back is source of truth
    audit.emit_result(action="refund.commit", downstream_id=result.id, snapshot=snapshot)
    return {"refund_id": result.id, "status": snapshot.status}
```

If you add A2A: the **refund specialist** is an A2A Server. Client fetches `/.well-known/agent-card.json`, `Send Message` → `Task`, poll `Get Task` or stream SSE. The remote agent still uses MCP (or local functions) for Stripe/SQL. Client never receives the specialist’s tools or prompts ([A2A and MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)).

Harrison Chase (LangChain) at AI Engineer: raise **value if right** and **P(success)**; **lower cost if wrong** via reversible actions and human correction ([talk](https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents), [YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg)). Week 13 implemented the pause. Week 14 implements **reversibility machinery** (idempotency, preview, compensation-aware design) so a wrong write is cheap or blocked.

### What “done” looks like

1. A user-visible write happens **once** (row / Stripe object / event id).  
2. Kill the process after timeout; retry with the **same** key → **same** object, not two.  
3. Reject / `Command(resume=False)` → **zero** writes.  
4. Preview numbers match commit (or documented drift).  
5. Audit can answer: who approved, which key, which downstream id.  
6. Optional: `curl` the Agent Card; a second process completes the Task.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| **Workflow SOP + gated commit** (syllabus) | Predictable writes; easy tests | Less “autonomous magic” |
| **Fully autonomous writes** | Speed | Duplicate charges; silent failures |
| **Human executes; agent only drafts** | Max safety | No automation ROI |
| **Treat remote agent as MCP tool** | Familiar function-call UX | Lose Task lifecycle, artifacts, discovery |
| **A2A for same-process specialists** | Protocol practice | Extra hop; usually overkill vs Week 13 handoff |
| **Saga + compensation** | Multi-system “undo” | Compensation can fail; still need idempotency |
| **Deferred send window** | Soft undo for email | Not true preview; user already “sent” in UX |

Anthropic: prefer the **simplest** system that works; add agent autonomy only when fixed workflows fail ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)). For **money movement**, a workflow with an agent in the lookup slot is usually the right split.

---

## Necessity

If Week 14 is still a chatbot:

- FDE interviews ask *how you prevent double refunds after a 504*. Prompt hope is a fail.  
- Week 13 node replay **will** re-enter code before `interrupt` — writes before the pause duplicate.  
- Cross-team “just POST to their agent” without task IDs duplicates work and has no audit spine.  
- τ-bench / support evals exist because **policy + DB state** matter, not fluent closings ([τ-bench](https://github.com/sierra-research/tau-bench); Anthropic cites τ²-bench loopholes in [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

---

## Industry Practice

- **Common:** one `refund` tool; LLM invents keys; `input()` confirmation; logs of chat only; A2A slide with no Agent Card.  
- **Senior:** read/write split; wrapper keys bound to `thread_id` / A2A `taskId`; Stripe (or equivalent) native keys; preview tools with poka-yoke names; structural gates; intent log before execute; post-write read-back; staging fixtures that reset; Agent Card as a **product contract** (skills, auth, streaming flags).

Google announced A2A 2025-04-09 as complementary to MCP, later donated to the Linux Foundation ([Google Developers Blog](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/); [Linux Foundation](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)). DeepLearning.AI + Google Cloud + IBM Research course walks a **healthcare** multi-agent demo (insurance / research / doctor-matching as A2A servers) — [course](https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction), trailer [YouTube `4gYm0Rp7VHc`](https://www.youtube.com/watch?v=4gYm0Rp7VHc). Protocol intro [YouTube `Fbr_Solax1w`](https://www.youtube.com/watch?v=Fbr_Solax1w).

---

## Concrete Scenario

**Support agent issues a $50 refund once.**

1. Agent looks up payment `pay_123` (read).  
2. `preview_refund` returns `{amount_cents: 5000, customer_id, already_refunded: false}`.  
3. Graph `interrupt` shows that payload (Week 13). Human approves.  
4. `commit_refund` with key `sha256(tenant|refund|pay_123|task_abc)`. Stripe-shaped store records first response.  
5. HTTP timeout; harness retries; store returns **same** `re_456`. Payments table has **one** refund.  
6. Read-back: `status=refunded`, `refund_id=re_456`. Audit lines: intent, approve, commit, result.

Stripe’s own example: retry `POST /v1/customers` with `Idempotency-Key` without creating two customers ([Idempotent requests](https://docs.stripe.com/api/idempotent_requests)).

A2A scenario (optional extra): client orchestrator delegates “process refund for order 991” to a **LangGraph** refund agent wrapped as A2A; insurance/health narrative in the DLAI course ([goo.gle/dlai-a2a](https://goo.gle/dlai-a2a)).

---

## Open Questions

- Who generates idempotency keys when A2A client and server both retry — client key in metadata, server key, or both concatenated?  
- Should Agent Cards advertise `preview` / `dryRun` as first-class skills?  
- When is in-process Week 13 handoff enough vs A2A (same team vs cross-vendor)?  
- Soft-reversibility windows vs true confirmation — UX research still thin.  
- Cross-vendor audit: whose log is authoritative for a delegated Task?

---

## Sources

- https://a2a-protocol.org/latest/  
- https://a2a-protocol.org/latest/topics/key-concepts/  
- https://a2a-protocol.org/latest/topics/a2a-and-mcp/  
- https://a2a-protocol.org/latest/specification/  
- https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/  
- https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://docs.stripe.com/api/idempotent_requests  
- https://docs.langchain.com/oss/python/langgraph/interrupts  
- https://github.com/sierra-research/tau-bench  
- https://www.youtube.com/watch?v=Fbr_Solax1w  
- https://www.youtube.com/watch?v=4gYm0Rp7VHc  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction  
