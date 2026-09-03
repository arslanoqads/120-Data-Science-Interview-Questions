# 00 — Week overview & syllabus mapping

> Week 12 — Model Context Protocol: wrap a capability, connect Claude Desktop / Claude Code  
> Research notes (raw). Phase 3 week after the agent loop.

---

## Fundamentals

Week 12 is the **connector** week of Phase 3. Week 11 taught you the **loop contract** (plan → act → observe, pairing IDs, stop reasons). This week does **not** replace that loop. It standardizes how tools and context **show up at the host boundary** so the same capability can attach to Claude Desktop, Claude Code, Cursor, VS Code, ChatGPT, or a custom host without rewriting function schemas per product.

Anthropic and the MCP site use the same slogan: MCP is a **“USB-C port for AI applications”** — an open standard so hosts can connect to data, tools, and workflows ([What is MCP?](https://modelcontextprotocol.io/docs/getting-started/intro), [Anthropic MCP overview](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)).

**What you ship this week:** one **MCP server** wrapping **one** capability, plus **two host configs** that actually connect.

MCP does **not** decide how the host uses the LLM. Official architecture docs are explicit: MCP is the protocol for **context exchange**; hosts still own orchestration, consent, and aggregation ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)).

### Participants you must name correctly

From the spec architecture ([Specification architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture/index)) and the learn overview:

| Role | What it is | This week’s instance |
|------|------------|----------------------|
| **Host** | The AI app the user talks to. Creates clients, enforces consent, talks to the LLM. | Claude Desktop **or** Claude Code |
| **Client** | Protocol session **inside** the host; **1:1** with a server | Instantiated when Desktop/Code attaches your server |
| **Server** | Independent process/service exposing primitives | **Your** wrapped capability |

Local stdio servers typically serve **one** client (the host spawned the subprocess). Remote Streamable HTTP servers typically serve **many** clients ([Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)).

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

Official “connect local servers” tutorial uses Claude Desktop as the example host ([Connect to local MCP servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)):

- **macOS config:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
- Developer Settings → **Edit Config**. Completely **quit and restart** Desktop after edits.  
- Logs: `~/Library/Logs/Claude/mcp.log` and `mcp-server-<NAME>.log` (Windows under `%APPDATA%\Claude\logs`).

Filesystem example from that tutorial (you will swap command/args for **your** server):

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

