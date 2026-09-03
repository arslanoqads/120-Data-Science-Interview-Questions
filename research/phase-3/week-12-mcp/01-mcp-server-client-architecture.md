# 01 — MCP server / client architecture

> Week 12 — Model Context Protocol  
> Research notes (raw).

---

## Fundamentals

MCP is a **stateful session protocol** on **JSON-RPC 2.0** for exchanging context and coordinating sampling between **clients** and **servers**. The documented topology is **client–host–server**, not “the LLM speaks MCP.” The **host** is the AI application; it creates **one client instance per connected server**; each client holds **one dedicated session** ([Specification architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture/index), [Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)).

### Host vs client vs server

**Host** (container and coordinator):

- Creates/destroys client instances  
- Connection permissions and lifecycle  
- Security policy and **user consent**  
- LLM integration and **sampling** (when a server asks the host to complete)  
- Aggregates context from many servers  

**Client** (inside the host):

- Stateful session **1:1** with a server  
- Protocol version + **capability** exchange  
- Bidirectional JSON-RPC routing  
- Subscriptions and notifications  
- Isolation: server A must not see server B’s traffic or the full chat log  

**Server** (your process or a vendor service):

- Exposes **resources, tools, prompts**  
- Focused responsibility; composable with other servers  
- May **request** client features: sampling, elicitation, logging  
- Local subprocess **or** remote HTTP service  

Design principles from the spec (paraphrase, not slogans to tattoo on a README):

1. **Servers should be easy to build** — hosts do orchestration.  
2. **Servers should be composable** — isolation + shared protocol.  
3. **Servers must not read the whole conversation or peer into other servers** — host keeps history.  
4. **Features are progressive** — negotiate; don’t assume.

VS Code as host connecting to Sentry (remote HTTP) **and** filesystem (local stdio) is the official mental picture: two client objects, two sessions ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)).

### Two layers

| Layer | Job |
|-------|-----|
| **Data** | JSON-RPC methods: lifecycle, primitives, notifications, utilities |
| **Transport** | Bytes, framing, connection, **auth** |

Same JSON-RPC messages on every transport. SDKs hide framing; you still own **capability honesty** and **security**.

**Data layer buckets** ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)):

- **Lifecycle** — `initialize` / `initialized` / shutdown  
- **Server features** — tools, resources, prompts  
- **Client features** — sampling (`sampling/createMessage`), elicitation (`elicitation/create`), logging  
- **Utilities** — notifications, progress, cancellation, experimental **tasks**  

### Transports

Spec currently defines **two** standard transports; clients **SHOULD** support stdio ([Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)).

**stdio**

- Client **spawns** the server as a subprocess.  
- Newline-delimited JSON-RPC on stdin/stdout; **no embedded newlines**.  
- **stderr** = logs (client MUST NOT treat stderr as protocol errors).  
- Server MUST NOT print non-MCP bytes on stdout (print debugging on stdout **breaks** Desktop/Code).  
- Shutdown: client closes stdin → wait → `SIGTERM` → `SIGKILL`. Server may exit by closing stdout.

**Streamable HTTP** (replaces HTTP+SSE from protocol `2024-11-05`)

- Independent process; **many** clients.  
- **One** MCP endpoint (POST + GET), e.g. `https://example.com/mcp`.  
- Client POST: `Accept: application/json, text/event-stream`. Body = one JSON-RPC message.  
- Responses: JSON object **or** SSE stream. GET may open an SSE stream for server-initiated messages.  
- Session: server MAY return `MCP-Session-Id` on `InitializeResult`; client MUST send it on later requests. DELETE may end the session.  
- Subsequent HTTP requests MUST send `MCP-Protocol-Version` (negotiated version). Missing header: servers SHOULD assume `2025-03-26` for compatibility.  
- Auth: bearer / API keys / headers; docs **recommend OAuth** for tokens ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)). Full rules: [Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) (OAuth 2.1, PKCE, RFC 9728 protected resource metadata, RFC 8707 resource indicators).  

**HTTP security (normative warnings):** validate `Origin` (invalid → 403) to block DNS rebinding; bind local servers to **127.0.0.1** not `0.0.0.0`; authenticate. SSE `Last-Event-ID` for resume; do not treat disconnect as cancel — send `CancelledNotification`.

Custom transports are allowed if they preserve JSON-RPC + lifecycle.

Claude Code additionally documents **WebSocket** and still-supported **SSE** as host-specific — those are **host** transports, not a reason to ignore the spec’s two standards (overview file 00).

### Lifecycle (mandatory)

([Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle))

1. Client sends **`initialize`**: `protocolVersion`, client `capabilities`, `clientInfo`.  
2. Server responds: agreed/supported `protocolVersion`, server `capabilities`, `serverInfo`, optional `instructions`.  
3. Client sends **`notifications/initialized`**.  
4. **Operation** — only negotiated methods.  
5. **Shutdown** via transport (no special JSON-RPC goodbye).

Rules:

- Client SHOULD NOT send non-ping requests before the initialize **result**.  
- Server SHOULD NOT send non-ping/logging requests before `initialized`.  
- If the client cannot speak the server’s returned version → **disconnect**.  
- Timeouts on all requests; cancel on timeout; progress may reset a clock but a **max** timeout still applies.

**Capability negotiation is the security/compat boundary.** Spec architecture: if the server does not advertise `tools`, the client must not call `tools/call`. Same for resource subscriptions (`subscribe` flag), sampling (client must declare `sampling`), etc.

Illustrative server capability object from the lifecycle spec:

