# 02 — Designing agents with real external side effects

> Week 14 — Actions that mutate systems of record  
> Research notes (raw).

---

## Fundamentals

A **side-effecting agent** does more than answer questions: it **takes actions** that change external state — create/update/delete records, file tickets, send messages, charge or refund cards, book resources, mutate CRMs/ERPs.

Anthropic frames agents as systems where the LLM dynamically directs tool use and must obtain **environmental ground truth** each step. Customer support is called out because actions (refunds, ticket updates) are programmatic and success is measurable. Coding agents similarly get ground truth from tests. Computer-use agents mutate a desktop. All three are **write-capable**; the difference is the blast radius ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

**ACI (agent–computer interface).** Anthropic: invest in tool design the way you invest in HCI — names, parameters, poka-yoke (hard-to-misuse shapes). They spent more time on tools than on the outer prompt for SWE-bench (absolute paths vs relative). Side-effect design **is** ACI design, not a system prompt that says “be careful.”

### Transcript vs outcome (design, not only eval)

From [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents):

- **Transcript** — messages, tool calls, reasoning.  
- **Outcome** — whether the **environment** is correct (SQL reservation exists), not whether the model *claimed* success.  
- **Harness** — the scaffold *and* the model are evaluated together. A beautiful transcript with a failed DB write is a harness bug as much as a model bug.

