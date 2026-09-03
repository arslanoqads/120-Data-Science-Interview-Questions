# Week 14 — Domain Agents & Side Effects (A2A, Actions, Safety Controls)

> Raw source material for agent evaluation curricula and side-effecting agent design.  
> Legal / public sources only. Not a textbook — research dump with citations for later synthesis.  
> Gathered: 2026-09-03

---

## Concept A — Agent-to-Agent (A2A) delegation across frameworks

### 1. Fundamentals

**Agent2Agent (A2A)** is an open protocol for communication and interoperability between **opaque** agentic applications built on different frameworks/vendors. It is **not** an agent SDK and **not** a tool-calling protocol.

Core idea (from official docs):

- **MCP** = agent-to-**tool** (equip one agent with tools/APIs/resources).
- **A2A** = agent-to-**agent** (discover peers, delegate tasks, share results) without sharing internal memory, tools, or proprietary logic.

**Core actors**

| Actor | Role |
|-------|------|
| User | Human or automated service that defines the goal |
| A2A Client (Client Agent) | Initiates A2A communication on behalf of the user |
| A2A Server (Remote Agent) | HTTP endpoint implementing A2A; treated as a black box by the client |

**Fundamental elements**

| Element | Purpose |
|---------|---------|
| **Agent Card** | JSON “business card”: identity, skills, endpoint URL, capabilities (streaming, pushNotifications), auth requirements |
| **Task** | Stateful unit of work with unique ID and lifecycle; tracks long-running / multi-turn work |
| **Message** | One turn of communication (`user` or `agent` role) |
| **Part** | Content container: text, file (URL/bytes), or structured data |
| **Artifact** | Tangible task output (document, image, structured result) |

**Interaction modes**

1. Request/response + **polling** (`Get Task`) for long work  
2. **Streaming** (SSE / binding-specific streams) for incremental status/artifacts  
3. **Push notifications** (client webhook) for disconnected / very long tasks  

**Operations (binding-independent)** include Send Message, Send Streaming Message, Get Task, Cancel Task, and push-notification config CRUD. Transport bindings include JSON-RPC over HTTP(S), gRPC, and HTTP+JSON/REST. Normative data model is Protocol Buffers (`spec/a2a.proto`).

**Governance:** Originally developed by Google; donated to the **Linux Foundation**; TSC includes AWS, Cisco, Google, IBM Research, Microsoft, Salesforce, SAP, ServiceNow. Apache 2.0.

**Complementarity with multi-agent frameworks:** LangGraph, CrewAI, ADK, Semantic Kernel, BeeAI, etc. remain the *build* layer; A2A is the *interop* layer at agent boundaries. Framework-native handoffs are fine *inside* one process/trust domain; A2A is for **cross-framework / cross-vendor / cross-service** delegation.

### 2. Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **A2A across services** | Standard discovery (Agent Card), opaque boundaries, streaming/async, multi-vendor | Extra network hop; auth/observability surface; versioning of cards/skills |
| **Framework-native multi-agent** (LangGraph handoffs, CrewAI crews, ADK sub-agents) | Low latency, shared memory optional, simpler local debugging | Lock-in; hard to compose agents from other vendors; weak enterprise boundary |
| **Treat remote agent as “just another tool” (MCP or custom HTTP)** | Familiar tool-call UX | Loses task lifecycle, artifacts, streaming task semantics, agent discovery; conflates tools with peers |
| **Ad-hoc REST between agents** | Full control | Every pair reinventing discovery, auth, async, schemas |
| **Orchestrator-workers without a protocol** (Anthropic pattern) | Simple when all workers are yours | Does not solve cross-org interoperability |

**Design choice:** Use **MCP inside** an agent; use **A2A between** agents. Do not replace MCP with A2A or vice versa.

### 3. Necessity

Without a shared agent protocol (or an equivalent internal standard):

- Cross-team agents cannot discover skills/auth endpoints uniformly.  
- Delegation becomes brittle custom glue (different JSON shapes per framework).  
- Long-running work lacks a shared **task** lifecycle → clients cannot poll/stream/cancel consistently.  
- Security reviews fail: no clear Agent Card surface for auth schemes, no opaque boundary (temptation to share memory/tools).  
- Side effects multiply across agents with no single correlation ID / task ID for audit.

Failure mode example: a “triage” LangGraph agent calls a CrewAI “refund” agent via a one-off HTTP POST; retries create duplicate refunds because neither side shared task IDs or idempotency keys.

### 4. Industry Practice

**Common**

