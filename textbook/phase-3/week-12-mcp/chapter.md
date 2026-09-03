# Chapter 12 — Model Context Protocol (MCP)

> **Phase 3 — Agentic Systems**  
> **Compilation status:** COMPLETE  
> **Source of truth:** `research/phase-3/week-12-mcp/`  
> **Syllabus Build:** Ship a **single MCP server wrapping one capability**, then **prove it attaches to two hosts**: (1) take **one** Week 11 capability (recommended: `docs_search`, or `structured_query`, or calendar list — not all three dumped as 40 tools) and implement it as an MCP **server** with advertised `tools` (optionally a **resource** for schema/docs and a **prompt** for the playbook); (2) transport **stdio** for local Desktop/Code attach (optional second Streamable HTTP listener for remote hosts — do not skip stdio); (3) connect **Claude Desktop** via `claude_desktop_config.json` (`mcpServers` + `command`/`args`, absolute paths); (4) connect **Claude Code** via `claude mcp add` and/or project `.mcp.json` (`type`: `stdio` vs `http`; `--` separator for stdio; workspace trust / project approval); (5) demonstrate host lists the tool → model calls it → observation returns (screenshot or `/mcp` `✔ Connected` plus a successful tool trace); (6) document the **trust boundary**: directories/APIs the process can reach; secrets in `env` not committed; user confirmation for writes. Interview artifact = **one server + two host configs + a successful tool call**, not a slide that says “we use MCP.”

---

## Chapter framing

Week 12 is the **connector** week of Phase 3. Week 11 taught the **loop contract** (plan → act → observe, pairing IDs, stop reasons). This week does **not** replace that loop. It standardizes how tools and context **show up at the host boundary** so the same capability can attach to Claude Desktop, Claude Code, Cursor, VS Code, ChatGPT, or a custom host without rewriting function schemas per product.

Anthropic and the MCP site use the same slogan: MCP is a **“USB-C port for AI applications”** — an open standard so hosts can connect to data, tools, and workflows. Official architecture docs are explicit: MCP is the protocol for **context exchange**; hosts still own orchestration, consent, and aggregation. Do **not** start Week 13 (orchestration / multi-agent) from this chapter — MCP is a *distribution and discovery* layer for tools/context, not graphs, HITL persistence, or multi-agent handoffs.

**What you ship this week:** one **MCP server** wrapping **one** capability, plus **two host configs** that actually connect.

### Participants you must name correctly

| Role | What it is | This week’s instance |
|------|------------|----------------------|
| **Host** | The AI app the user talks to. Creates clients, enforces consent, talks to the LLM. | Claude Desktop **or** Claude Code |
| **Client** | Protocol session **inside** the host; **1:1** with a server | Instantiated when Desktop/Code attaches your server |
| **Server** | Independent process/service exposing primitives | **Your** wrapped capability |

Local stdio servers typically serve **one** client (the host spawned the subprocess). Remote Streamable HTTP servers typically serve **many** clients.

### Syllabus artifact: wrap one capability

Do **not** wrap your entire CRM. Pick **one** Week 11 tool and expose it over MCP.

**Recommended: `docs_search` as MCP.** Why: read-only (safer first server), JSON Schema already exists, results are observations the Week 11 loop already understands.

Sketch of what the server advertises after `initialize` (server capabilities) and `tools/list`:

```json
{
  "name": "docs_search",
  "description": "Keyword/semantic search over the internal document corpus (policies, runbooks, product docs). Use when the user needs quoted handbook text. Do not use for warehouse metrics or calendar.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "Search terms, not a full chat transcript." },
      "k": { "type": "integer", "description": "Max chunks (1–8)." }
    },
    "required": ["query", "k"]
  }
}
```

Optional but senior:

- **Resource** `docs://corpus/schema` or `file:///…/INDEX.md` — application-driven context (what the corpus contains).  
- **Prompt** `handbook_lookup` — user-selected slash-command workflow that already includes “cite snippets, do not invent policy.”

The host then: `tools/list` → maps MCP tools into the model’s tool schema → model `tool_use` / `function_call` → host `tools/call` → MCP result → `tool_result` in the **Week 11 loop**. MCP is the **wire**; the loop is still yours (or the host’s built-in runner).

### Connect Claude Desktop (local stdio)

Official “connect local servers” tutorial uses Claude Desktop as the example host:

- **macOS config:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
- Developer Settings → **Edit Config**. Completely **quit and restart** Desktop after edits.  
- Logs: `~/Library/Logs/Claude/mcp.log` and `mcp-server-<NAME>.log` (Windows under `%APPDATA%\Claude\logs`).