```json
{
  "logging": {},
  "prompts": { "listChanged": true },
  "resources": { "subscribe": true, "listChanged": true },
  "tools": { "listChanged": true }
}
```

Client examples: `roots`, `sampling`, `elicitation`, `tasks`, `experimental`.

Sub-flags: `listChanged` (prompts/resources/tools), `subscribe` (**resources only**).

### Isolation that FDEs forget

The host **must not** dump the full transcript into every server. Servers see **arguments you send** and **sampling payloads they request**. That is why a “filesystem MCP” plus a “prod-db MCP” is a **trust architecture**, not just packaging. Cross-server composition happens **in the host/model**, not by servers calling each other (that would be A2A or your own backend — file 02).

---

## Alternatives & Tradeoffs

| Integration style | Pros | Cons |
|-------------------|------|------|
| **MCP (stdio)** | Simple local attach; no network; official Desktop path | Process = user permissions; hard to share; stdout hygiene |
| **MCP (Streamable HTTP)** | Multi-user, OAuth, remote | Origin/session/auth complexity; you become an HTTP service |
| **Provider-native tools only** | Deep hosted features | Rewrite per host; no customer-owned connector |
| **Ad-hoc REST + custom function schemas** | Full control | N hosts × M APIs |
| **IDE plugin SDK** | Native UX | Not reusable in Desktop/API agents |
| **In-process function tools** (Week 11 only) | Fastest loop | Zero portability |

Tradeoff: MCP standardizes the **connector**, not intelligence. A JSON-RPC server with a 200-tool dump still fails Week 11 selection.

| Lifecycle stance | Pros | Cons |
|------------------|------|------|
| Advertise only implemented caps | Clients skip dead methods | You must implement `listChanged` if you set the flag |
| Advertise everything “for the future” | Looks complete | Spec violation; hosts call missing methods |
| Skip `initialized` | Seems faster | Servers may not start normal ops; spec forbids most server requests until then |

---

## Necessity

Without host/client/server + capability negotiation:

- Silent `tools/call` against a resources-only server.  
- Version skew (client `2025-11-25`, server `2024-11-05` SSE-only) with no disconnect.  
- Stdio servers log to stdout → host JSON parse failures that look like “MCP is flaky.”  
- HTTP servers on `0.0.0.0` without Origin checks → browser-based attacks on local MCP.  
- One “god client” sharing state across servers → data bleed (the spec’s isolation principle exists because this happens).

FDE symptom: “it works in Inspector, fails in Desktop” is almost always **transport** (CWD, env, stdout) or **capability** (host didn’t map resources), not the model.

---

## Industry Practice

- **Common:** FastMCP hello; never read lifecycle; mix `print()` on stdout; skip protocol version; copy SSE URLs into Streamable HTTP configs; no session ID handling.  
- **Senior:** Official SDK; pin version; capability flags match code; Inspector + unit tests for `initialize` payload; stdio stderr logging only; HTTP: localhost bind in dev, Origin check, OAuth 2.1 + resource indicators in prod; timeouts and cancellation; `MCP-Protocol-Version` on HTTP; separate servers per trust domain (files vs prod DB); document host-specific extras (Code `type: ws`) as **non-portable**.

Claude Code v2 runtime (SDK 2.0) can negotiate revision **2026-07-28** for some HTTP connectors; stdio stays on older handshake unless `MCP_PROTOCOL_NEGOTIATION=auto` ([Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)). Senior practice: **test the host you ship to**, don’t assume one revision everywhere.

---

## Concrete Scenario

Official architecture walkthrough: host creates one client per server; tools/resources/prompts; JSON-RPC data layer + stdio/HTTP ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)).

Sequence you should be able to draw on a whiteboard:

1. Desktop launches `uv run server.py` (stdio).  
2. Client `initialize` with `protocolVersion: "2025-11-25"`.  
3. Server returns `tools: { listChanged: true }`, `resources: {}`.  
4. Client `notifications/initialized`.  
5. Client `tools/list` → your `docs_search`.  
6. Model (inside host) chooses the tool; host `tools/call`.  
7. Server returns `content[]` + `isError`.  
8. Host injects observation into the **Week 11** loop.

Workshop grounding: Mahesh Murag, AI Engineer Summit ([YouTube](https://youtu.be/kQmXtrmQ5Zg)).

If you instead use Anthropic’s **Messages API MCP connector**, the **host is Anthropic’s API**: you pass `mcp_servers[]` + `tools: [{type: mcp_toolset}]`; **no stdio**; **tools only** ([MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)). Same protocol idea, different participant (you are not running the client).

---

## Open Questions

- Will remote auth converge on one OAuth profile across Desktop, Code, Cursor, and API connectors?  
- Experimental **tasks** (durable/deferred tool calls): which hosts will expose them before FDEs should depend on them?  
- How should hosts sandbox stdio (containers, OS permissions, secret stores) without breaking `npx -y` developer UX?  
- Session hijacking mitigations for `MCP-Session-Id` — are enterprise hosts treating session IDs like cookies?

---

## Sources

- https://modelcontextprotocol.io/docs/learn/architecture  
- https://modelcontextprotocol.io/docs/getting-started/intro  
- https://modelcontextprotocol.io/specification/2025-11-25/architecture/index  
- https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle  
- https://modelcontextprotocol.io/specification/2025-11-25/basic/transports  
- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization  
- https://docs.anthropic.com/en/docs/agents-and-tools/mcp  
- https://docs.anthropic.com/en/docs/claude-code/mcp  
- https://platform.claude.com/docs/en/agents-and-tools/mcp-connector  
- https://youtu.be/kQmXtrmQ5Zg  