- Prototype multi-agent *inside one framework*.  
- Expose specialists later via A2A servers; publish Agent Cards at well-known URLs.  
- Pair with MCP for tool access inside each specialist.

**Strong / senior**

- Treat Agent Card as a **product contract**: skills, input/output modes, auth, capability flags.  
- Prefer opaque remote agents; never require sharing prompts/tools across org boundaries.  
- Use streaming for UX; push notifications for batch/long jobs; always support `Get Task` fallback.  
- Propagate **task/context IDs** into downstream audit logs and idempotency keys.  
- Evaluate multi-agent A2A systems with trajectory metrics (e.g. Vertex AI `trajectory_exact_match`, `trajectory_precision`, `trajectory_recall` in public Google Cloud material).  
- Train teams via DeepLearning.AI **“A2A: The Agent2Agent Protocol”** (Google Cloud + IBM Research).

### 5. Concrete Scenario (URL)

**Healthcare multi-agent demo (DeepLearning.AI / A2A course narrative):**  
Insurance agent (Claude on Vertex) + health research agent (ADK) + doctor-matching agent (LangGraph), each wrapped as an A2A server; client orchestrates without sharing internals. Course entry: https://goo.gle/dlai-a2a and https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction  

**Protocol home / spec:** https://a2a-protocol.org/latest/ · Specification: https://a2a-protocol.org/latest/specification/  

**GitHub (protocol + SDKs):** https://github.com/a2aproject/A2A (also historically https://github.com/google/A2A)

**YouTube / short intro:** A2A video intro referenced from protocol site (“Video Intro in under 8 min”); course trailer pattern uses YouTube id `4gYm0Rp7VHc` via https://goo.gle/dlai-a2a  

**Google Cloud community walkthrough of concepts (Agent Card, Task, push notifications):** https://discuss.google.dev/t/understanding-a2a-the-protocol-for-agent-collaboration/189103

### 6. Open Questions

- How should **authorization scopes** compose when Agent A delegates to Agent B which calls tools that mutate customer data?  
- Should remote agents expose **dry-run / preview skills** in the Agent Card as first-class capabilities?  
- Versioning: skill IDs vs. Agent Card versions when behavior changes silently.  
- Observability: standard OTel semantic conventions for A2A task spans across vendors?  
- When is A2A overkill vs. in-process handoff for same-team agents?

### 7. Sources

- https://a2a-protocol.org/latest/  
- https://a2a-protocol.org/latest/topics/key-concepts/  
- https://a2a-protocol.org/latest/specification/  
- https://a2a-protocol.org/v1.0.0/specification/  
- https://github.com/a2aproject/A2A  
- https://github.com/google/A2A  
- https://discuss.google.dev/t/understanding-a2a-the-protocol-for-agent-collaboration/189103  
- https://goo.gle/dlai-a2a  
- https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction  
- https://discuss.google.dev/t/end-to-end-evaluation-of-multi-agent-systems-on-vertex-ai-with-cloud-run-deployment-for-a2a-agents/250552  
- https://cloud.google.com/blog/products/ai-machine-learning/introducing-agent-evaluation-in-vertex-ai-gen-ai-evaluation-service  
- https://www.anthropic.com/engineering/building-effective-agents (orchestrator-workers / when to use agents)

---

## Concept B — Designing agents with real external side effects

### 1. Fundamentals

A **side-effecting agent** does more than answer questions: it **takes actions** that change external state — create/update/delete records, file tickets, send messages, charge cards, book resources, mutate CRMs/ERPs.

Anthropic’s “Building effective agents” frames agents as systems where the LLM dynamically directs tool use with **environmental ground truth** each step; customer support is called out as a prime domain because actions (refunds, ticket updates) are programmatic and success is measurable.

**Critical distinction (Anthropic evals language, useful for design):**

- **Transcript / trajectory** — what the agent said and which tools it called.  
- **Outcome** — whether the **environment state** is correct (e.g. reservation row exists in SQL), not merely that the agent claimed success.

Designing for side effects therefore means designing the **tool/ACI envelope**, not only prompts:

1. **Classify actions** by irreversibility (read / compensable write / pivot / irreversible).  
2. **Idempotency** so retries and restarts do not double-apply.  
3. **Confirmation gates (HITL)** for high-risk ops.  
4. **Dry-run / preview** modes to validate plans.  
5. **Audit logs** correlating agent, user, task, tool args, and result.  
6. **Read-back verification** after writes.  
7. **Stop conditions** (max turns, budgets) so loops cannot hammer write APIs.