Filesystem example from that tutorial (swap command/args for **your** server):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/Desktop",
        "/Users/username/Downloads"
      ]
    }
  }
}
```

For a Python/uv server, official build-server docs use **absolute** `--directory` paths and `uv run …`. Debugging docs: CWD for stdio servers may be `/`; **never rely on relative paths**; stdio servers inherit a **limited** env — put secrets in `env`. Security: the process runs **as the user**. Only grant directories/APIs you accept. Desktop still **prompts before tool execution**.

### Connect Claude Code (stdio, HTTP, project `.mcp.json`)

Transports Claude Code documents:

| Transport | How you add it | When |
|-----------|----------------|------|
| **HTTP** (Streamable HTTP; JSON `type` may be `http` or alias `streamable-http`) | `claude mcp add --transport http <name> <url>` | Remote / cloud MCP. Recommended for remote. |
| **SSE** | `--transport sse` | Deprecated; only if the vendor still only speaks HTTP+SSE. |
| **stdio** | `claude mcp add --transport stdio <name> -- <command> [args…]` | Local process; `--` is mandatory so Code does not swallow server flags. |
| **WebSocket** | `.mcp.json` / `add-json` with `"type": "ws"` | Push/events; **no** OAuth via `--transport`; header auth only. |

**Scopes:** `local` (default, current project in `~/.claude.json`) → `project` (`.mcp.json` at repo root, VCS-friendly) → `user` (all projects). Precedence: local > project > user > plugins > claude.ai connectors. Duplicate names: **one** definition wins; fields are **not** merged.

Project `.mcp.json` shape:

```json
{
  "mcpServers": {
    "docs-search": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/SERVER", "run", "server.py"]
    }
  }
}
```

Remote HTTP example:

```json
{
  "mcpServers": {
    "shared-server": {
      "type": "http",
      "url": "https://example.com/mcp"
    }
  }
}
```

A `url` **without** `type` is a config error: Code treats typeless entries as **stdio**. Code also sets `CLAUDE_PROJECT_DIR` in the **spawned server env**. Servers that sandbox files should implement **`roots/list`**; Code answers with launch dir + `--add-dir` / additional directories.

**Trust:** project `.mcp.json` servers wait for **workspace trust** and interactive **approval** (`⏸ Pending approval`). Untrusted clones cannot self-approve via committed `enableAllProjectMcpServers`. `claude -p` / Agent SDK / `bypassPermissions` may **skip** the prompt — use `disabledMcpjsonServers` or `--strict-mcp-config` when that is a problem.

Ops: `/mcp` panel, `claude mcp list` health (`✔ Connected`, `! Needs authentication`, `✘ Failed to connect`), OAuth from `/mcp`, `MCP_TIMEOUT` / per-server `timeout`, idle timeouts, `list_changed` refresh, HTTP reconnect with backoff, tool-output token caps (`MAX_MCP_OUTPUT_TOKENS`). Stdio servers are **not** auto-reconnected (local processes). Import Desktop configs: `claude mcp add-from-claude-desktop`. You can also expose **Claude Code itself** as a Desktop stdio server (`claude mcp serve`) — useful as a demo of host-as-server, not the syllabus default.

### What “done” looks like

1. Server process starts; `initialize` ↔ capabilities; client sends `notifications/initialized`.  
2. Desktop shows the connector / tools; Code `/mcp` shows connected + tool count.  
3. User prompt causes **one** `tools/call` for your capability; result is visible in the chat.  
4. Write tools (if any) required a **confirmation**.  
5. You can point a **second** host at the **same** stdio command (or the same HTTP URL) without changing server code.

### Default path (synthesis)

1. Prefer **official MCP SDKs** (or FastMCP on top of them) over hand-rolled JSON-RPC. Pin a **protocol version** (`2025-11-25` is the spec revision used throughout the research corpus; hosts may also negotiate later revisions such as `2026-07-28`).  
2. Prefer **stdio** for laptop/IDE attach; **Streamable HTTP + OAuth 2.1** for shared remote servers. Treat HTTP+SSE (`2024-11-05`) as deprecated compatibility.  
3. Advertise **only** capabilities you implement. If you do not declare `tools`, clients must not call `tools/call`.  
4. Split **read vs write** tools. Resources for schemas and docs; prompts for opinionated workflows; tools for actions.  
5. Allowlist third-party servers. Treat every `tools/call` as a **side effect channel** (Week 11 loop + Week 14 safety).  
6. Interview artifact = **one server + two host configs + a successful tool call**, not a slide that says “we use MCP.”

Do **not** skip this week for “we’ll just `bind_tools` in LangGraph.” You cannot debug host catalogs, capability mismatch, or customer handoff if the **connector** is implicit.

Read the concepts in order. Each section’s **Worked Example** and **Apply It** assume the same flagship service (working title: Deployment Copilot) lifting **one** Week 11 capability onto MCP and attaching Claude Desktop + Claude Code.

---

### MCP server / client architecture

* **Fundamentals:**  
  MCP is a **stateful session protocol** on **JSON-RPC 2.0** for exchanging context and coordinating sampling between **clients** and **servers**. The documented topology is **client–host–server**, not “the LLM speaks MCP.” The **host** is the AI application; it creates **one client instance per connected server**; each client holds **one dedicated session**.

  **Host** (container and coordinator): creates/destroys client instances; connection permissions and lifecycle; security policy and **user consent**; LLM integration and **sampling** (when a server asks the host to complete); aggregates context from many servers.

  **Client** (inside the host): stateful session **1:1** with a server; protocol version + **capability** exchange; bidirectional JSON-RPC routing; subscriptions and notifications; isolation — server A must not see server B’s traffic or the full chat log.

  **Server** (your process or a vendor service): exposes **resources, tools, prompts**; focused responsibility; composable with other servers; may **request** client features (sampling, elicitation, logging); local subprocess **or** remote HTTP service.

  Spec design principles (paraphrase): servers should be easy to build (hosts do orchestration); servers should be composable (isolation + shared protocol); servers must not read the whole conversation or peer into other servers (host keeps history); features are progressive (negotiate; don’t assume).

  VS Code as host connecting to Sentry (remote HTTP) **and** filesystem (local stdio) is the official mental picture: two client objects, two sessions.

  **Two layers:**

  | Layer | Job |
  |-------|-----|
  | **Data** | JSON-RPC methods: lifecycle, primitives, notifications, utilities |
  | **Transport** | Bytes, framing, connection, **auth** |

  Same JSON-RPC messages on every transport. SDKs hide framing; you still own **capability honesty** and **security**.

  Data layer buckets: **Lifecycle** (`initialize` / `initialized` / shutdown); **Server features** (tools, resources, prompts); **Client features** (sampling `sampling/createMessage`, elicitation `elicitation/create`, logging); **Utilities** (notifications, progress, cancellation, experimental **tasks**).

  **Transports** — the spec currently defines **two** standard transports; clients **SHOULD** support stdio:

  **stdio:** Client **spawns** the server as a subprocess. Newline-delimited JSON-RPC on stdin/stdout; **no embedded newlines**. **stderr** = logs (client MUST NOT treat stderr as protocol errors). Server MUST NOT print non-MCP bytes on stdout (print debugging on stdout **breaks** Desktop/Code). Shutdown: client closes stdin → wait → `SIGTERM` → `SIGKILL`. Server may exit by closing stdout.

  **Streamable HTTP** (replaces HTTP+SSE from protocol `2024-11-05`): Independent process; **many** clients. **One** MCP endpoint (POST + GET), e.g. `https://example.com/mcp`. Client POST: `Accept: application/json, text/event-stream`. Body = one JSON-RPC message. Responses: JSON object **or** SSE stream. GET may open an SSE stream for server-initiated messages. Session: server MAY return `MCP-Session-Id` on `InitializeResult`; client MUST send it on later requests. DELETE may end the session. Subsequent HTTP requests MUST send `MCP-Protocol-Version` (negotiated version). Missing header: servers SHOULD assume `2025-03-26` for compatibility. Auth: bearer / API keys / headers; docs **recommend OAuth** for tokens (OAuth 2.1, PKCE, RFC 9728 protected resource metadata, RFC 8707 resource indicators). HTTP security (normative): validate `Origin` (invalid → 403) to block DNS rebinding; bind local servers to **127.0.0.1** not `0.0.0.0`; authenticate. SSE `Last-Event-ID` for resume; do not treat disconnect as cancel — send `CancelledNotification`.

  Custom transports are allowed if they preserve JSON-RPC + lifecycle. Claude Code additionally documents **WebSocket** and still-supported **SSE** as host-specific — those are **host** transports, not a reason to ignore the spec’s two standards.

  **Lifecycle (mandatory):**

  1. Client sends **`initialize`**: `protocolVersion`, client `capabilities`, `clientInfo`.  
  2. Server responds: agreed/supported `protocolVersion`, server `capabilities`, `serverInfo`, optional `instructions`.  
  3. Client sends **`notifications/initialized`**.  
  4. **Operation** — only negotiated methods.  
  5. **Shutdown** via transport (no special JSON-RPC goodbye).

  Rules: Client SHOULD NOT send non-ping requests before the initialize **result**. Server SHOULD NOT send non-ping/logging requests before `initialized`. If the client cannot speak the server’s returned version → **disconnect**. Timeouts on all requests; cancel on timeout; progress may reset a clock but a **max** timeout still applies.

  **Capability negotiation is the security/compat boundary.** If the server does not advertise `tools`, the client must not call `tools/call`. Same for resource subscriptions (`subscribe` flag), sampling (client must declare `sampling`), etc.

  Illustrative server capability object:

  ```json
  {
    "logging": {},
    "prompts": { "listChanged": true },
    "resources": { "subscribe": true, "listChanged": true },
    "tools": { "listChanged": true }
  }
  ```

  Client examples: `roots`, `sampling`, `elicitation`, `tasks`, `experimental`. Sub-flags: `listChanged` (prompts/resources/tools), `subscribe` (**resources only**).

  **Isolation:** The host **must not** dump the full transcript into every server. Servers see **arguments you send** and **sampling payloads they request**. A “filesystem MCP” plus a “prod-db MCP” is a **trust architecture**, not just packaging. Cross-server composition happens **in the host/model**, not by servers calling each other.