τ-bench (Sierra) grades **final answer and resulting database state** under policy constraints in retail/airline domains ([tau-bench](https://github.com/sierra-research/tau-bench)). Anthropic notes Opus 4.5 found a **policy loophole** on a τ²-bench flight task — “failed” the written eval but was better for the user. That is a reminder: outcome checkers must encode **policy**, not only “row exists.”

### Classify actions before you expose them

| Class | Examples | Default control |
|-------|----------|-----------------|
| **Read** | get payment, search docs, list events | Allow in-loop; still log |
| **Compensable write** | create draft ticket, hold inventory with TTL | Idempotency + audit; compensation path |
| **Pivot / update** | change ticket status, reschedule | Idempotency; often preview |
| **Irreversible / high-blast** | charge, refund, send customer email, `DROP`, grant admin | Preview + **confirmation gate** + audit + read-back |
| **Bulk** | CSV update 10k rows | Dry-run mandatory; chunk; budget |

Chase’s AI Engineer talk: **lower cost if wrong** via reversible actions and human inboxes ([YouTube](https://www.youtube.com/watch?v=kTnfJszFxCg)). If the action cannot be made reversible, it must be **gated**.

### Envelope around every write tool

1. Classify irreversibility (table above).  
2. **Idempotency** so retries do not double-apply (file 03).  
3. **Confirmation** for high-risk ops (file 03; Week 13 `interrupt`).  
4. **Dry-run / preview** to validate plans (file 03).  
5. **Audit** correlating agent, user, task, args, result (file 04).  
6. **Read-back** after writes — outcome is the store, not the tool’s JSON claim if they can diverge.  
7. **Stop conditions** (Week 11): max turns, spend caps, so loops cannot hammer write APIs.  
8. **Sandbox** for development: production-*shaped* APIs with resettable fixtures (Anthropic: extensive testing in sandboxes when agents write).

### Workflows vs agents for writes

Anthropic split ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)):

- **Workflows** — predetermined code paths (prompt chaining, routing, orchestrator–workers). **Gates** can sit on intermediate steps.  
- **Agents** — model directs the loop.

For **money and access**, put the **write SOP in a workflow** (or a graph node sequence) and let the agent own **conversation + lookup**. Open-ended `while` loops that can call `refund` any turn are how you get compounding errors.

Prompt chaining’s explicit **gate** on intermediate steps is the ancestor of Week 14 confirmation: a programmatic check, not a polite request in the system prompt.

---

## Alternatives & Tradeoffs

| Pattern | When | Tradeoff |
|---------|------|----------|
| **Agent proposes text only; human executes** | Highest risk / early product | Safe; loses automation |
| **Workflow (fixed path) with agent only in slots** | Stable SOPs (refund, KYC) | Predictable; less flexible |
| **Fully autonomous writes** | Low-risk, sandboxed, high trust | Speed; duplicate side effects |
| **Propose → confirm → commit** | Money, access, irreversible comms | Latency; UX friction |
| **Dry-run then execute** | Multi-step plans, bulk | Extra tool surface; need parity |
| **Deferred / buffered send** | Email, webhooks | Softens irreversibility; not undo |
| **Saga + compensation** | Multi-system transactions | Compensation can fail |
| **A2A-delegate the write specialist** | Cross-team bounded context | Network + dual audit; still need local envelope |

Tradeoff: **too much** autonomy on writes fails security review. **Too little** (human types every refund) fails the FDE value prop. The syllabus default is **workflow + gate + one specialist**.

---

## Necessity

Skipping the envelope yields production failures that FDE interviews expect you to name:

- **Double charge / double refund** after timeout + agent retry.  
- Agent reports “done” while **DB write failed** (transcript ≠ outcome).  
- Infinite tool loop spamming create APIs (Week 11 stop conditions missing).  
- Unauthorized mutation (identity/policy skipped because it was “in the prompt”).  
- Cross-agent A2A delegation amplifies blast radius without shared IDs.  
- Irreversible email/Slack sent mid-plan before later steps validate.  
- τ-bench-style **policy** violations: refund issued against the wrong policy branch while the model sounds compliant.

These are **harness** bugs. Changing the model does not fix missing idempotency.

---

## Industry Practice

**Common**

- Separate read tools from write tools (good start) but same auth.  
- Human approval via chat (“Reply YES”) with no token.  
- LangSmith/Langfuse traces of *tokens*, not of *ledger events*.  
- Staging that is not production-shaped (no idempotency headers).

**Strong / senior**

- Risk tags on tools: `AUTO` / `LOG` / `REQUIRE_APPROVAL`.  
- **Idempotency keys** on all non-idempotent POSTs (Stripe as template).  
- Structural consent: propose returns single-use token; commit consumes it.  
- Intent log **before** execution; result log after; IDs across sub-agents / A2A.  
- Dry-run skill used to build the HITL payload.  
- Post-write **read-back** as source of truth.  
- Eval harnesses that grade **environment state** (even a 5-case pytest this week).  
- Sandboxed staging with resettable fixtures; production writes behind flags.  
- Tool docs written as ACI (Anthropic Appendix 2): when **not** to call, absolute identifiers, no ambiguous twins (`delete_user` vs `delete_user_dry_run`).

Google A2A auto-repair narrative: the **parts order** is a side-effecting A2A conversation with a supplier agent — the Mechanic still uses MCP for the lift. Side effects can live **behind** an opaque peer; your client still needs confirmation policy for “place order.”

---

## Concrete Scenario

**Customer support agent issuing refunds** (Anthropic): conversational agent with tools to verify identity, process refund, send confirmation. Success = ticket resolved **and** refund row processed — not “I refunded you” text.

- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- Support domain motivation: https://www.anthropic.com/engineering/building-effective-agents  

**τ-bench:** retail/airline tool-agent-user; grades answer **and** DB under policy: https://github.com/sierra-research/tau-bench  

**Stripe:** retry customer creation without two customers: https://docs.stripe.com/api/idempotent_requests  

**LangGraph $500 transfer** approve/reject (harness for the gate, not the payments ledger): https://docs.langchain.com/oss/python/langgraph/interrupts  

**Chase** on reversible actions + agent inbox: https://www.youtube.com/watch?v=kTnfJszFxCg  

---

## Open Questions

- Who owns generation of idempotency keys — LLM, tool wrapper, or orchestrator? (Consensus from Stripe + agent write-ups: **deterministic wrapper**, never the model.)  
- How to expose dry-run over A2A without doubling the skill surface?  
- Compensating actions when the LLM “succeeds” on the **wrong semantic** (wrong customer ID, valid HTTP 200).  
- Should write tools be **withheld** from the model until after preview (dynamic tool availability) vs always visible with a `dry_run` flag?  
- Usage-based pricing on “successful resolutions” (Anthropic customer-support note) — how to define success if outcome and transcript disagree?

---

## Sources

- https://www.anthropic.com/engineering/building-effective-agents  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://github.com/sierra-research/tau-bench  
- https://docs.stripe.com/api/idempotent_requests  
- https://docs.langchain.com/oss/python/langgraph/interrupts  
- https://a2a-protocol.org/latest/topics/a2a-and-mcp/  
- https://ai.engineer/talks/3-ingredients-for-building-reliable-enterprise-agents  
- https://www.youtube.com/watch?v=kTnfJszFxCg  
