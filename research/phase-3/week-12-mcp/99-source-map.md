# 99 — Week 12 master source map

> Consolidated index of official docs, spec, talks. Legal sources only; no pirate book sites.

**Deep-pass date:** 2026-09-03. MCP docs are versioned (`/docs/2025-11-25/…`, `/docs/2026-07-28/…`). This corpus cites **specification revision `2025-11-25`** plus current Anthropic host docs. Hosts (e.g. Claude Code v2 runtime) may negotiate later protocol revisions — re-fetch before shipping.

Unversioned `https://modelcontextprotocol.io/docs/...` URLs typically resolve to a current docs train; prefer the spec URLs below when a paragraph is normative.

---

## MCP — intro & architecture (primary)

| Topic | URL |
|-------|-----|
| What is MCP? (USB-C metaphor; Calendar/Notion/Figma/DB/Blender examples) | https://modelcontextprotocol.io/docs/getting-started/intro |
| Architecture overview (host/client/server, layers, primitives, example handshake) | https://modelcontextprotocol.io/docs/learn/architecture |
| Architecture overview (pinned docs train) | https://modelcontextprotocol.io/docs/2025-11-25/learn/architecture |
| Specification: architecture (isolation, capability rules) | https://modelcontextprotocol.io/specification/2025-11-25/architecture/index |
| Specification index | https://modelcontextprotocol.io/specification/2025-11-25/ |
| Docs index (`llms.txt`) | https://modelcontextprotocol.io/llms.txt |

---

## MCP — lifecycle, transports, authorization

| Topic | URL |
|-------|-----|
| Lifecycle (`initialize` / `initialized`, capability table, stdio/HTTP shutdown, timeouts) | https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle |
| Transports (stdio, Streamable HTTP, Origin/DNS rebinding, sessions, `MCP-Protocol-Version`) | https://modelcontextprotocol.io/specification/2025-11-25/basic/transports |
| Authorization (OAuth 2.1, PKCE, RFC 9728, resource indicators) | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization |
| Authorization (later revision; same family) | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization |
| Understanding authorization (tutorial: libraries, least privilege, WWW-Authenticate) | https://modelcontextprotocol.io/docs/tutorials/security/authorization |

---

## MCP — server primitives

| Topic | URL |
|-------|-----|
| Server overview (control hierarchy: user / application / model) | https://modelcontextprotocol.io/specification/2025-11-25/server |
| Tools (`tools/list`, `tools/call`, `isError`, outputSchema, security) | https://modelcontextprotocol.io/specification/2025-11-25/server/tools |
| Resources (URI, templates, subscribe, `-32002`) | https://modelcontextprotocol.io/specification/2025-11-25/server/resources |
| Prompts (`prompts/list`, `prompts/get`) | https://modelcontextprotocol.io/specification/2025-11-25/server/prompts |
| Concepts: resources | https://modelcontextprotocol.io/docs/concepts/resources |
| Concepts: tools | https://modelcontextprotocol.io/docs/concepts/tools |
| Schema reference | https://modelcontextprotocol.io/specification/2025-11-25/schema |

---

## MCP — client primitives & develop

| Topic | URL |
|-------|-----|
| Sampling (`sampling/createMessage`, HITL, nested tools) | https://modelcontextprotocol.io/specification/2025-11-25/client/sampling |
| Connect local servers (Claude Desktop `claude_desktop_config.json`, filesystem example, logs) | https://modelcontextprotocol.io/docs/develop/connect-local-servers |
| Same (pinned train) | https://modelcontextprotocol.io/docs/2025-11-25/develop/connect-local-servers |
| Build an MCP server (uv/absolute paths → Desktop) | https://modelcontextprotocol.io/docs/develop/build-server |
| Debugging (CWD `/`, limited env, `env` key) | https://modelcontextprotocol.io/docs/tools/debugging |

---

## Anthropic — MCP hosts & API

| Topic | URL |
|-------|-----|
| MCP overview (same intro as MCP site; ecosystem) | https://docs.anthropic.com/en/docs/agents-and-tools/mcp |
| Claude Code ↔ MCP (transports, `.mcp.json`, scopes, trust, `/mcp`, OAuth, timeouts) | https://docs.anthropic.com/en/docs/claude-code/mcp |
| Messages API MCP connector (tools-only, HTTPS, `mcp_toolset`, beta `mcp-client-2025-11-20`) | https://platform.claude.com/docs/en/agents-and-tools/mcp-connector |
| Managed Agents MCP connector (vaults, URL-matched credentials) | https://platform.claude.com/docs/en/managed-agents/mcp-connector |

---

## Adjacent ecosystems (legal, complementary)

| Topic | URL |
|-------|-----|
| A2A protocol (MCP = tools; A2A = agent-to-agent) | https://a2a-protocol.org/latest/ |
| OpenAI Agents SDK tools (MCP as tool source, `defer_loading`) | https://openai.github.io/openai-agents-python/tools/ |
| AI Engineer `llms.txt` (conference/data surface) | https://www.ai.engineer/llms.md |

---

## YouTube / workshops

| Topic | URL |
|-------|-----|
| **Mahesh Murag (Anthropic)** — Building Agents with Model Context Protocol, AI Engineer Summit | https://youtu.be/kQmXtrmQ5Zg |
| **AI Engineer Europe** — multi-MCP / FastMCP workshop (Deep Research + LinkedIn servers) | https://www.youtube.com/watch?v=mYSRn6PC1mc |
| Workshop companion repo (prompts `research_workflow` / `linkedin_post_workflow`) | https://github.com/samtalasila/ai-engineer-europe |
| AI Engineer channel (index more MCP talks) | https://www.youtube.com/@aidotengineer |

---

## Mapping: concept file → sources

| File | Must-cite |
|------|-----------|
| 00 overview + wrap/connect | Intro; connect-local-servers; build-server; debugging; Claude Code MCP; Desktop config paths; Murag + Europe videos |
| 01 architecture | Learn architecture; spec architecture; lifecycle; transports; authorization; Claude Code runtime note |
| 02 expose vs consume | Anthropic MCP; Claude Code MCP; API connector; A2A; OpenAI Agents tools; Europe workshop |
| 03 primitives | Spec server / tools / resources / prompts; concepts resources+tools; sampling; API connector tools-only limit |
| 04 FDE surface | Intro; Anthropic MCP; architecture isolation; authorization tutorial; A2A; both workshops; ai.engineer llms.md |

---

## Out of scope (do not pull into Week 12)

| Topic | Week |
|-------|------|
| Agent loop, pairing IDs, retries, stop reasons | 11 |
| Graphs, multi-agent orchestration, HITL persistence | 13 |
| A2A **implementation** and side-effect safety controls | 14 |
| Trajectory eval | 15 |

Week 12 **mentions** A2A only as “not MCP.” Do not write an A2A corpus here.

---

## Prior single-file week

Expanded from `phase-3/week-12-mcp.md` (removed after this deep pass). Do not resurrect a thin single file for Week 12.