* **The Alternatives:**  

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

* **Failure Modes:**  
  - Silent `tools/call` against a resources-only server.  
  - Version skew (client `2025-11-25`, server `2024-11-05` SSE-only) with no disconnect.  
  - Stdio servers log to stdout → host JSON parse failures that look like “MCP is flaky.”  
  - HTTP servers on `0.0.0.0` without Origin checks → browser-based attacks on local MCP (DNS rebinding).  
  - One “god client” sharing state across servers → data bleed (the spec’s isolation principle exists because this happens).  
  - FDE symptom: “it works in Inspector, fails in Desktop” is almost always **transport** (CWD, env, stdout) or **capability** (host didn’t map resources), not the model.

* **Average vs. Strong Engineer:**  
  **Average:** FastMCP hello; never read lifecycle; mix `print()` on stdout; skip protocol version; copy SSE URLs into Streamable HTTP configs; no session ID handling.  
  **Strong:** Official SDK; pin version; capability flags match code; Inspector + unit tests for `initialize` payload; stdio stderr logging only; HTTP: localhost bind in dev, Origin check, OAuth 2.1 + resource indicators in prod; timeouts and cancellation; `MCP-Protocol-Version` on HTTP; separate servers per trust domain (files vs prod DB); document host-specific extras (Code `type: ws`) as **non-portable**. Claude Code v2 runtime (SDK 2.0) can negotiate revision **2026-07-28** for some HTTP connectors; stdio stays on older handshake unless `MCP_PROTOCOL_NEGOTIATION=auto`. Senior practice: **test the host you ship to**, don’t assume one revision everywhere.

* **Worked Example:**  
  Deployment Copilot lifts `docs_search` to MCP. Sequence you should be able to draw on a whiteboard:

  1. Desktop launches `uv run server.py` (stdio).  
  2. Client `initialize` with `protocolVersion: "2025-11-25"`.  
  3. Server returns `tools: { listChanged: true }`, `resources: {}`.  
  4. Client `notifications/initialized`.  
  5. Client `tools/list` → your `docs_search`.  
  6. Model (inside host) chooses the tool; host `tools/call`.  
  7. Server returns `content[]` + `isError`.  
  8. Host injects observation into the **Week 11** loop.

  If you instead use Anthropic’s **Messages API MCP connector**, the **host is Anthropic’s API**: you pass `mcp_servers[]` + `tools: [{type: mcp_toolset}]`; **no stdio**; **tools only**. Same protocol idea, different participant (you are not running the client).