### 2. Alternatives & Tradeoffs

| Pattern | When | Tradeoff |
|---------|------|----------|
| **Agent proposes text only; human executes** | Highest risk / early product | Safe; loses automation value |
| **Workflow (fixed path) with agent only in slots** | Stable SOPs | Predictable; less flexible than open agents |
| **Fully autonomous writes** | Low-risk, sandboxed, high trust | Speed; compounding errors & duplicate side effects |
| **Propose → confirm → commit** (tokenized gate) | Money, access, irreversible comms | Latency; UX friction |
| **Dry-run then execute** | Multi-step plans, bulk updates | Extra tool surface; must ensure dry-run parity |
| **Deferred / buffered send** (cancel window) | Emails, webhooks | Softens irreversibility; not true undo |
| **Saga + compensation** | Multi-system transactions | Complex; compensation itself can fail |

Anthropic guidance: prefer **simplest** system that works; add agent autonomy only when fixed workflows fail; sandbox + guardrails when agents write.

### 3. Necessity

Skipping side-effect controls yields classic production failures:

- **Double charge / double refund** after timeout + agent retry.  
- Agent reports “done” while **DB write failed** (transcript ≠ outcome).  
- Infinite tool loop spamming create APIs.  
- Unauthorized mutation (skipped identity/policy check).  
- Cross-agent delegation amplifies blast radius without shared audit IDs.  
- Irreversible email/Slack sent mid-plan before later steps validate.

τ-bench / customer-support benchmarks exist precisely because **policy + DB state** matter, not fluent final text.

### 4. Industry Practice

**Common**

- Separate read tools from write tools; stricter auth on writes.  
- Human approval for refunds / deletes / external messages.  
- Basic logging of tool calls in LangSmith/Langfuse.

**Strong / senior**

- **Idempotency keys** on all non-idempotent POSTs (Stripe pattern as industry template).  
- Tool risk tags: `AUTO` / `LOG` / `REQUIRE_APPROVAL`.  
- Structural **consent gates**: propose returns single-use token; commit requires token; no side-effect path without gate.  
- Intent log **before** execution; result log after; correlation across sub-agents.  
- Dry-run skill used to build user-visible plan.  
- Post-write **read-back** as source of truth.  
- Eval harnesses that grade **environment state**, not only assistant text (Anthropic; τ-bench).  
- Sandboxed staging with production-like APIs and resettable fixtures.

### 5. Concrete Scenario (URL)

**Customer support agent issuing refunds** (Anthropic): conversational agent with tools to verify identity, process refund, send confirmation; success = ticket resolved **and** refund row processed — not “I refunded you” text alone.  
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  

**τ-bench (Sierra):** retail/airline tool-agent-user domains; grades final answer **and** resulting database state under policy constraints.  
https://github.com/sierra-research/tau-bench  

**Stripe idempotent API requests** (canonical industry pattern agents should wrap):  
https://docs.stripe.com/api/idempotent_requests  

**Consent / propose-commit gates for dangerous ops** (engineering pattern write-up):  
https://trydock.ai/blog/consent-gates-for-dangerous-ops  

### 6. Open Questions

- Who owns generation of idempotency keys — LLM, tool wrapper, or orchestrator? (Consensus leans: **deterministic wrapper**, never the model.)  
- How to expose dry-run over A2A without doubling skill surface?  
- Soft-reversibility windows vs. true user confirmation — UX research still thin.  
- Compensating actions when the LLM “succeeds” on a wrong semantic (wrong customer ID).  

### 7. Sources

- https://www.anthropic.com/engineering/building-effective-agents  
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents  
- https://github.com/sierra-research/tau-bench  
- https://docs.stripe.com/api/idempotent_requests  
- https://trydock.ai/blog/consent-gates-for-dangerous-ops  
- https://www.pontil.com/blog/api-idempotency-for-ai-agents-a-practical-guide-to-safe  
- https://agentblueprint.substack.com/p/designing-idempotent-write-operations  
- https://pragmaticstack.in/safe-side-effects-agentic-ai  
- https://www.padiso.co/blog/building-idempotent-tools-for-long-running-agents/

---

## Concept C — Idempotency for agent tool calls

### 1. Fundamentals

Agents and harnesses provide **at-least-once** tool execution semantics in practice: network timeouts, checkpoint resume, user retries, and framework restarts re-invoke tools. For non-idempotent writes, that means duplicate side effects unless the **server** (or a durable dedupe layer) coalesces retries.

**Idempotency key pattern (Stripe-style):**

