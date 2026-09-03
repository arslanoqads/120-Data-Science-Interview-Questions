# 01 — Agent-to-Agent (A2A) delegation

> Week 14 — Google-originated A2A protocol (Linux Foundation)  
> Research notes (raw). Public spec: https://a2a-protocol.org/latest/specification/

---

## Fundamentals

**Agent2Agent (A2A)** is an **open protocol** for communication and interoperability between **opaque** agentic applications built on different frameworks and vendors. Official “what it is not” list ([A2A home](https://a2a-protocol.org/latest/)):

- **Not** an agent development kit (LangGraph, CrewAI, ADK, Semantic Kernel, BeeAI, …). Those are how you *build*.  
- **Not** a sub-agent or **tool-call** protocol. How an agent talks to *its own* tools is MCP or framework primitives.  
- **Not** a replacement for **MCP**.  
- **Not** an interactive messaging app (Slack / Discord). It is **machine-to-machine**.

**Governance.** Originally developed by Google (announced 2025-04-09, 50+ launch partners) ([Google Developers Blog](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)); donated to the **Linux Foundation** (2025-06-23) ([LF press](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)). TSC includes AWS, Cisco, Google, IBM Research, Microsoft, Salesforce, SAP, ServiceNow. License: **Apache 2.0**. IBM’s **ACP** (BeeAI) merged into A2A; BeeAI now ships A2A adapters ([IBM tutorial](https://www.ibm.com/think/tutorials/use-a2a-protocol-for-ai-agent-communication)).

**Latest released spec version** at deep-pass time: **1.0.0**. Normative data model: Protocol Buffers `spec/a2a.proto` — JSON schema on the website is a **non-normative** build artifact ([Specification](https://a2a-protocol.org/latest/specification/)).

### Core actors ([Key concepts](https://a2a-protocol.org/latest/topics/key-concepts/))

| Actor | Role |
|-------|------|
| **User** | Human or automated service that defines the goal |
| **A2A Client** (client agent) | Initiates A2A on behalf of the user |
| **A2A Server** (remote agent) | HTTP endpoint implementing A2A; **black box** to the client (no internal memory/tools) |

### Fundamental elements

| Element | Purpose |
|---------|---------|
| **Agent Card** | JSON “business card”: identity, skills, endpoint URL, capabilities (`streaming`, `pushNotifications`), auth schemes |
| **Task** | Stateful unit of work with unique ID and **lifecycle**; long-running / multi-turn |
| **Message** | One turn (`role`: `user` or `agent`) with `messageId` |
| **Part** | Content: `text`, file (`url` / inline bytes), or structured `data` + `mediaType` |
| **Artifact** | Tangible task output (document, image, structured result) with `artifactId` |
| **Context** (`contextId`) | Groups related Tasks |
| **Extension** | Declared extra capabilities on the Agent Card |

Discovery of the card ([Agent discovery](https://a2a-protocol.org/latest/topics/agent-discovery/)):

1. **Well-known URI** — `GET https://{domain}/.well-known/agent-card.json` (RFC 8615). Python tutorial serves this via `create_agent_card_routes` ([Start server](https://a2a-protocol.org/latest/tutorials/python/5-start-server/)).  
2. **Curated registries** — enterprise catalogs; spec does **not** mandate a registry API.  
3. **Direct config** — env vars / hardcoded URLs for private pairs.

Protect sensitive cards: authenticated **extended** cards, mTLS, network allowlists, OAuth on the card endpoint. **Do not** embed static secrets in the card; use out-of-band credentials (HTTP headers, not A2A message bodies). Cache with `Cache-Control` / `ETag`.

### Interaction modes

1. **Request/response + polling** — `Send Message` then `Get Task` for long work.  
2. **Streaming** — SSE (or binding-specific streams) of `TaskStatusUpdateEvent` / `TaskArtifactUpdateEvent`. Stream **closes** when the task hits a terminal state.  
3. **Push notifications** — client webhook for disconnected / very long tasks; CRUD for push-config is a first-class operation.

If the agent can answer immediately it MAY return a **Message** instead of a Task. Messages to **terminal** tasks (`COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`) MUST be rejected (`UnsupportedOperationError`).

### Binding-independent operations (Layer 2)

Send Message, Send Streaming Message, Get Task, List Tasks, Cancel Task, Get Agent Card, plus push-notification config. **Layer 3** maps these to JSON-RPC over HTTP(S), **gRPC**, and **HTTP+JSON/REST**. Spec goals: reuse HTTP / JSON-RPC / SSE; enterprise auth/tracing; **async-first**; modality-agnostic; **opaque execution**.

### Complementarity with MCP (official auto-repair example)

Shop Manager ↔ customer and Mechanic ↔ Parts Supplier = **A2A**. Mechanic ↔ diagnostic scanner / repair manual = **MCP**. Do not expose the scanner as a remote *agent* unless it actually reasons over a Task lifecycle ([A2A and MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)).

You **may** expose a well-defined A2A skill in a tool-like way (even as MCP), but you lose multi-turn Task semantics.

### Framework-native vs A2A

Inside **one process / one trust domain**, Week 13 handoffs (`Command`, Swarm, AutoGen topics) are enough. A2A is for **cross-framework, cross-vendor, cross-service** delegation: ADK insurance agent + LangGraph matcher + Claude-on-Vertex specialist, as in the DeepLearning.AI course narrative.

---

## Alternatives & Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **A2A across services** | Standard discovery, opaque boundary, streaming/async, multi-vendor | Extra hop; auth + observability surface; card/skill versioning |
| **Framework-native multi-agent** (LangGraph, CrewAI, ADK sub-agents) | Low latency; optional shared memory; simpler local debug | Lock-in; weak enterprise boundary |
| **Remote agent as “just a tool”** (MCP or ad-hoc HTTP) | Familiar tool UX | No Task lifecycle, artifacts, skill discovery, cancel/stream contract |
| **Ad-hoc REST per pair** | Full control | Every pair reinventing discovery, auth, async |
| **Anthropic orchestrator–workers** (all workers yours) | Simple when you own the fleet | Does not solve cross-org interop |
| **ADK `RemoteA2aAgent`** | Card handshake + JSON-RPC hidden ([Google Developers](https://developers.googleblog.com/en/build-cross-language-multi-agent-team-with-google-agent-development-kit-and-a2a/)) | Still need production auth, idempotency, audit on both sides |

**Design choice:** MCP **inside**; A2A **between**. Treating a peer as a stateless tool is the most common protocol smell.

---

## Necessity

Without a shared agent protocol (or an equivalent **internal** standard):

- Cross-team agents cannot discover skills/auth endpoints uniformly.  
- Delegation is brittle custom JSON per framework.  
- Long-running work lacks a shared **task** lifecycle → no consistent poll/stream/cancel.  
- Security review has no Agent Card surface; temptation to share prompts/tools across orgs.  
- Side effects multiply with **no correlation ID** (`taskId` / `contextId`) for audit and idempotency.

Failure mode: a LangGraph “triage” agent POSTs to a CrewAI “refund” agent; client times out and retries; **two refunds** because neither side shared task IDs or idempotency keys. A2A does not *automatically* fix that — you still implement keys (file 03) — but the Task ID is the natural spine.

---

## Industry Practice

**Common**

- Prototype multi-agent *inside one framework*.  
- Slideware “we’ll use A2A” with no `/.well-known/agent-card.json`.  
- Wrap every microservice as an “agent.”

**Strong / senior**

- Treat the Agent Card as a **product contract**: skill ids, input/output modes, auth, capability flags, version. Cache with ETag.  
- Opaque remotes: never require sharing prompts/tools across org boundaries.  
- Streaming for UX; push for batch; always support `Get Task` fallback.  
- Propagate **task/context IDs** into downstream audit logs and idempotency keys.  
- Auth in **HTTP headers** (OAuth2, mTLS), declared on the card.  
- Evaluate multi-agent A2A systems with **trajectory** metrics when you reach Week 15 (Vertex AI `trajectory_exact_match` / precision / recall appear in public Google Cloud material).  
- Train via DeepLearning.AI **A2A: The Agent2Agent Protocol** (Google Cloud + IBM Research): wrap heterogeneous frameworks as A2A servers, then orchestrate ([course intro](https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction)).

Google Cloud community write-up of Card / Task / push: [discuss.google.dev](https://discuss.google.dev/t/understanding-a2a-the-protocol-for-agent-collaboration/189103). Vertex + Cloud Run A2A eval thread: [discuss.google.dev 250552](https://discuss.google.dev/t/end-to-end-evaluation-of-multi-agent-systems-on-vertex-ai-with-cloud-run-deployment-for-a2a-agents/250552).

---

## Concrete Scenario

**Healthcare multi-agent (DeepLearning.AI / A2A course):** insurance assistant (no framework / Claude on Vertex), health research agent (**ADK**), doctor-matching agent (**LangGraph**), each wrapped as an A2A server. Client orchestrates **without** sharing internals. Sequential ADK workflow first, then BeeAI dynamic handoff; deploy on Agent Stack.

- Course: https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction  
- Short link: https://goo.gle/dlai-a2a  
- Trailer: https://www.youtube.com/watch?v=4gYm0Rp7VHc  

**Protocol intro (Google, ~8 min):** https://www.youtube.com/watch?v=Fbr_Solax1w — Agent Card as business card; HTTPS + JSON-RPC; A2A vs MCP; `pip install a2a-sdk`. Also linked from [a2a-protocol.org](https://a2a-protocol.org/latest/) as “Video Intro in under 8 min.”

**Spec / code:** https://a2a-protocol.org/latest/ · https://a2a-protocol.org/latest/specification/ · https://github.com/a2aproject/A2A (historical https://github.com/google/A2A)

**Cross-language:** Python Gemini extractor + Go policy agent over A2A, orchestrated by ADK `RemoteA2aAgent` ([Google Developers Blog](https://developers.googleblog.com/en/build-cross-language-multi-agent-team-with-google-agent-development-kit-and-a2a/)).

---

## Open Questions

- How should **authorization scopes** compose when Agent A delegates to Agent B which calls mutating tools? (Card declares *server* auth; user-to-agent OAuth is a different hop.)  
- Should remotes expose **dry-run / preview skills** on the Agent Card as first-class capabilities?  
- Skill id vs Agent Card `version` when behavior changes silently.  
- Standard **OTel** semantic conventions for A2A task spans across vendors? (`invoke_agent` exists in GenAI conventions; A2A-specific attributes are still emerging.)  
- When is A2A overkill vs in-process Week 13 handoff for same-team agents?  
- Should the client’s idempotency key be a reserved metadata field on `Send Message`?

---

## Sources

- https://a2a-protocol.org/latest/  
- https://a2a-protocol.org/latest/topics/key-concepts/  
- https://a2a-protocol.org/latest/topics/a2a-and-mcp/  
- https://a2a-protocol.org/latest/topics/agent-discovery/  
- https://a2a-protocol.org/latest/specification/  
- https://a2a-protocol.org/v1.0.0/specification/  
- https://a2a-protocol.org/latest/tutorials/python/5-start-server/  
- https://github.com/a2aproject/A2A  
- https://github.com/google/A2A  
- https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/  
- https://developers.googleblog.com/en/build-cross-language-multi-agent-team-with-google-agent-development-kit-and-a2a/  
- https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai  
- https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents  
- https://discuss.google.dev/t/understanding-a2a-the-protocol-for-agent-collaboration/189103  
- https://discuss.google.dev/t/end-to-end-evaluation-of-multi-agent-systems-on-vertex-ai-with-cloud-run-deployment-for-a2a-agents/250552  
- https://goo.gle/dlai-a2a  
- https://learn.deeplearning.ai/courses/a2a-the-agent2agent-protocol/lesson/vtf72ap4/introduction  
- https://www.ibm.com/think/tutorials/use-a2a-protocol-for-ai-agent-communication  
- https://www.anthropic.com/engineering/building-effective-agents  
- https://www.youtube.com/watch?v=Fbr_Solax1w  
- https://www.youtube.com/watch?v=4gYm0Rp7VHc  