* **Apply It:**  
  1. Implement the server with an official Python/TS SDK (or FastMCP on top); pin protocol version `2025-11-25` in docs and HTTP headers.  
  2. Advertise only capabilities you implement; never set `listChanged` / `subscribe` without handlers.  
  3. Log to **stderr** only on stdio; ban `print()` on stdout.  
  4. Contract-test the `initialize` capability object and `tools/list` schema (Inspector + unit tests).  
  5. For any Streamable HTTP path: bind `127.0.0.1` in dev, validate `Origin`, send `MCP-Protocol-Version`, handle `MCP-Session-Id`.  
  6. Keep filesystem and prod-DB credentials on **separate** servers so isolation is real.

---

### Expose vs consume MCP servers

* **Fundamentals:**  
  Two FDE postures. They use the **same protocol** and **opposite ownership**. Mixing them in one engagement without naming which is which is how “we use MCP” becomes un-debuggable.

  **A. You are the server author (**expose**):** Wrap **your** product APIs, warehouses, or workflows so **any MCP host** can use them. You implement lifecycle + primitives (at least `tools/list` + `tools/call`). You choose transport: **stdio** (customer laptops, Desktop, Code, Cursor local attach) or **Streamable HTTP** (shared service, many clients, OAuth). You own: schemas, versioning, auth to **downstream** systems, rate limits, `isError` vs JSON-RPC errors, SLA, blast radius. Anthropic’s pitch — MCP **reduces development time** when building or integrating with AI apps — is true **only if** hosts already speak MCP; you still write the domain semantics. Claude Code can **scaffold** a server (`mcp-server-dev` plugin / `/mcp-server-dev:build-mcp-server`) — still **your** security review.

  **B. You are the host integrator (**consume**):** Point Claude Code / Desktop / Cursor / Agents SDK / Anthropic API at **someone else’s** server (GitHub, Slack, Notion, internal platform team). Discovery paths that are real in host docs: Desktop `claude_desktop_config.json`; Code `claude mcp add`, project `.mcp.json`, user/local scopes, plugins, **Anthropic Directory** remote connectors; `claude mcp add-from-claude-desktop`; Anthropic Messages **MCP connector** (`mcp_servers` + `mcp_toolset`, remote HTTPS only); OpenAI Agents SDK documents MCP as a **tool source** alongside function tools (tool search + `defer_loading`). After the host bridges MCP → model tools, your Week 11 loop sees **ordinary callable functions**. You do **not** automatically get the vendor’s SLAs or a safe allowlist. Claude Code: **verify you trust each server**; servers that fetch external content are a **prompt-injection** channel.

  **Complementary protocol: A2A (not a substitute).** Linux Foundation **A2A** (Google-originated): **agent-to-agent**. Official framing: **MCP** = equip **one** agent with tools/data; **A2A** = opaque agents **discover, delegate, share results** across frameworks **without** sharing internal memory/tools. A2A explicitly is **not** a tool-call protocol and **not** a replacement for MCP. If the customer wants “our LangGraph agent talks to their Crew agent,” that is A2A (Week 14 adjacent). If they want “Claude Code can `docs_search`,” that is MCP.

  **Thin MCP over REST vs curated surface:** A mechanical wrapper that 1:1 maps every REST endpoint to a tool **will** explode the palette (Week 11 selection). Consume-side, attaching **five** vendor servers can dump **hundreds** of tools into one Code session. Code’s **tool search** is the host mitigation; your job is still **allowlists** (`mcp_toolset` allow/deny on the API connector; Code `/mcp` disable; don’t commit random Directory servers).

* **The Alternatives:**  

  | Choice | When | Risk |
  |--------|------|------|
  | **Build MCP for your SaaS** | Customers live in many AI hosts | You own server security, versioning, SLA |
  | **Consume vendor MCP** | Fast enablement (Notion, GitHub, Stripe URLs in Code docs) | Supply chain; injection; schema drift |
  | **Thin MCP over existing REST** | Reuse API surface quickly | Leaky tools; oversized lists; auth passthrough |
  | **Skip MCP; proprietary plugin** | One strategic host | Lock-in; rewrite at the next RFP |
  | **One fat server** | Simple deploy | Blast radius; mixed trust (files + prod writes) |
  | **Many small servers** | Trust boundaries | Config sprawl; host connection limits |
  | **API MCP connector only** | No desktop fleet | Tools-only; public HTTPS; beta headers |
  | **A2A instead of MCP** | Multi-vendor **agents** | Does not attach Claude Desktop to your DB |

  Tradeoff: **exposing everything as tools** creates selection problems; **resources + prompts** are often the safer read-heavy API. **Consuming** everything from a marketplace is an un-reviewed plugin folder.

  | Engagement deliverable | Expose | Consume |
  |------------------------|--------|---------|
  | Customer keeps it after you leave | **Your** server repo + config | Their vendor contracts + your allowlist doc |
  | Who patches CVEs | You / customer platform | Vendor |
  | Auth | Your OAuth/resource server | Vendor OAuth in `/mcp` |