1. Client sends `Idempotency-Key` with POST.  
2. Server stores first response for that key.  
3. Retries with same key + same params return the **same** result.  
4. Same key + different params → error (misuse).  
5. Keys expire after a TTL (Stripe: prune after ≥24h).

For agents specifically:

- Key should be derived from **stable structural context** (user id + intent + business object id + step id / task id) — **not** from free-form LLM text.  
- Tool wrapper performs claim → execute → record atomically.  
- Do not cache transient 5xx as final success; allow true retry.  
- Pair with read-back when the downstream API lacks native idempotency.

### 2. Alternatives & Tradeoffs

| Technique | Pros | Cons |
|-----------|------|------|
| Native API idempotency keys | Correctness at source | Not all APIs support it |
| Caller-side dedupe store | Works in front of legacy APIs | You operate the store; clock/TTL issues |
| Natural idempotency (PUT by ID, upsert) | Simple | Not always available |
| Read-before-write / read-back | Detects silent success/failure | Races under concurrency |
| Exactly-once message queues | Strong for async | Heavy; still need handler idempotency |

### 3. Necessity

Without idempotency: every agent timeout becomes a potential **duplicate booking, charge, ticket, or email**. Checkpointed long-running agents make this near-certain at scale.

### 4. Industry Practice

- Require idempotency keys on all side-effecting tools in the agent runtime.  
- Bind keys to A2A `taskId` / session ids when crossing agents.  
- Monitor dedupe hit rates and key collisions.  
- Test restart/resume scenarios explicitly.

### 5. Concrete Scenario (URL)

Stripe docs — safely retry customer creation without creating two customers:  
https://docs.stripe.com/api/idempotent_requests  

Agent-oriented guide: https://www.pontil.com/blog/api-idempotency-for-ai-agents-a-practical-guide-to-safe  

### 6. Open Questions

- Standard header / field in A2A messages for idempotency keys?  
- Cross-agent dedupe: should remote agent trust client-supplied keys?

### 7. Sources

- https://docs.stripe.com/api/idempotent_requests  
- https://www.pontil.com/blog/api-idempotency-for-ai-agents-a-practical-guide-to-safe  
- https://agentblueprint.substack.com/p/designing-idempotent-write-operations  
- https://www.padiso.co/blog/building-idempotent-tools-for-long-running-agents/

---

## Concept D — Confirmation gates (human-in-the-loop)

### 1. Fundamentals

A **confirmation gate** forces a human (or policy engine) to approve before a dangerous side effect commits. Strong form is **structural**, not prompt-based:

1. Agent calls `propose_*` → returns human-readable summary + **single-use token** (TTL-bound).  
2. UI shows summary; human approves.  
3. Agent calls `commit_*` with token → side effect executes in same transaction as token consume.  
4. Retry after success returns `already_consumed` — must not loop.

Prompt-only “please confirm” without a tokenized commit path can be bypassed by a confused / jailbroken model path.

Anthropic notes agents should pause for human feedback at checkpoints or blockers; support agents often gate refunds/escalations.

### 2. Alternatives & Tradeoffs

| Gate style | Pros | Cons |
|------------|------|------|
| Structural propose/commit | Cannot bypass in-loop | More tools; token security |
| UI interrupt in orchestrator (LangGraph HITL) | Clean graph semantics | Framework-specific |
| Policy engine auto-approve under thresholds | Scales | Threshold tuning risk |
| Dual control (two humans) | High assurance | Slow |
| No gate + anomaly detection | Fast | Reactive only |

### 3. Necessity

Without gates: runaway loops can charge cards, grant admin access, or mass-email. Post-incident “the model shouldn’t have…” is not a control.

### 4. Industry Practice

- Risk-tier tools; only irreversible / high-value require gates.  
- Redact tokens in logs.  
- Audit: separate events for propose, approve, commit.  
- Combine with idempotency on commit.

### 5. Concrete Scenario (URL)

https://trydock.ai/blog/consent-gates-for-dangerous-ops  

Anthropic agent patterns (pause for judgment): https://www.anthropic.com/engineering/building-effective-agents  

### 6. Open Questions

- Can another agent be a “confirmer,” or must confirmer be human for regulated domains?  
- How to gate A2A-delegated side effects — gate at client, remote, or both?

### 7. Sources

- https://trydock.ai/blog/consent-gates-for-dangerous-ops  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://pragmaticstack.in/safe-side-effects-agentic-ai  

---

## Concept E — Dry-run / preview modes

### 1. Fundamentals

