# Week 12 — Model Context Protocol (MCP)

> Phase 3 — Agentic Systems  
> Raw research notes (not textbook prose). Legal sources only; no pirated books.

---

## Concept: MCP server / client architecture

### Fundamentals
**Model Context Protocol (MCP)** is an open standard for connecting LLM applications to external data and tools — described by Anthropic as a “USB-C port for AI applications” ([What is MCP?](https://modelcontextprotocol.io/docs/getting-started/intro) / Anthropic MCP docs index via https://docs.anthropic.com/en/docs/agents-and-tools/mcp).

Architecture (host–client–server):

- **Host:** the AI application the user interacts with (Claude Desktop, Claude Code, Cursor, ChatGPT, custom apps). Creates and manages clients.
- **Client:** a protocol connector **inside** the host; one stateful session per connected server; handles capability negotiation and message routing.
- **Server:** an independent local process or remote service that exposes **resources**, **tools**, and/or **prompts** over MCP.

Layers ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)):

1. **Data layer** — JSON-RPC 2.0 messages: lifecycle, primitives, notifications.
2. **Transport layer** — how bytes move: **stdio** (local processes) and **Streamable HTTP** / SSE-style remote transports.

**Lifecycle:** `initialize` (exchange protocol version + capabilities) → server result → client `initialized` notification → operational messages (`tools/list`, `tools/call`, `resources/read`, …). Capability negotiation is mandatory: if a server does not advertise `tools`, the client must not call `tools/call` ([Specification architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture/index)).

Servers may also use **client features** (when the client advertises them): **sampling** (ask host LLM to complete), **elicitation** (ask user for input), **roots** (filesystem/URI boundaries).

### Alternatives & Tradeoffs
| Integration style | Pros | Cons |
|-------------------|------|------|
| MCP | Portable across hosts; clear security boundary per server | Spec/SDK churn; auth & remote transport maturity still evolving |
| Provider-native tools only | Deep platform features | Lock-in; reimplement per host |
| Ad-hoc REST + custom function schemas | Full control | N×M connectors (every agent × every API) |
| Plugin SDKs per IDE | Native UX | Not reusable outside that IDE |

Tradeoff: MCP standardizes the **connector**, not agent intelligence — you still design tools and orchestration.

### Necessity
Without a shared protocol, FDE work rebuilds “Jira tool,” “Slack tool,” “SQL tool” for every harness. Hosts that speak MCP can attach the same server to Claude Code today and a custom host tomorrow. Capability negotiation prevents silent feature mismatches.

### Industry Practice
- **Common:** copy a FastMCP “hello” server; stdio only; no auth story.
- **Senior:** declare capabilities accurately; pin protocol version; prefer official SDKs; separate servers by trust boundary (filesystem vs prod DB); for remote: Streamable HTTP + auth; health/logging via protocol utilities; register in org catalogs/registries as they mature.

### Concrete Scenario
Official architecture walkthrough (host creates one client per server; tools/resources/prompts; JSON-RPC data layer + transports): https://modelcontextprotocol.io/docs/learn/architecture  
Specification index (hosts/clients/servers; server vs client features): https://modelcontextprotocol.io/specification/2025-11-25/  
AI Engineer Summit workshop — *Building Agents with Model Context Protocol* (Mahesh Murag, Anthropic): https://youtu.be/kQmXtrmQ5Zg

### Open Questions
- Will remote MCP auth converge on OAuth/OIDC patterns uniformly across hosts?
- How should hosts sandbox local stdio servers (OS permissions, secrets) at enterprise scale?

### Sources
- https://modelcontextprotocol.io/docs/learn/architecture
- https://modelcontextprotocol.io/specification/2025-11-25/
- https://modelcontextprotocol.io/specification/2025-11-25/architecture/index
- https://docs.anthropic.com/en/docs/agents-and-tools/mcp
- https://youtu.be/kQmXtrmQ5Zg

---

## Concept: Exposing tools as an MCP server vs consuming third-party MCP servers

### Fundamentals
Two FDE postures:

**A. You are the server author (expose).**  
Wrap your product’s APIs, databases, or workflows as MCP tools/resources/prompts so any MCP-capable host can use them. Build with official SDKs / FastMCP-style frameworks; implement `tools/list` + `tools/call` (and optionally resources/prompts); choose transport (stdio for local IDE attach; HTTP for shared remote service).

**B. You are the client/host integrator (consume).**  
Point Claude Code / Cursor / Agents SDK / custom host at third-party or vendor MCP servers (GitHub, Slack, internal platform servers). Discovery via config (e.g. `.mcp.json`), marketplace/registry, or programmatic client sessions. Your agent loop then sees those tools as ordinary callable functions after the host bridges MCP ↔ model tool schemas.