* **Failure Modes:**  
  - FDEs embedding into customer environments rebuild “Jira tool” per IDE — wasted engagement.  
  - Consuming **unvetted** MCP servers without allowlists: `tools/call` is arbitrary side effects with the user’s (or a service account’s) credentials; prompt injection via servers that fetch external content.  
  - Exposing a server **without** a versioning story: the first `inputSchema` change breaks every pinned host.  
  - Only consume: **no** artifact when vendors deprecate SSE.  
  - Only expose and never attach Desktop/Code: a process nobody runs.  
  - Secrets in committed `.mcp.json` instead of `env` / `${VAR}` expansion.  
  - Confusing “we connected Notion” with “we wrapped our capability.”

* **Average vs. Strong Engineer:**  
  **Average:** one demo stdio server in the repo; `.env` committed; `npx -y` whatever GitHub README; no review for added `.mcp.json` servers; production agent still uses hardcoded tools; “MCP” on the slide.  
  **Strong:** name the posture in the SOW (**ship a server** vs **compose existing servers** vs **both**). Allowlist per environment. Least-privilege credentials (read vs write tools split). Version server releases; contract tests for `tools/list`. Separate servers by trust domain. For consume: Directory/official vendor URLs, OAuth via host UI, disable unused servers in `/mcp`. For expose: official SDK, Inspector, both hosts in CI as far as feasible. Document SSE vs Streamable HTTP. API path: `mcp_toolset` **allowlist**, not “enable all.” Code: project `.mcp.json` uses `${API_KEY}` expansion, not literals. Workshop pattern (expose twice, then consume locally): two authored FastMCP servers + attach to Code/Cursor — still not “install the internet.”

* **Worked Example:**  
  **Engagement split** for Deployment Copilot / customer ACME:

  1. **Expose:** wrap the customer’s `structured_query` allowlisted warehouse as `acme-metrics` MCP (stdio for the pilot, HTTP later).  
  2. **Consume:** attach official GitHub MCP (remote HTTP) so Code can open PRs.  
  3. **Do not** wrap GitHub yourself unless the official server is blocked.  
  4. **Do not** put prod DB credentials in the GitHub server’s env.  
  5. Anthropic API bot for Slack: use **MCP connector** to the **HTTP** `acme-metrics` URL with `authorization_token` you minted; allowlist `structured_query` only.

  A2A vs MCP: if later “metrics agent” must delegate to a vendor “compliance agent” without sharing tools, add A2A — do not pretend MCP servers should call each other.

  Code examples of consume-by-URL from Anthropic’s own page: Notion `https://mcp.notion.com/mcp`, Asana SSE, Stripe `https://mcp.stripe.com`.

* **Apply It:**  
  1. Write the engagement posture in one sentence: expose / consume / both — and name which servers are yours.  
  2. Ship **your** Week 12 server for one proprietary capability; do not reimplement GitHub/Slack/Notion.  
  3. Allowlist every third-party server per environment; disable unused tools in `/mcp` or `mcp_toolset`.  
  4. Use `${VAR}` / Desktop `env` for secrets; never commit API keys in `.mcp.json`.  
  5. Semver the server; contract-test `tools/list` before hosts pin schemas.  
  6. Optional consume demo: attach one official remote (e.g. Notion) **after** your server works — label it consume, not expose.

---

### Resource vs tool vs prompt primitives

* **Fundamentals:**  
  MCP servers expose three **server primitives**. The spec’s **control hierarchy** is the whole design:

  | Primitive | Control | Role | Typical methods | Example |
  |-----------|---------|------|-----------------|---------|
  | **Prompts** | **User-controlled** | Templated workflows / slash commands | `prompts/list`, `prompts/get` | `code_review`, `research_workflow` |
  | **Resources** | **Application-controlled** | URI-addressed context | `resources/list`, `resources/read`, templates, subscribe | `file:///project/src/main.rs`, DB schema |
  | **Tools** | **Model-controlled** | Executable actions | `tools/list`, `tools/call` | API POST, search, file write |

  Hosts **may** implement any UX; the protocol does not mandate pickers vs auto-attach vs slash commands. If you collapse all three into tools, you are not “using MCP”; you are using **one** primitive.

  Mental model: **resources = context**, **tools = actions**, **prompts = packaged plays**. Advertise capabilities in `initialize` or clients must not call the methods.

  **Tools (model-controlled):** Unique `name` (SHOULD 1–128 chars; `[A-Za-z0-9_.-]`; case-sensitive; unique **per server**). `inputSchema`: JSON Schema object (default draft **2020-12**). Empty args: `{ "type": "object", "additionalProperties": false }`. Optional `title`, `description`, `icons`, `outputSchema`, `annotations`, `execution.taskSupport`. **Annotations are untrusted** unless the server is trusted. Pagination on `tools/list` (`cursor` / `nextCursor`). `listChanged` → `notifications/tools/list_changed`. Call: `tools/call` with `name` + `arguments`. Result: `content[]` (text, image, audio, `resource_link`, embedded `resource`) + optional `structuredContent` + `isError`. If `outputSchema` is set: server MUST conform; clients SHOULD validate. Also emit serialized JSON as text for compatibility. `structuredContent` is **not** LLM structured-output mode.

  **Two error channels** (same split as Anthropic `is_error` in Week 11):

  1. **Protocol / JSON-RPC** — unknown tool, malformed `CallToolRequest`, server faults (`-32602` unknown tool, …). Models rarely recover.  
  2. **`isError: true` in the result** — business/validation failures. Clients SHOULD feed these to the model for self-repair.

  Security (spec): servers MUST validate inputs, access control, rate limit, sanitize outputs. Clients SHOULD confirm sensitive ops, **show arguments before send** (exfil risk), validate results before the LLM, timeouts, audit logs. **HITL SHOULD exist to deny invocations.** Tool results MAY point at resources (`resource_link`) without those URIs appearing in `resources/list`.

  **Resources (application-controlled):** Identified by **URI**. Optional MIME, `size`, `title`, `description`, `icons`. Hosts may: tree UI, search, **heuristics / auto-include**, or ignore them. Caps: `subscribe`, `listChanged` independently. `resources/read` → `contents[]` as `text` or base64 `blob`. **Templates:** `resources/templates/list` with `uriTemplate` (e.g. `file:///{path}`); completions API may autocomplete args. Subscribe: `resources/subscribe` → `notifications/resources/updated` → client re-reads. Annotations: `audience` (`user` / `assistant`), `priority` 0–1, `lastModified` ISO-8601. URI schemes: `https://` only if the **client** can fetch itself; else custom/file. `file://` need not be a real FS (`inode/directory` XDG type allowed). `git://`. Custom per RFC3986. Errors: not found **`-32002`**; internal `-32603`. Security: **validate URIs**; prevent **path traversal** on `file://`; access control; binary encoding. Resources are the right default for **schemas, runbooks, config snapshots** — data the **app** should attach without waiting for the model to guess a tool.

  **Prompts (user-controlled):** `prompts/list` / `prompts/get` with `arguments`. Result: `messages[]` with `role` `user` | `assistant` and content (text, image, audio, embedded resource). Intended UX: **slash commands / menus**. Errors: invalid name / missing args → `-32602`. Security: validate I/O against injection and unauthorized resource embed. Workshop servers register prompts like `research_workflow` / `linkedin_post_workflow` so users don’t remember tool choreography. Prompts are **portable plays**. They are **not** LangGraph. Hosts that never call `prompts/get` leave this primitive dead.

  **Client primitives (not substitutes):** Servers may **call into** the host: **Sampling** (`sampling/createMessage`; server stays model-agnostic — no API keys in the server; client SHOULD HITL; can nest **tool loops** if `sampling.tools` is advertised; user reject → JSON-RPC `-1`); **Elicitation** (ask the user for input/confirmation); **Logging** (structured logs to the client); **Roots** (filesystem/URI boundaries the client provides — `roots/list`; Code documents this). Do not implement “the server has its own Anthropic key” if sampling would keep policy/keys in the host.

  **Database example from official architecture** — a DB MCP **should** typically expose: **Tool** (constrained query), **Resource** (schema), **Prompt** (few-shot “how to ask this database”). That triad is the senior default, not tools-only.