For a Python/uv server, the official build-server docs use **absolute** `--directory` paths and `uv run …` ([Build an MCP server](https://modelcontextprotocol.io/docs/develop/build-server)). Debugging docs: CWD for stdio servers may be `/`; **never rely on relative paths**; stdio servers inherit a **limited** env — put secrets in `env` ([Debugging](https://modelcontextprotocol.io/docs/tools/debugging)).

Security from the same Desktop tutorial: the process runs **as the user**. Only grant directories/APIs you accept. Desktop still **prompts before tool execution**.

### Connect Claude Code (stdio, HTTP, project `.mcp.json`)

Official reference: [Connect Claude Code to tools via MCP](https://docs.anthropic.com/en/docs/claude-code/mcp) (also mirrored at `code.claude.com`).

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

Remote HTTP example from the same page:

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

Ops the page actually specifies: `/mcp` panel, `claude mcp list` health (`✔ Connected`, `! Needs authentication`, `✘ Failed to connect`), OAuth from `/mcp`, `MCP_TIMEOUT` / per-server `timeout`, idle timeouts, `list_changed` refresh, HTTP reconnect with backoff, tool-output token caps (`MAX_MCP_OUTPUT_TOKENS`). Stdio servers are **not** auto-reconnected (local processes).

Import Desktop configs: `claude mcp add-from-claude-desktop`. You can also expose **Claude Code itself** as a Desktop stdio server (`claude mcp serve`) — useful as a demo of host-as-server, not the syllabus default.

### What “done” looks like

1. Server process starts; `initialize` ↔ capabilities; client sends `notifications/initialized`.  
2. Desktop shows the connector / tools; Code `/mcp` shows connected + tool count.  
3. User prompt causes **one** `tools/call` for your capability; result is visible in the chat.  
4. Write tools (if any) required a **confirmation**.  
5. You can point a **second** host at the **same** stdio command (or the same HTTP URL) without changing server code.

---

## Alternatives & Tradeoffs

| Path | What you optimize | What you sacrifice |
|------|-------------------|-------------------|
| **MCP server + Desktop + Code** (syllabus) | Portable connector; customer can keep the server | Spec/SDK churn; you still need Week 11 loop inside the host |
| **Only `bind_tools` in one Python app** | Fast demo | Dead when the customer lives in Desktop/Code/Cursor |
| **Anthropic Messages MCP connector** (`mcp_servers` + `mcp_toolset`) | No local client; API-side remote tools | **Tools only** (no resources/prompts); **HTTPS remote only**; no stdio; beta (`mcp-client-2025-11-20`) ([MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)) |
| **OpenAI hosted MCP / Agents SDK MCP** | Same idea in another ecosystem | Different host quirks; still not a substitute for **your** server semantics |
| **Fat 80-tool server on day one** | Feels “platform” | Tool-selection collapse (Week 11 file 03) |
| **Skip Desktop, Code only** | Faster for engineers | Misses the Desktop config/log story customers actually hit |

Tradeoff: wrapping **HTTP APIs as MCP** is right when humans will drive agents in **multiple hosts**. A batch ETL job that never sits in a chat UI should stay a job.

---

## Necessity

If Week 12 is a slide or a FastMCP hello-world that nobody attaches:

- Week 11 tools stay **hard-coded** in one process; the FDE rewrites connectors per IDE.  
- Capability mismatch is silent (`tools/call` against a server that never advertised `tools`).  
- Secrets land in committed `.mcp.json` instead of `env` / `${VAR}` expansion.  
- Remote HTTP is bound to `0.0.0.0` without Origin checks → DNS rebinding ([Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)).  
- You cannot hand the customer a **versioned server + config**; engagement dies when they switch hosts.

Harrison Chase’s enterprise formula (Week 11) still applies: MCP raises **portability**, not `P(success)` of the loop. A portable footgun is still a footgun.

---

## Industry Practice

- **Common:** copy a FastMCP weather server; stdio only; API keys in JSON; never open Desktop logs; never declare resources/prompts; call it “MCP” while the production agent still uses in-process functions.  
- **Senior:** one capability, accurate `initialize` capabilities, official SDK, absolute paths, `env` for secrets, contract test `tools/list` schema, Inspector for JSON-RPC, Desktop **and** Code configs in the README, allowlist of third-party servers, Streamable HTTP + OAuth only when the server is actually shared, health via `/mcp` and `mcp.log`. Claude Code: project `.mcp.json` with `${VAR}` for keys; document approval/trust. Pin protocol version in HTTP (`MCP-Protocol-Version` header).

Mahesh Murag (Anthropic), AI Engineer Summit, *Building Agents with Model Context Protocol*: MCP as the shared tool/context surface for agents — watch for **philosophy + building + roadmap**, then implement against the **current spec**, not talk slides ([YouTube](https://youtu.be/kQmXtrmQ5Zg)).

AI Engineer Europe workshop: **two** FastMCP servers (Deep Research + LinkedIn writing) attached to Code/Cursor via `.mcp.json` — “build once, orchestrate from any MCP harness” ([YouTube](https://www.youtube.com/watch?v=mYSRn6PC1mc), [repo](https://github.com/samtalasila/ai-engineer-europe)). Syllabus this week is **one** server; that workshop is the **compose** pattern for file 02.

---

## Concrete Scenario

**Wrap `docs_search`, attach both hosts.**

1. Implement stdio server with official Python/TS SDK; advertise `tools` (+ optional `resources`).  
2. Desktop: `mcpServers.docs-search.command` = `uv` / `node` with **absolute** paths; restart; confirm tools under Connectors; ask “what does the PTO policy say?”; approve the search tool.  
3. Code: `claude mcp add --transport stdio docs-search -- uv --directory /ABS/PATH run server.py` **or** commit `.mcp.json` and approve in `/mcp`. `claude mcp list` → `✔ Connected`. Same prompt.  
4. Optional: `claude mcp add --transport http notion https://mcp.notion.com/mcp` as a **consumed** third-party server (file 02) — do not confuse “we connected Notion” with “we wrapped our capability.”

Official Desktop filesystem walkthrough is the same **shape** of work (config → restart → approve tools → act) ([Connect to local MCP servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)).

Anthropic public narrative (Calendar/Notion agents, Code + Figma, enterprise DB chat, Blender) is the **product** story for why hosts bother ([MCP overview](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)).

---

## Open Questions

- Will Desktop, Code, Cursor, and VS Code converge on **one** `mcpServers` schema (Code already has `type`/`http`/`ws` that Desktop tutorials omit)?  
- How should enterprises **sandbox** stdio servers (OS permissions, secret injection) at fleet scale?  
- Protocol revision split: Code v2 runtime can negotiate **2026-07-28**; this corpus documents **2025-11-25** as the stable spec snapshot — when do FDEs pin hosts vs pin servers?  
- Does Anthropic’s API MCP connector staying **tools-only** push FDE servers to over-use tools and starve resources/prompts?

---

## Sources

- https://modelcontextprotocol.io/docs/getting-started/intro  
- https://modelcontextprotocol.io/docs/learn/architecture  
- https://modelcontextprotocol.io/docs/develop/connect-local-servers  
- https://modelcontextprotocol.io/docs/develop/build-server  
- https://modelcontextprotocol.io/docs/tools/debugging  
- https://modelcontextprotocol.io/specification/2025-11-25/architecture/index  
- https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle  
- https://modelcontextprotocol.io/specification/2025-11-25/basic/transports  
- https://docs.anthropic.com/en/docs/agents-and-tools/mcp  
- https://docs.anthropic.com/en/docs/claude-code/mcp  
- https://platform.claude.com/docs/en/agents-and-tools/mcp-connector  
- https://youtu.be/kQmXtrmQ5Zg  
- https://www.youtube.com/watch?v=mYSRn6PC1mc  
- https://github.com/samtalasila/ai-engineer-europe  