A **dry-run** tool returns “what would happen” (diffs, affected rows, cost, recipients) **without** mutating state. Agents can chain dry-runs to validate a plan, then execute — also improves explainability for HITL summaries.

Requirements for usefulness:

- Parity: dry-run predictions must match commit behavior closely.  
- Clear naming so the model cannot confuse `delete_user` with `delete_user_dry_run`.  
- Prefer poka-yoke: separate tools or a mandatory `dry_run: true` default on dangerous tools.

### 2. Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| Dedicated `*_preview` tools | Hard to mix up | Tool count doubles |
| `dry_run` boolean | Single tool | Model may set false too early |
| Staging environment clone | Highest fidelity | Costly; drift |
| Deferred execution queue | Soft undo window | Not a true preview |

### 3. Necessity

Without preview: HITL approves vague natural-language plans; bulk updates surprise operators; multi-step agents discover blockers only after partial mutation.

### 4. Industry Practice

- High-stakes domains (IAM, payments, prod config) ship preview first.  
- Show dry-run artifacts to users before commit.  
- Include dry-run results in audit trail.

### 5. Concrete Scenario (URL)

Safe side-effects guidance emphasizing DryRun/Preview and deferred sends:  
https://pragmaticstack.in/safe-side-effects-agentic-ai  

### 6. Open Questions

- Should Agent Cards advertise `preview` as a capability/skill modality?  
- How to dry-run actions that depend on nondeterministic external systems?

### 7. Sources

- https://pragmaticstack.in/safe-side-effects-agentic-ai  
- https://agentblueprint.substack.com/p/designing-idempotent-write-operations  

---

## Concept F — Audit logs for side-effecting agents

### 1. Fundamentals

An **audit log** is an append-only, correlatable record of who/what attempted which side effect, with what arguments, under which policy decision, and with what outcome. For agents it must cover: attempts, retries, compensations, propose/approve/commit, and A2A delegation boundaries.

Minimum fields (industry write-ups converge):

- Actor: user id, agent id, model/version, harness version  
- Causation: conversation/session id, A2A task id, parent span  
- Action: tool name, params (redacted), idempotency key  
- Decision: policy result, approval id  
- Result: success/failure, downstream ids, read-back snapshot  
- Time: synced timestamps  

OpenTelemetry GenAI semantic conventions + LangSmith/Langfuse are common implementation layers.

### 2. Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| App logs only | Easy | Not immutable; weak queries |
| Trace platform (Langfuse/LangSmith) | Great DX for LLM spans | Retention/compliance may need export |
| Immutable ledger / SIEM | Compliance-grade | Heavier ops |
| Intent-before-execute log | Enables crash recovery | Must not log secrets |

### 3. Necessity

Without audits: cannot answer “did the payment go through?”, cannot debug duplicate writes, cannot satisfy compliance, cannot build eval datasets from real failures.

### 4. Industry Practice

- Log intent before side effect; log result after.  
- Treat logs as both **debugging** and **compliance** substrate.  
- Feed failing production traces into eval datasets (Langfuse loop).  
- Redact tokens, PII, secrets.

### 5. Concrete Scenario (URL)

https://www.padiso.co/blog/building-idempotent-tools-for-long-running-agents/  
https://agentblueprint.substack.com/p/designing-idempotent-write-operations  
Langfuse agent evaluation (production traces → datasets): https://langfuse.com/resources/engineering/ai-agent-evaluation  

### 6. Open Questions

- Retention vs. cost for full tool-arg payloads.  
- Cross-vendor A2A: whose audit log is authoritative?

### 7. Sources

- https://www.padiso.co/blog/building-idempotent-tools-for-long-running-agents/  
- https://agentblueprint.substack.com/p/designing-idempotent-write-operations  
- https://pragmaticstack.in/safe-side-effects-agentic-ai  
- https://langfuse.com/resources/engineering/ai-agent-evaluation  
- https://docs.langchain.com/langsmith/trajectory-evals  

---

## Cross-cutting notes for curriculum authors

1. **A2A ≠ safety.** Interop protocol + side-effect envelope are orthogonal; you need both for multi-vendor action agents.  
2. **Grade outcomes in the environment** when teaching side effects; transcript-only grading hides silent write failures.  
3. **Idempotency, gates, dry-run, audit** are the four practical controls that show up repeatedly in production write-ups; teach them as a set.  
4. Related weeks: Week 12 (MCP tools), Week 13 (orchestration/HITL), Week 15 (evaluating trajectories of these actions), Week 21 (idempotent legacy integration).