* **The Alternatives:**  

  | Design | Pros | Cons |
  |--------|------|------|
  | **DB table as resource** | Safer read; host picker; cache/subscribe | Hosts that only wire tools never see it |
  | **`run_sql` tool** | Model-flexible | Injection, blast radius, selection noise |
  | **Workflow as prompt** | Portable across hosts; user-initiated | Weak control vs a graph + HITL (Week 13) |
  | **Workflow as agent graph** | Strong HITL/state | Not an MCP primitive; host-specific |
  | **Stuff files into tool results** | Works in tools-only hosts (API connector) | Ephemeral; no subscribe; pollutes observations |
  | **Resources + `resource_link` from tools** | Search then attach | Two-step; host must implement resources |
  | **Tools-only server** | Matches Anthropic API MCP connector today | Loses application-driven context and slash workflows |

  Tradeoff: overusing tools for pure reads pollutes the list and raises accidental writes. Underusing prompts makes every user reinvent the play.

  API limitation: Messages **MCP connector supports tools only**. If the same server must serve Desktop **and** the API, you may need tools that **mirror** critical resources for the API path — document that as a **host gap**, not as “resources are useless.”

* **Failure Modes:**  
  - Collapsing everything into tools throws away MCP’s split between **model-initiated actions** and **application-controlled context**.  
  - Hosts that only implement `tools/call` (API connector, some IDE stubs) leave **half the protocol** on the table (schema pickers, live `resources/updated`, slash playbooks).  
  - Wrong error channel: JSON-RPC on a bad date format means the model never self-repairs; `isError` on “unknown tool” hides a client bug.  
  - Path traversal on `resources/read` is a classic local-server fail.  
  - Resources listed but never read by the host; prompts registered and unused.  
  - Trusting tool annotations from random consumed servers.

* **Average vs. Strong Engineer:**  
  **Average:** tools-only; no pagination; 200-character descriptions; `isError` never set; resources listed but never read by the host; prompts registered and unused.  
  **Strong:** resources for schemas/docs/config; tools for mutations **and** searches that need arguments; prompts for opinionated multi-step jobs; annotations for audience/priority; cursors on large lists; `-32002` for missing resources; `isError` for recoverable tool failures; validate URIs; don’t trust tool annotations from random consumed servers; contract-test `tools/list` + `resources/list` + `prompts/list`; Inspector round-trip. Claude Code: confirm host actually refreshes on `list_changed` (v2 streams).

* **Worked Example:**  
  **FDE `docs_search` server (syllabus) on Deployment Copilot:**

  | Primitive | Name | Why |
  |-----------|------|-----|
  | Resource | `docs://corpus/catalog` | Host can pin “what’s indexed” without a tool call |
  | Tool | `docs_search` | Model-controlled retrieval with `query`/`k` |
  | Prompt | `handbook_lookup` | User picks `/handbook_lookup` → messages already say “quote + cite, no invented policy” |

  Workshop pattern: Deep Research tools + `research_workflow`; LinkedIn tools + `linkedin_post_workflow`.

  Sampling scenario: a research server asks the **host LLM** to summarize a resource via `sampling/createMessage` so the server has no vendor SDK — only if the client advertised `sampling` and the user can deny.