Anthropic positions MCP as reducing development time when building or integrating with AI apps ([What is MCP?](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)). OpenAI Agents / Responses ecosystem also documents MCP as a tool source alongside function tools ([OpenAI Agents SDK tools](https://openai.github.io/openai-agents-python/tools/), tool search + MCP defer_loading).

**Complementary protocol:** Google-originated **A2A** (now Linux Foundation) is **agent-to-agent**, not a substitute for MCP. Official framing: use MCP to equip an agent with tools/data; use A2A so agents discover/delegate across frameworks ([A2A Protocol](https://a2a-protocol.org/latest/)).

### Alternatives & Tradeoffs
| Choice | When | Risk |
|--------|------|------|
| Build MCP server for your SaaS | Customers live in many AI hosts | You own security, versioning, SLA of the server |
| Consume vendor MCP | Fast enablement | Supply-chain: malicious or buggy third-party tools |
| Thin MCP over existing REST | Reuse API surface | Leaky abstractions; oversized tool lists |
| Skip MCP; proprietary plugin | One strategic host only | Lock-in |

Tradeoff: exposing everything as tools creates selection problems (Week 11); exposing curated **resources + prompts** can be safer for read-heavy context.

### Necessity
FDEs embedding into customer environments need a **stable integration surface**. Rebuilding connectors per IDE wastes the engagement. Consuming unvetted MCP servers without allowlists is a security incident waiting to happen (tool calls = arbitrary side effects).

### Industry Practice
- **Common:** one demo stdio server checked into the repo; credentials in env vars; no review process for added servers.
- **Senior:** allowlist servers per environment; least-privilege credentials; separate read vs write tools; version server releases; contract tests for `tools/list` schemas; document whether the engagement **ships a server** (customer keeps it) vs **composes existing servers**.

### Concrete Scenario
AI Engineer Europe workshop builds **two MCP servers** (Deep Research + LinkedIn Writing), each exposing tools/resources/prompts via FastMCP, then connects them to Claude Code/Cursor via `.mcp.json` — “build once, orchestrate from any MCP harness”: https://www.youtube.com/watch?v=mYSRn6PC1mc and https://github.com/samtalasila/ai-engineer-europe  
A2A vs MCP complementarity (official): https://a2a-protocol.org/latest/

### Open Questions
- Who certifies enterprise MCP servers (vendor? host? customer security team)?
- Should product companies expose **one fat server** or **many small servers** per domain for blast-radius control?

### Sources
- https://docs.anthropic.com/en/docs/agents-and-tools/mcp
- https://modelcontextprotocol.io/docs/learn/architecture
- https://a2a-protocol.org/latest/
- https://openai.github.io/openai-agents-python/tools/
- https://www.youtube.com/watch?v=mYSRn6PC1mc
- https://github.com/samtalasila/ai-engineer-europe
- https://youtu.be/kQmXtrmQ5Zg

---

## Concept: Resource vs tool vs prompt primitives in MCP

### Fundamentals
MCP servers expose three **server primitives** ([Specification](https://modelcontextprotocol.io/specification/2025-11-25/), [Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)):

| Primitive | Role | Typical methods | Who initiates? |
|-----------|------|-----------------|----------------|
| **Tools** | Executable actions (APIs, writes, searches) | `tools/list`, `tools/call` | Model/host decides to invoke |
| **Resources** | Read-only(ish) contextual data identified by **URI** | `resources/list`, `resources/read`, templates, subscribe | **Application-driven** — host UI or heuristics attach context |
| **Prompts** | Reusable templated workflows / message templates | `prompts/list`, `prompts/get` | Usually user/host selects a slash-command-like workflow |

**Resources** ([Resources docs](https://modelcontextprotocol.io/docs/concepts/resources)): URI-addressed; optional MIME type, size, icons, annotations (`audience`, `priority`, `lastModified`); support **templates** (`resources/templates/list`); optional `listChanged` notifications and **subscriptions** for updates. Designed so hosts can show pickers, search, or auto-include context — protocol does not mandate one UX. Security: validate URIs; prevent path traversal on `file://`.

**Tools:** side-effecting or computational; JSON Schema arguments; results returned to the model as tool observations (via the host’s tool-calling bridge).

**Prompts:** parameterized templates that structure multi-step interactions (e.g. “research workflow”) without requiring the user to remember the tool choreography — workshop servers register prompts like `research_workflow` / `linkedin_post_workflow` ([AI Engineer Europe workshop](https://github.com/samtalasila/ai-engineer-europe)).

Mental model: **resources = context**, **tools = actions**, **prompts = packaged plays**.

### Alternatives & Tradeoffs
- Expose a DB table as a **resource** (read schema/sample) vs a **tool** (`run_sql`) — resource is safer default; tool needs strong guardrails.
- Encode a workflow as a **prompt** vs an **agent graph** — prompts are portable across hosts; graphs give stronger control/HITL.
- Stuff files into tool results vs resources — resources are cacheable/subscribable and UI-selectable; tool results are ephemeral observations.

Tradeoff: overusing tools for pure reads pollutes the tool list and increases accidental side-effect risk; underusing prompts makes every user reinvent the workflow.

### Necessity
Collapsing everything into tools loses MCP’s design for **application-controlled context** (resources) and **shared workflow templates** (prompts). Hosts that only wire `tools/call` leave half the protocol’s value on the table for FDE demos and enterprise UX.

### Industry Practice
- **Common:** tools-only servers.
- **Senior:** resources for schemas, docs, configs; tools for mutations and searches; prompts for opinionated multi-step jobs; annotations to hint audience/priority; pagination/cursors on large lists; explicit error codes for missing resources (`-32602`).

### Concrete Scenario
Resources specification examples (`file:///project/src/main.rs` list/read, URI templates, subscribe/update notifications): https://modelcontextprotocol.io/docs/concepts/resources  
Workshop pattern table — Deep Research server tools + `research_workflow` prompt; LinkedIn server tools + `linkedin_post_workflow` prompt: https://github.com/samtalasila/ai-engineer-europe

### Open Questions
- When should a host auto-attach resources vs wait for the model to fetch via a tool?
- Are prompts competing with “skills” / agent-spec packs emerging in IDE ecosystems?

### Sources
- https://modelcontextprotocol.io/specification/2025-11-25/
- https://modelcontextprotocol.io/docs/learn/architecture
- https://modelcontextprotocol.io/docs/concepts/resources
- https://modelcontextprotocol.io/docs/concepts/tools
- https://github.com/samtalasila/ai-engineer-europe

---

## Concept: Why MCP matters for FDE work (standardized integration surface)

### Fundamentals
**Forward Deployed / AI Engineer** work is usually: land in a customer’s messy environment, connect models to **their** systems, and leave something operable. MCP matters because it turns “integration” into a **repeatable product surface**:

1. **Build once, attach many hosts** — same server works in Claude Code, Cursor, Desktop, and custom agents ([Anthropic MCP overview](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)).
2. **Clear security boundary** — each server is an isolated process/service with negotiated capabilities; blast radius can be scoped per system.
3. **Composable engagements** — stack vendor MCP servers + one custom server for the customer’s proprietary API instead of a monolith agent.
4. **Handoff artifact** — the MCP server + config becomes what the customer keeps after the FDE leaves (vs a fragile notebook).
5. **Ecosystem leverage** — registries, shared servers, and conference/workshop patterns accelerate delivery ([AI Engineer MCP workshop](https://youtu.be/kQmXtrmQ5Zg)).

MCP does **not** replace orchestration, evals, or auth design — it standardizes how context and tools show up at the model boundary. Pair with A2A when multiple opaque agents must collaborate across vendors ([A2A](https://a2a-protocol.org/latest/)).

### Alternatives & Tradeoffs
| FDE delivery artifact | Portability | Maintenance |
|-----------------------|-------------|-------------|
| MCP server(s) + host config | High across MCP hosts | Spec/SDK updates |
| LangGraph app with bespoke tools | High within that codebase | Host-specific UX weak |
| One-off Claude project instructions | Low | Drifts quickly |
| Customer-only IDE plugin | Low | High rewrite cost |

Tradeoff: standardizing on MCP may push you to shape APIs as tool schemas even when a batch ETL job would be more honest — don’t MCP-wash every integration.

### Necessity
Without a standardized surface, each customer engagement reinvents connectors and dies when the preferred chat UI changes. With MCP, the expensive part (domain tool semantics, auth, guardrails) concentrates in the server; the host is swappable.

### Industry Practice
- **Common:** slideware “we use MCP”; actually hard-coded tools in one app.
- **Senior:** treat MCP servers as versioned products; CI contract tests; secrets via customer vault; document host setup; measure tool success rates; combine with agent loop guardrails (Week 11) and orchestration (Week 13).

### Concrete Scenario
Anthropic’s public MCP narrative (Calendar/Notion agents, Claude Code + Figma, enterprise DB chat, Blender): https://docs.anthropic.com/en/docs/agents-and-tools/mcp  
AI Engineer Summit MCP workshop (philosophy, building, agents, roadmap): https://youtu.be/kQmXtrmQ5Zg  
Official AI Engineer org points at MCP as a first-class conference/data surface: https://www.ai.engineer/llms.md

### Open Questions
- Will enterprise procurement treat MCP servers like browser extensions (scary) or like APIs (manageable)?
- How do FDEs version breaking tool schema changes for customers who pinned an older host?

### Sources
- https://docs.anthropic.com/en/docs/agents-and-tools/mcp
- https://modelcontextprotocol.io/docs/learn/architecture
- https://a2a-protocol.org/latest/
- https://youtu.be/kQmXtrmQ5Zg
- https://www.ai.engineer/llms.md
- https://www.youtube.com/watch?v=mYSRn6PC1mc

---

## Week 12 cross-cutting sources

- MCP architecture (learn): https://modelcontextprotocol.io/docs/learn/architecture  
- MCP specification: https://modelcontextprotocol.io/specification/2025-11-25/  
- MCP resources: https://modelcontextprotocol.io/docs/concepts/resources  
- MCP tools: https://modelcontextprotocol.io/docs/concepts/tools  
- Anthropic MCP overview: https://docs.anthropic.com/en/docs/agents-and-tools/mcp  
- A2A protocol (MCP complement): https://a2a-protocol.org/latest/  
- AI Engineer Summit MCP workshop: https://youtu.be/kQmXtrmQ5Zg  
- AI Engineer Europe multi-MCP workshop: https://www.youtube.com/watch?v=mYSRn6PC1mc  