* **Apply It:**  
  1. Advertise `tools`, and optionally `resources` / `prompts`, only if you implement the corresponding methods.  
  2. Add a catalog/schema **resource** before turning every read into a tool.  
  3. Add one **prompt** playbook (`handbook_lookup`) with cite-don’t-invent instructions.  
  4. Use `isError: true` for recoverable business failures; JSON-RPC errors only for protocol faults.  
  5. Validate URIs on `resources/read`; block path traversal on `file://`.  
  6. Contract-test `tools/list` + `resources/list` + `prompts/list`; document the API-connector tools-only gap if you also serve Anthropic’s Messages MCP connector.

---

### Why MCP matters for FDE (standardized integration surface)

* **Fundamentals:**  
  **Forward Deployed / AI Engineer** work is usually: land in a messy customer environment, connect models to **their** systems, leave something **operable**. MCP matters because it turns “integration” into a **repeatable product surface**, not a one-off `bind_tools` in last week’s notebook.

  Five reasons, grounded in official docs:

  1. **Build once, attach many hosts.** Same server in Claude Code, Claude Desktop, VS Code, Cursor, ChatGPT, custom hosts. Ecosystem list is explicit: assistants **and** IDEs.  
  2. **Clear security boundary per server.** Isolated process/service; negotiated capabilities; host-enforced consent. Spec principle: servers do not see the full conversation or sibling servers. Blast radius = **that** server’s credentials and tools — if you did not build a god-server.  
  3. **Composable engagements.** Stack **vendor** MCP (consume) + **one custom** server for the proprietary API (expose) instead of a monolith agent.  
  4. **Handoff artifact.** The customer keeps **server + host config** (Desktop JSON, Code `.mcp.json`, runbooks for `/mcp` and logs). That outlives the FDE laptop and a “Claude Project” full of stale instructions.  
  5. **Ecosystem leverage.** Inspector, official SDKs, Directory connectors, conference workshops (Murag; AI Engineer Europe). Official AI Engineer org treats MCP as a first-class conference surface.

  MCP does **not** replace: Week 11 loop, Week 13 graphs/HITL, Week 14 side-effect policy, Week 15 evals, or **auth design**. Authorization for remote MCP is OAuth 2.1 + protected resource metadata — you still implement it.

  Pair with **A2A** when multiple **opaque agents** must collaborate across vendors.

  Anthropic product stories you can cite without inventing case studies: Calendar/Notion agents, Claude Code + Figma, enterprise multi-DB chat, Blender → 3D print. Those are **host capabilities enabled by connectors**, not proof your customer’s SAP instance is easy.

  **What “standardized surface” actually standardizes:**

  | Standardized | Still your problem |
  |--------------|--------------------|
  | JSON-RPC methods, lifecycle, primitive shapes | Domain tool semantics |
  | How Desktop/Code **spawn or HTTP-connect** | Which tools exist; descriptions (Week 11) |
  | Capability flags | Honest advertising |
  | OAuth discovery (remote) | IdP, scopes, token vault |
  | Isolation **idea** | OS sandbox, secret injection, allowlists |

  If you MCP-wash a nightly ETL, you added a chat UI to a batch job. Don’t.

  **FDE delivery shapes:**

  | Artifact | Portability | Maintenance |
  |----------|-------------|-------------|
  | **MCP server(s) + host config** | High across MCP hosts | Spec/SDK/host quirks |
  | LangGraph app with bespoke tools | High **inside that repo** | Weak Desktop UX |
  | Claude project instructions only | Low | Drifts immediately |
  | Customer-only IDE plugin | Low | Rewrite cost |
  | Anthropic API `mcp_toolset` only | High for **API** bots | Tools-only; no stdio |
  | Notebook `while True` + functions | Demo | Dies at handoff |

* **The Alternatives:**  

  | Strategy | Wins | Loses |
  |----------|------|-------|
  | **MCP as the integration SKU** | Host swap; customer-operable | You track protocol revisions (`2025-11-25` vs host `2026-07-28`) |
  | **Deep one-host plugin** | Best UX on that host | Next RFP uses a different IDE |
  | **Only consume marketplace servers** | Speed | No proprietary API; supply chain |
  | **Only expose, never consume** | Control | Reimplement GitHub/Slack badly |
  | **Standardize later “when we know the host”** | Feels agile | Engagement ends with nothing reusable |
  | **MCP server + Desktop + Code** (syllabus) | Portable connector; customer can keep the server | Spec/SDK churn; you still need Week 11 loop inside the host |
  | **Only `bind_tools` in one Python app** | Fast demo | Dead when the customer lives in Desktop/Code/Cursor |
  | **Anthropic Messages MCP connector** (`mcp_servers` + `mcp_toolset`) | No local client; API-side remote tools | **Tools only** (no resources/prompts); **HTTPS remote only**; no stdio; beta (`mcp-client-2025-11-20`) |
  | **OpenAI hosted MCP / Agents SDK MCP** | Same idea in another ecosystem | Different host quirks; still not a substitute for **your** server semantics |
  | **Fat 80-tool server on day one** | Feels “platform” | Tool-selection collapse (Week 11) |
  | **Skip Desktop, Code only** | Faster for engineers | Misses the Desktop config/log story customers actually hit |

  Tradeoff: wrapping **HTTP APIs as MCP** is right when humans will drive agents in **multiple hosts**. A batch ETL job that never sits in a chat UI should stay a job. Shaping APIs as **chat tools** can be dishonest when the real interface is a pipeline. MCP is for **interactive agent context**, not a replacement for job schedulers.

  Harrison Chase (Week 11 talk): reliability lives in **control flow**. MCP does not give you that. It gives you **where tools come from**. `P(success)` still depends on the loop, palettes, and HITL. MCP raises **portability**, not `P(success)` of the loop. A portable footgun is still a footgun.

* **Failure Modes:**  
  - Without a standardized surface, each engagement **reinvents connectors** and dies when the preferred chat UI changes.  
  - Without MCP-as-handoff, the customer inherits a Python script that imports your unpublished package.  
  - Without allowlists, “we connected MCP” is an **unreviewed RCE-shaped plugin** (stdio = your user account; HTTP = whatever token you pasted).  
  - Without treating servers as **versioned products**, the first schema change breaks Desktop while Code still works (or the reverse).  
  - Secrets land in committed `.mcp.json`; remote HTTP bound to `0.0.0.0` without Origin checks.  
  - Week 11 tools stay **hard-coded** in one process; the FDE rewrites connectors per IDE.  
  - Capability mismatch is silent (`tools/call` against a server that never advertised `tools`).

* **Average vs. Strong Engineer:**  
  **Average:** slideware “we use MCP”; actually hardcoded tools in one LangGraph; or 12 unreviewed `npx -y` servers; credentials in git; no `tools/list` tests; no Desktop log path in the runbook; copy a FastMCP weather server; never open Desktop logs; never declare resources/prompts; call it “MCP” while the production agent still uses in-process functions.  
  **Strong:** MCP servers as **versioned products** (semver, changelog of tool schemas). CI contract tests. Secrets via customer vault / Code `${VAR}` / Desktop `env`. Document **both** host setups. Measure tool success rates (Week 15 traces). Combine with loop guardrails (Week 11) and do **not** pretend Week 13 is done. Separate read/write; confirm writes in the host. For remote: OAuth 2.1, resource indicators, no token passthrough (validate audience; least-privilege scopes; official libraries). Anthropic API bots: allowlisted `mcp_toolset`. Code: workspace trust story for committed `.mcp.json`. Registry/Directory as they mature — still **allowlist**. Managed Agents / vaults pattern: credentials matched by MCP URL, agent never sees the token — **session-time credential injection**, not tokens in tool descriptions. One capability, accurate `initialize` capabilities, absolute paths, health via `/mcp` and `mcp.log`.

* **Worked Example:**  
  **90-day FDE, customer using Claude Code today and “maybe Desktop for execs.”**

  1. Week 11 loop proven with three **in-process** tools.  
  2. Week 12: lift `docs_search` to MCP; attach Code **and** Desktop; exec demo uses Desktop filesystem-style approval UX.  
  3. Consume official GitHub MCP for PRs; do not wrap GitHub.  
  4. Handoff: repo `servers/docs-search`, `.mcp.json` with `${DOCS_API_KEY}`, Desktop snippet in README, `/mcp` approval instructions, `mcp.log` paths, protocol version pin, **which tools are writes**.  
  5. Explicit non-goals: multi-agent graph (Week 13), A2A (later), wrapping SAP in one weekend.

  Concrete host attach (from overview):

  1. Implement stdio server with official Python/TS SDK; advertise `tools` (+ optional `resources`).  
  2. Desktop: `mcpServers.docs-search.command` = `uv` / `node` with **absolute** paths; restart; confirm tools under Connectors; ask “what does the PTO policy say?”; approve the search tool.  
  3. Code: `claude mcp add --transport stdio docs-search -- uv --directory /ABS/PATH run server.py` **or** commit `.mcp.json` and approve in `/mcp`. `claude mcp list` → `✔ Connected`. Same prompt.  
  4. Optional: `claude mcp add --transport http notion https://mcp.notion.com/mcp` as a **consumed** third-party server — do not confuse with wrapping your capability.

  Official Desktop filesystem walkthrough is the same **shape** of work (config → restart → approve tools → act). Murag workshop: philosophy → build → agents → roadmap — use for **framing**; implement against **spec URLs**. Europe workshop: two servers, one harness file — that is the **compose** endgame after one capability works.

* **Apply It:**  
  1. Treat the MCP server as the engagement **SKU**: versioned repo + Desktop config + Code `.mcp.json` in the handoff.  
  2. Attach **both** Claude Desktop and Claude Code to the same stdio command before calling the week done.  
  3. Document trust boundary: reachable dirs/APIs, secret injection path, which tools are writes and need confirmation.  
  4. Allowlist every consumed server; measure tool success in traces (Week 15).  
  5. Pin protocol version; note host revision differences (`2025-11-25` vs possible `2026-07-28`).  
  6. Explicit non-goals in the README: Week 13 graphs, A2A, fat multi-system servers.

---

## Week 12 build checklist (end-to-end)

Use this as the chapter’s capstone sequence; every concept above maps here.

1. **Architecture:** stdio server with honest `initialize` capabilities; stderr-only logs; no stdout pollution.  
2. **Expose:** wrap **one** Week 11 capability (`docs_search` recommended) — not a 40-tool dump.  
3. **Primitives:** advertise `tools`; optionally add catalog **resource** + `handbook_lookup` **prompt**; use `isError` correctly.  
4. **Desktop:** `claude_desktop_config.json` with absolute paths; quit/restart; confirm tools; successful call.  
5. **Code:** `claude mcp add --transport stdio … -- …` and/or project `.mcp.json`; `/mcp` → `✔ Connected`; same successful call.  
6. **Consume (optional label):** one official third-party HTTP server, allowlisted — distinct from your expose artifact.  
7. **Handoff:** trust boundary doc, secrets in `env` / `${VAR}`, protocol version pin, read vs write confirmation story.  
8. **Interview artifact:** one server + two host configs + a successful tool call (screenshot or `/mcp` + trace).

When those steps are true, Week 12 is done in the syllabus sense: Deployment Copilot has a **portable connector**, not an in-process `bind_tools` demo — and Week 13 orchestration starts from a capability that already attaches to real hosts.
